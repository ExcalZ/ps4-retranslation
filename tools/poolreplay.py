"""Replay a savestate's visible names through the BUILT rom's name path.

    python tools/poolreplay.py <savestate> [...]
    python tools/poolreplay.py <savestate> --top 69 --dead 22-25 --draw "Wood Cane,Graphite Shield,Laser Barrier,Laser Barrier"

The second form replays a TRANSIENT rather than the settled screen: the
pool is taken to hold `top` live cells (opaque, distinct keys) with the
`dead` slot range free, and the listed names are drawn in that order,
duplicates included.  That is the equip-screen overflow as the marks
recorded it - window 8 opening at PoolTop 69 with four dead cells below.

The savestate says which names the screen holds (strip heads below PoolTop,
in slot order) and how many composed cells sit beneath them (party names,
labels: the slots before the first strip head).  This keeps that composed
baseline - keys, refs, PoolTop - and redraws the same names through
VWFMenu_DrawString of whatever ps4disasm/ps4built.bin currently is, so the
same screen can be costed under vwf_menu_strips=1 (prerendered strips) and
=0 (composed, deduplicated) with no other variable changed.

No sweep is allowed during the replay (FieldReuseDepth=0), so the pool grows
or fails and the number printed is the demand, not what reclaim managed.
That is the question being asked: does this screen fit in VWFMENU_SLOTS?
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blastem_ram import work_ram
from emu68k import CPU
import menuharness as H

BASE = 0x5400
C = open("ps4disasm/ps4.constants.asm", encoding="utf-8", errors="replace").read()
SLOTS = int(re.search(r"^VWFMENU_SLOTS\s*=\s*(\d+)", C, re.M).group(1))
def off(name):
    return BASE + int(re.search(r"^%s\s*=\s*VWF_RAM_Base\+\$([0-9A-Fa-f]+)" % name, C, re.M).group(1), 16)
TOP, KEYS, REFS, STRIPOF = off("VWFMenu_PoolTop"), off("VWFMenu_Keys"), off("VWFMenu_Refs"), off("VWFMenu_StripOf")
FIELD_DEPTH, FIELD_BLOCKED, INHIBIT = off("VWFMenu_FieldReuseDepth"), off("VWFMenu_FieldReuseBlocked"), off("VWFMenu_ReclaimInhibit")
GAME_MODE = int(re.search(r"^Game_Mode_Index\s*=\s*ramaddr\(\$([0-9A-Fa-f]+)\)", C, re.M).group(1), 16) & 0xFFFF

sym = H.Symbols()
rom = open(H.ROM, "rb").read()
idx = open("ps4disasm/vwf/menustripidx.bin", "rb").read()
smap = open("ps4disasm/vwf/menustripmap.bin", "rb").read()
LO = sym["InventoryNames"]
addr_of = {}
for o in range(0, len(smap), 2):
    i = (smap[o] << 8) | smap[o + 1]
    if i != 0xFFFF:
        addr_of.setdefault(i, LO + o // 2)
names_txt = open("ps4disasm/vwf/menunames.bin", "rb").read()
names_idx = open("ps4disasm/vwf/menunameidx.bin", "rb").read()
import menustrip
INV = {v: k for k, v in menustrip.code.items()}
def text(i):
    o = int.from_bytes(names_idx[i * 2:i * 2 + 2], "big")
    s = ""
    while names_txt[o] < 0xFE:
        s += INV[names_txt[o]]; o += 1
    return s

PLANE = 0xFF1000
ENTRY = sym["VWFMenu_DrawString"]
mode = "strips" if re.search(r":\s+VWFMenu_DrawStrip:", sym.text) else "composed"

args = sys.argv[1:]
opt = {}
for k in ("--top", "--dead", "--draw"):
    if k in args:
        j = args.index(k); opt[k] = args[j + 1]; del args[j:j + 2]
index_of = {text(i): i for i in range(len(names_idx) // 2)}

for p in args:
    ram = bytearray(work_ram(p))
    w = lambda a: int.from_bytes(ram[a:a + 2], "big")
    top = w(TOP)
    heads = [(s, w(STRIPOF + s * 2)) for s in range(top) if w(STRIPOF + s * 2) < 0xFFFE]
    if "--draw" in opt:
        heads = [(None, index_of[t.strip()]) for t in opt["--draw"].split(",")]
    elif top > SLOTS or any(i * 4 + 2 >= len(idx) for _, i in heads):
        print("== %s   skipped: pool bookkeeping is not this build's layout" % os.path.basename(p))
        continue
    baseline = int(opt["--top"]) if "--top" in opt else (heads[0][0] if heads else top)
    dead = set()
    if "--dead" in opt:
        a, b = opt["--dead"].split("-"); dead = set(range(int(a), int(b) + 1))
    print("== %s   built rom: %s, %d slots" % (os.path.basename(p), mode, SLOTS))
    print("   baseline %d cells (%d dead); drawing %d names, %d strip cells"
          % (baseline, len(dead), len(heads), sum(idx[i * 4 + 2] for _, i in heads)))
    # the baseline stays; everything above it is redrawn from scratch
    ram[TOP:TOP + 2] = baseline.to_bytes(2, "big")
    for s in range(SLOTS):
        live = s < baseline and s not in dead
        ram[REFS + s] = 1 if live else 0
        ram[STRIPOF + s * 2:STRIPOF + s * 2 + 2] = (b"\xff\xfe" if s < baseline else b"\xff\xff")
        if "--top" in opt and s < baseline:
            # opaque live content: a key no glyph cell can match
            ram[KEYS + s * 8:KEYS + s * 8 + 8] = bytes([0xA5, s, 0x5A, s, 0xA5, s, 0x5A, s])
        if s >= baseline:
            # nothing resident above the baseline: the composed build's dedup
            # scan covers the whole table, so a stale key here would be a hit
            ram[KEYS + s * 8:KEYS + s * 8 + 8] = bytes([0xFF] * 8)
    ram[FIELD_DEPTH] = 0; ram[FIELD_BLOCKED] = 0; ram[INHIBIT] = 0
    ram[GAME_MODE:GAME_MODE + 2] = (0xC).to_bytes(2, "big")
    mem = bytearray(0x1000000); mem[:len(rom)] = rom
    mem[0xFF0000:0xFF0000 + len(ram)] = ram
    plane = PLANE
    prev = baseline
    blanked = 0
    for s, i in heads:
        for k in range(0x80): mem[plane + k] = 0xAA
        cpu = CPU(mem, ENTRY); cpu.a[0] = addr_of[i]; cpu.a[1] = plane; cpu.setd_w(2, 0xE680)
        for _ in range(400000):
            if cpu.step(): break
        else: raise SystemExit("no exit")
        now = int.from_bytes(mem[0xFF0000 + TOP:0xFF0000 + TOP + 2], "big")
        n = (cpu.a[1] - plane) // 2
        cells = [cpu.rw(plane + 2 * k) & 0x7FF for k in range(n)]
        ink = sum(1 for c in cells if c != 0x680)
        want = idx[i * 4 + 2]
        if mode == "composed":
            # an ink-less trailing cell is the blank tile on this build
            _c, _span = menustrip.compose(text(i))
            want = sum(1 for t in range(_c) if any(_span[y * 16 + t] for y in range(8)))
        note = "" if ink == want else "   <-- %d of %d cells drawn" % (ink, want)
        if ink < want: blanked += 1
        print("   %-16s %2d cells  +%2d  -> PoolTop %2d%s" % (text(i), want, now - prev, now, note))
        prev = now
        plane += 0x80
    print("   total %d of %d%s" % (prev, SLOTS, "  (%d name(s) could not be drawn in full)" % blanked if blanked else ""))
