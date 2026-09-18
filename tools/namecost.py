"""Instructions the BUILT rom spends drawing one name, first draw and redraw.

    python tools/namecost.py [--top N] [name ...]

Counts 68000 instructions through VWFMenu_DrawString in the harness - not
cycles, so it is a ratio between the two settings of vwf_menu_strips, not a
frame budget.  A first draw allocates and uploads; a redraw of a resident
name is the reuse path.  Names default to a long one, a short one and one
with a shared prefix.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu68k import CPU
import menuharness as H
import menustrip

sym = H.Symbols()
rom = open(H.ROM, "rb").read()
C = open("ps4disasm/ps4.constants.asm", encoding="utf-8", errors="replace").read()
BASE = 0xFF5400
GAME_MODE = int(re.search(r"^Game_Mode_Index\s*=\s*ramaddr\(\$([0-9A-Fa-f]+)\)", C, re.M).group(1), 16) & 0xFFFFFF
smap = open("ps4disasm/vwf/menustripmap.bin", "rb").read()
names_txt = open("ps4disasm/vwf/menunames.bin", "rb").read()
names_idx = open("ps4disasm/vwf/menunameidx.bin", "rb").read()
INV = {v: k for k, v in menustrip.code.items()}
LO = sym["InventoryNames"]
addr_of = {}
for o in range(0, len(smap), 2):
    i = (smap[o] << 8) | smap[o + 1]
    if i != 0xFFFF:
        addr_of.setdefault(i, LO + o // 2)
def text(i):
    o = int.from_bytes(names_idx[i * 2:i * 2 + 2], "big")
    s = ""
    while names_txt[o] < 0xFE:
        s += INV[names_txt[o]]; o += 1
    return s
index_of = {text(i): i for i in range(len(names_idx) // 2)}
mode = "strips" if re.search(r":\s+VWFMenu_DrawStrip:", sym.text) else "composed"
ENTRY = sym["VWFMenu_DrawString"]

args = sys.argv[1:]
top = 0
if "--top" in args:
    j = args.index("--top"); top = int(args[j + 1]); del args[j:j + 2]
names = args or ["Graphite Shield", "Dagger", "Ceramic Sword", "Ceramic Shield"]
mem = bytearray(0x1000000); mem[:len(rom)] = rom
# --top N: start with N opaque live cells, so the content search has a full
# pool to scan - the cost that grows with occupancy
mem[BASE + 0x100:BASE + 0x102] = top.to_bytes(2, "big")
for s in range(top):
    mem[BASE + 0x440 + s] = 1
    mem[BASE + 0x500 + s * 2:BASE + 0x500 + s * 2 + 2] = bytes([0xFF, 0xFE])
    mem[BASE + 0x140 + s * 8:BASE + 0x140 + s * 8 + 8] = bytes([0xA5, s, 0x5A, s, 0xA5, s, 0x5A, s])
mem[GAME_MODE:GAME_MODE + 2] = (0xC).to_bytes(2, "big")
plane = 0xFF1000
print("built rom: %s" % mode)
for n in names:
    a0 = addr_of[index_of[n]]
    counts = []
    for pass_ in ("first", "redraw"):
        for k in range(0x80): mem[plane + k] = 0xAA
        cpu = CPU(mem, ENTRY); cpu.a[0] = a0; cpu.a[1] = plane; cpu.setd_w(2, 0xE680)
        steps = 0
        for _ in range(400000):
            steps += 1
            if cpu.step(): break
        else: raise SystemExit("no exit")
        counts.append(steps)
        plane += 0x80
    top = int.from_bytes(mem[BASE + 0x100:BASE + 0x102], "big")
    print("  %-16s %2d cells   first draw %6d instrs   redraw %6d   (PoolTop %d)"
          % (n, menustrip.compose(n)[0], counts[0], counts[1], top))
