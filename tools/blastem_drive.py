"""Drive BlastEm from Python through its GDB remote stub.

    from blastem_drive import BlastEm
    with BlastEm("work/ps4en_compose.bin", "work/pd-slot7.state") as em:
        em.frames(30)                      # run 30 frames, pad released
        em.press("C", hold=2)              # C for two frames, then release
        em.frames(10)
        print(em.word(0xFFFF5500))          # read RAM

BlastEm's own debugger takes stdin; the GDB stub (`-D`) takes a socket and
supports exactly what this needs: Z0 breakpoints, c, g/p/P, m/M.  Anything
else makes the stub call fatal_error, so send nothing else.

The pad is injected at ReadJoypad, on the instruction after `not.b d0`
(the address is read from the listing), by overwriting d0 with the wanted
button mask - so the emulator window never needs the keyboard, and the
player's own keyboard is left alone.  A frame is one hit of that
breakpoint.  Button bits are the game's own: U D L R = 0-3, B (Cancel) 4,
C (Speak/confirm) 5, A (Camp) 6, Start 7.

`-s` takes BlastEm's own `.state` files (the help text says GST, but
start_genesis tries the native format first).  See _survive_startup_reset
for the 0.6.2 bug that makes a loaded state reboot, and how it is dodged.
"""
import os, re, socket, subprocess, sys, time
from blastem_ram import work_ram

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

BLASTEM = os.path.join(ROOT, "blastem-win32-0.6.2", "blastem.exe")
BUTTON = {"U": 1, "D": 2, "L": 4, "R": 8, "B": 0x10, "C": 0x20, "A": 0x40, "S": 0x80}


def listing_address(lst, label, after=None):
    """Address of `label:` in an AS listing, or of the first line matching
    `after` (a regex on the source text) below the label."""
    txt = open(lst, encoding="utf-8", errors="replace")
    found = False
    for line in txt:
        m = re.match(r"(?:\(\d+\))?\s*\d+/\s*([0-9A-F]+) :\s*(.*)", line)   # "(1)" prefixes included files
        if not m:
            continue
        addr, src = int(m.group(1), 16), m.group(2)
        if not found:
            if src.startswith(label + ":"):
                found = True
                if after is None:
                    return addr
        elif re.search(after, src):
            return addr
    raise KeyError(label)


class BlastEm:
    def __init__(self, rom, state=None, lst=None, port=1234, visible=True, log=None):
        self.rom = os.path.abspath(rom)
        self.lst = lst or (os.path.splitext(self.rom)[0] + ".lst")
        if not os.path.exists(self.lst):
            self.lst = os.path.join(ROOT, "ps4disasm", "ps4.lst")
        self.pad = 0
        self.frame = 0
        self.bps = set()
        self.log = log
        args = [BLASTEM, self.rom, "-D"]
        if state:
            args += ["-s", os.path.abspath(state)]
        self.proc = subprocess.Popen(args, cwd=os.path.dirname(BLASTEM),
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.sock = None
        for _ in range(100):
            try:
                self.sock = socket.create_connection(("127.0.0.1", port), timeout=1)
                break
            except OSError:
                time.sleep(0.1)
        if not self.sock:
            self.proc.kill()
            raise RuntimeError("BlastEm's GDB stub did not answer")
        self.sock.settimeout(30)
        self.buf = b""
        if state:
            self._survive_startup_reset(os.path.abspath(state))
        self.pad_bp = listing_address(self.lst, "ReadJoypad", r"move\.w\s+\(Button_Mappings_Index\)")
        self.breakpoint(self.pad_bp)
        # Lag accounting: every VInt is counted, but the pad is only read on
        # the VInts the main loop was ready for (VInt_Flag set), so
        # vints - frame = frames the game logic overran.  The interrupted PC
        # of each overrun is kept as a sample of where the time went.
        self.vint_bp = listing_address(self.lst, "VInt")
        self.breakpoint(self.vint_bp)
        self.vints = 0
        self.vint_flag = 0xFFFFEF12
        self.lag_samples = []
        self.vint_log = []

    def _survive_startup_reset(self, state):
        """0.6.2 zero-initialises `reset_cycle`, so the first sync after any
        `-s` load requests a reset and the loaded state boots to the SEGA
        screen (genesis.c sync_components: `mclks >= gen->reset_cycle`).  The
        reset re-enters the ROM at its entry point with RAM, VRAM and the VDP
        untouched - only the CPU registers, YM and Z80 are lost - and the
        entry point has not been JIT-translated yet at this moment, so patch
        it in BlastEm's ROM copy to jump straight back to the state's PC, and
        put the registers back when that lands.  Sound is not recoverable
        (the YM was reset) and is stubbed out, which a harness can live with."""
        r = self.regs()
        pc = r["pc"]
        entry = int.from_bytes(self.read(4, 4), "big")
        # The reset also put the YM back to power-on and left the Z80 held in
        # reset, and the 68k sound driver then spins forever on the YM busy
        # flag / Z80 bus grant inside VInt.  Stub both driver entry points
        # (`jmp UpdateSound(pc)` -> `rts`) before the JIT sees them.
        for label in ("JumpTo_UpdateSound", "JumpTo_InitSoundDriver"):
            self.write(listing_address(self.lst, label), bytes([0x4E, 0x75]))
        # move.w #$100,(Z80_Reset).l  - the reset left the Z80 held in reset
        #                              and BlastEm never grants the bus to a
        #                              Z80 in reset, so VInt's bus-request
        #                              wait would spin forever
        # jmp pc.l
        self.write(entry, bytes([0x33, 0xFC, 0x01, 0x00, 0x00, 0xA1, 0x12, 0x00, 0x4E, 0xF9]) + pc.to_bytes(4, "big"))
        # The reset fires at the first sync, which is immediate when the state
        # was saved on a VDP access (the DMA queue) but can be most of a frame
        # away otherwise - long enough for the game to pop the very stack frame
        # the state's PC will return through.  So catch the reset at the entry
        # (the stub's first instruction) and put the whole of work RAM back
        # from the state file along with the registers; the VRAM the game
        # touched meanwhile is what it would have drawn anyway.
        self.breakpoint(entry)
        stop = self.cont()
        assert stop == entry, "expected the startup reset at %06X, stopped at %06X" % (entry, stop)
        self.write_ram(work_ram(state))
        for i in range(8):
            self.setreg(i, r["d"][i])
            self.setreg(8 + i, r["a"][i])
        self.setreg(16, r["sr"])
        self.unbreak(entry)

    def write_ram(self, image):
        """Replace all 64K of work RAM (M packets of 200 bytes)."""
        assert len(image) == 0x10000
        for off in range(0, 0x10000, 200):
            self.write(0xFF0000 + off, image[off:off + 200])

    # -- protocol ---------------------------------------------------------
    def _send(self, payload):
        s = ("$" + payload + "#%02x" % (sum(payload.encode()) & 0xFF)).encode()
        self.sock.sendall(s)

    def _recv_packet(self):
        while True:
            i = self.buf.find(b"$")
            if i >= 0:
                j = self.buf.find(b"#", i)
                if j >= 0 and len(self.buf) >= j + 3:
                    pkt = self.buf[i + 1:j].decode()
                    self.buf = self.buf[j + 3:]
                    self.sock.sendall(b"+")
                    return pkt
            data = self.sock.recv(4096)
            if not data:
                raise RuntimeError("BlastEm closed the GDB socket")
            self.buf += data

    def cmd(self, payload):
        self._send(payload)
        return self._recv_packet()

    # -- primitives -------------------------------------------------------
    def breakpoint(self, addr):
        if addr not in self.bps:
            assert self.cmd("Z0,%x,2" % addr) == "OK"
            self.bps.add(addr)

    def unbreak(self, addr):
        if addr in self.bps:
            assert self.cmd("z0,%x,2" % addr) == "OK"
            self.bps.discard(addr)

    def regs(self):
        h = self.cmd("g")
        v = [int(h[i:i + 8], 16) for i in range(0, 18 * 8, 8)]
        return {"d": v[:8], "a": v[8:16], "sr": v[16], "pc": v[17]}

    def pc(self):
        return int(self.cmd("p11"), 16)

    def setreg(self, n, value):
        assert self.cmd("P%x=%08x" % (n, value & 0xFFFFFFFF)) == "OK"

    def read(self, addr, n):
        out = b""
        while n:
            k = min(n, 200)
            out += bytes.fromhex(self.cmd("m%x,%x" % (addr & 0xFFFFFF, k)))
            addr += k; n -= k
        return out

    def write(self, addr, data):
        assert self.cmd("M%x,%x:%s" % (addr & 0xFFFFFF, len(data), data.hex())) == "OK"

    def byte(self, addr):
        return self.read(addr, 1)[0]

    def word(self, addr):
        return int.from_bytes(self.read(addr, 2), "big")

    def cont(self):
        """Run until a breakpoint; returns the pc it stopped at."""
        r = self.cmd("c")
        assert r.startswith("S") or r.startswith("T"), r
        return self.pc()

    # -- frames and pad ---------------------------------------------------
    def step_frame(self, hook=None):
        """Run to the next pad read, injecting the current pad state.  Other
        breakpoints hit on the way are passed to `hook(pc)`."""
        while True:
            pc = self.cont()
            if pc == self.pad_bp:
                self.setreg(0, self.pad)
                self.frame += 1
                return
            if pc == self.vint_bp:
                self.vints += 1
                flag = self.byte(self.vint_flag)
                sp = self.regs()["a"][7]
                self.vint_log.append((self.frame, flag, int.from_bytes(self.read(sp + 2, 4), "big")))
                if not flag:
                    self.lag_samples.append(self.vint_log[-1])
                continue
            if hook:
                hook(pc)

    def frames(self, n, hook=None):
        for _ in range(n):
            self.step_frame(hook)

    def press(self, buttons, hold=2, release=8, hook=None):
        """Hold the named buttons (e.g. "C", "UC") for `hold` frames, then
        run `release` frames with the pad clear."""
        self.pad = 0
        for b in buttons:
            self.pad |= BUTTON[b]
        self.frames(hold, hook)
        self.pad = 0
        self.frames(release, hook)

    @property
    def lag(self):
        return self.vints - self.frame

    def close(self):
        try:
            self.sock.close()
        finally:
            self.proc.kill()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()
