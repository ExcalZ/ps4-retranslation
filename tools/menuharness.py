"""Drive the menu draw routines against a real savestate, without the emulator.

A play session costs ten minutes to reach a battle; this costs a second, and
it answers questions a screenshot cannot - which nametable cell was written,
in what order, by which routine.

It loads a savestate's RAM, VRAM and 68000 registers, models just enough of
the VDP to catch tile uploads, calls a routine, and renders the resulting
Plane A buffer as text.  Nametable writes never reach the VDP at all: the
window code builds them in RAM (`move.w #Plane_A_Buffer, d5`), so the result
is readable straight out of memory.

emu68k raises on opcodes it does not implement rather than guessing, so a
trap here means "add that opcode", not "the ROM is wrong".
"""
import os, re, sys, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu68k import CPU, Trap

# PS4_ROM / PS4_LST point the harness at another build - a rom and the
# listing it was assembled with - so two configurations can be compared
# without reassembling between runs (tools/poolreplay.py, tools/namecost.py).
ROM = os.environ.get("PS4_ROM", "ps4disasm/ps4built.bin")
LST = os.environ.get("PS4_LST", "ps4disasm/ps4.lst")
CONSTANTS = "ps4disasm/ps4.constants.asm"

VDP_DATA, VDP_CTRL = 0xC00000, 0xC00004


class SlotLayout:
    """Where the composed pool keeps slot s's key, refcount and hash link, and
    save record r's key.  Slots below VWFMENU_BASE_SLOTS are in VWF_RAM_Base;
    the field-only tail (114..145) is in the battle-setup RAM at $FFFF4200,
    exactly as VWFMenu_KeyAddr/RefAddr/NextAddr/SaveAddr resolve them.  Tests
    that seed or read per-slot state must go through this, or a loop over
    VWFMENU_SLOTS runs the base arrays into their neighbours."""

    def __init__(self, path=CONSTANTS):
        c = open(path, encoding="utf-8", errors="replace").read()
        num = lambda n: int(re.search(r"^%s\s*=\s*(\d+)" % n, c, re.M).group(1))
        off = lambda n: int(re.search(
            r"^%s\s*=\s*VWF_RAM_Base\+\$([0-9A-Fa-f]+)" % n, c, re.M).group(1), 16)
        ram = lambda n: 0xFF0000 + (int(re.search(
            r"^%s\s*=\s*ramaddr\(\$([0-9A-Fa-f]+)\)" % n, c, re.M).group(1), 16) & 0xFFFF)
        self.base = ram("VWF_RAM_Base")
        self.slots = num("VWFMENU_SLOTS")
        self.base_slots = num("VWFMENU_BASE_SLOTS")
        self.battle_slots = num("VWFMENU_BATTLE_SLOTS")
        self.saven = num("VWFMENU_SAVEN")
        self.keys, self.refs = self.base + off("VWFMenu_Keys"), self.base + off("VWFMenu_Refs")
        self.next, self.save = self.base + off("VWFMenu_StripNext"), self.base + off("VWFMenu_SaveStack")
        self.keys_x, self.refs_x = ram("VWFMenu_KeysX"), ram("VWFMenu_RefsX")
        self.next_x, self.save_x = ram("VWFMenu_NextX"), ram("VWFMenu_SaveStackX")

    def _split(self, i, base, tail, size):
        assert 0 <= i < max(self.slots, self.saven), i
        if i < self.base_slots:
            return base + i * size
        return tail + (i - self.base_slots) * size

    def key(self, slot): return self._split(slot, self.keys, self.keys_x, 8)
    def ref(self, slot): return self._split(slot, self.refs, self.refs_x, 1)
    def link(self, slot): return self._split(slot, self.next, self.next_x, 1)
    def record(self, r): return self._split(r, self.save, self.save_x, 8)


class Symbols:
    """Addresses from the listing: code labels and the trailing symbol table."""

    def __init__(self, path=LST):
        self.text = open(path, encoding="utf-8", errors="replace").read()
        self._cache = {}

    def __getitem__(self, name):
        if name in self._cache:
            return self._cache[name]
        # The listing prints the address unpadded, so anything below $100000
        # - which is all of the game code - shows five digits, not six.
        m = re.search(r"/\s*([0-9A-F]{4,6}) :\s+" + re.escape(name) + r":", self.text)
        if not m:
            m = re.search(re.escape(name) + r"\s*:\s*([0-9A-F]{4,16})\s", self.text)
        if not m:
            # RAM equates live in the constants file, not the listing:
            #   Plane_A_Buffer = ramaddr($FFFF8000)
            eq = open(CONSTANTS, encoding="utf-8", errors="replace").read()
            m = re.search(r"^" + re.escape(name) + r"\s*=\s*(?:ramaddr\()?\$([0-9A-Fa-f]+)",
                          eq, re.M)
        if not m:
            # Last resort, still taken from the build: every `jsr (NAME).l`
            # carries the resolved address in its own encoding, 4EB9 hhhh llll.
            m = re.search(r"4EB9 ([0-9A-F]{4}) ([0-9A-F]{4})[^(]*\("
                          + re.escape(name) + r"\)\.l", self.text)
            if m:
                v = ((int(m.group(1), 16) << 16) | int(m.group(2), 16)) & 0xFFFFFF
                self._cache[name] = v
                return v
        if not m:
            raise KeyError("no address for " + name)
        v = int(m.group(1), 16) & 0xFFFFFF
        self._cache[name] = v
        return v


class Machine(CPU):
    """68000 plus the slice of VDP the window code actually touches."""

    def __init__(self, rom, state):
        mem = bytearray(0x1000000)
        mem[:len(rom)] = rom
        mem[0xFF0000:0xFF0000 + len(state["ram"])] = state["ram"]
        super().__init__(mem, pc=state["pc"], sp=state["sp"])
        self.d = list(state["d"])
        a = list(state["a"])
        a.append(state["sp"])
        self.a = a
        self.a[7] -= 4
        self.wl(self.a[7], self.SENTINEL)
        self.vram = bytearray(state["vram"])
        self.vram_writes = []
        self._ctrl = []
        self._vdp_addr = 0
        self._vdp_code = 0
        self._pend = {}
        self.inc = state["autoinc"]

    # -- memory ------------------------------------------------------
    def wb(self, addr, v):
        a = addr & 0xFFFFFF
        if 0xC00000 <= a <= 0xC00007:
            self._vdp_byte(a, v & 0xFF)
            return
        self.m[a] = v & 0xFF

    def rb(self, addr):
        a = addr & 0xFFFFFF
        if 0xC00004 <= a <= 0xC00007:
            return 0x34 if (a & 1) else 0x00     # status: FIFO empty, not busy
        return self.m[a]

    def _vdp_byte(self, a, v):
        port = VDP_CTRL if a >= 0xC00004 else VDP_DATA
        if a & 1:
            word = (self._pend.pop(port, 0) << 8) | v
            self._vdp_word(port, word)
        else:
            self._pend[port] = v

    def _vdp_word(self, port, w):
        if port == VDP_CTRL:
            if w & 0x8000 and not self._ctrl:
                return                            # register write, ignored
            self._ctrl.append(w)
            if len(self._ctrl) == 2:
                w1, w2 = self._ctrl
                self._vdp_addr = (w1 & 0x3FFF) | ((w2 & 3) << 14)
                self._vdp_code = ((w1 >> 14) & 3) | ((w2 >> 2) & 0x3C)
                self._ctrl = []
            return
        if self._vdp_code & 1:                    # VRAM write
            at = self._vdp_addr & 0xFFFF
            self.vram[at] = (w >> 8) & 0xFF
            self.vram[(at + 1) & 0xFFFF] = w & 0xFF
            self.vram_writes.append(at)
            self._vdp_addr = (self._vdp_addr + self.inc) & 0xFFFF


def load_state(path):
    z = zipfile.ZipFile(path)
    xml = z.read("save.xml").decode("utf-8", "replace")
    reg = {}
    for m in re.finditer(r'<Register name="([^"]{1,6})"[^>]*>([0-9A-Fa-f]{1,16})</Register>', xml):
        reg.setdefault(m.group(1), m.group(2))
    val = lambda n: int(reg[n], 16)
    vdpregs = z.read("MD1600.VDP.Registers.bin")
    return {
        "ram":  z.read("MD1600.RAM.bin"),
        "vram": z.read("MD1600.VDP - VRAM.bin"),
        "d":    [val("D%d" % i) for i in range(8)],
        "a":    [val("A%d" % i) for i in range(7)],
        "sp":   val("SSP"),
        "pc":   val("PC"),
        "autoinc": vdpregs[15] if len(vdpregs) > 15 else 2,
    }


def call(state, routine, sym, limit=400000, **regs):
    """Run `routine` with the savestate's context plus register overrides."""
    rom = open(ROM, "rb").read()
    m = Machine(rom, state)
    m.pc = sym[routine] if isinstance(routine, str) else routine
    for k, v in regs.items():
        idx = int(k[1])
        if k[0] == "d":
            m.d[idx] = v & 0xFFFFFFFF
        else:
            m.a[idx] = v & 0xFFFFFFFF
    steps = 0
    while steps < limit:
        steps += 1
        if m.step():
            return m, steps
    raise Trap("did not return within %d instructions" % limit)


CHAR = {0: " "}
for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"): CHAR[1 + i] = c
for i, c in enumerate("0123456789"):                 CHAR[27 + i] = c
for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"): CHAR[57 + i] = c
CHAR[0x31] = "-"; CHAR[0x34] = ":"


def render(m, base, rows=28, cols=64, width=40):
    """Plane A buffer as text: letters for $7C0 glyphs, S for pool tiles."""
    out = []
    for r in range(rows):
        line = ""
        for c in range(width):
            t = m.rw(base + r * 0x80 + c * 2) & 0x7FF
            if 0x682 <= t <= 0x6FF:   line += "S"
            elif 0x7C0 <= t <= 0x7FF: line += CHAR.get(t - 0x7C0 + 1, "?")
            elif t == 0x680:          line += "."
            else:                     line += " "
        out.append(line)
    return out


if __name__ == "__main__":
    sym = Symbols()
    path = sys.argv[1] if len(sys.argv) > 1 else \
        "Exodus_2.1/Savestates/vwfmenu10-techmenu.exs"
    st = load_state(path)
    print("state %s" % os.path.basename(path))
    print("  pc $%06X  sp $%08X  autoinc %d" % (st["pc"], st["sp"], st["autoinc"]))
    print("  a0 $%08X  a1 $%08X  d0 $%08X  d2 $%08X"
          % (st["a"][0], st["a"][1], st["d"][0], st["d"][2]))
    print("  Plane_A_Buffer $%06X" % sym["Plane_A_Buffer"])
