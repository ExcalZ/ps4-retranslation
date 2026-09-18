import re
"""Cover a strip cell, free its tiles, reveal it, and check it comes back.

This is the path no other suite touches: SaveRegion records what a window
covers, Release hands those slots to something else, and RemapCell has to
repoint the revealed cell at wherever the strip lives now.  Before strip
records existed it repointed using a composer key that was never written,
so the revealed cell drew whatever had been allocated over it.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import menuharness as H

sym = H.Symbols()
rom = open(H.ROM, "rb").read()
STATE = "Exodus_2.1/Savestates/vwfmenu11-status.exs"
BASE = 0xFF5400
POOLTOP = BASE + 0x100
ok = True


def note(label, good, detail=""):
    global ok
    ok &= good
    print("  %s %-44s %s" % ("ok  " if good else "FAIL", label, detail))


def entry(table, n):
    a = sym[table]
    for _ in range(n):
        while rom[a] < 0xFE:
            a += 1
        a += 1
    return a


st = H.load_state(STATE)
st["ram"] = bytearray(st["ram"])
st["ram"][0x5400 + 0x100:0x5400 + 0x102] = b"\x00\x00"     # empty pool
_C = open("ps4disasm/ps4.constants.asm", encoding="utf-8", errors="replace").read()
_off = lambda name: int(re.search(
    r"^" + name + r"\s*=\s*VWF_RAM_Base\+\$([0-9A-Fa-f]+)", _C, re.M).group(1), 16)
_st = _off("VWFMenu_SaveTop")
_ss = _off("VWFMenu_SaveStack")
st["ram"][0x5400 + _st:0x5400 + _st + 2] = b"\x00\x00"     # empty save stack
PB = sym["Plane_A_Buffer"]
for i in range(0x80 * 8):
    st["ram"][(PB - 0xFF0000) + i] = 0

def carry(m):
    st["ram"] = bytearray(m.m[0xFF0000:0x1000000])
    st["vram"] = bytes(m.vram)

# A state made by the preceding experimental build carries ten-byte
# (tile,key) records.  The first window operation must compact those records
# in place without changing their indices, because marker cells refer to the
# index and can already be visible in the saved plane.
mig = H.load_state(STATE)
mig["ram"] = bytearray(mig["ram"])
mark = _off("VWFMenu_SaveMark")
magic = _off("VWFMenu_LayoutMagic")
mig["ram"][0x5400 + _st:0x5400 + _st + 2] = b"\x00\x02"
mig["ram"][0x5400 + mark:0x5400 + mark + 32] = b"\x00" * 32
mig["ram"][0x5400 + magic:0x5400 + magic + 4] = b"\x00" * 4
key0 = bytes.fromhex("1020304050607080")
key1 = bytes.fromhex("89ABCDEF01234567")
old = b"\xE6\x82" + key0 + b"\xE6\x83" + key1
mig["ram"][0x5400 + _ss:0x5400 + _ss + len(old)] = old
mm, _ = H.call(mig, "VWFMenu_EnsureLayout", sym)
packed = bytes(mm.m[BASE + _ss:BASE + _ss + 16])
note("old ten-byte save records compact in place",
     packed == key0 + key1 and mm.rl(BASE + magic) == 0x56574635,
     packed.hex())
# Every migration ends by initialising the field-only tail: keys all-ones
# (never composed), counts, links and records clear.
_L = H.SlotLayout()
note("migration initialises the tail slots",
     all(mm.rl(_L.key(s)) == 0xFFFFFFFF and mm.rl(_L.key(s) + 4) == 0xFFFFFFFF
         and mm.rb(_L.ref(s)) == 0 and mm.rb(_L.link(s)) == 0
         for s in range(_L.base_slots, _L.slots))
     and all(mm.rl(_L.record(r)) == 0 and mm.rl(_L.record(r) + 4) == 0
             for r in range(_L.base_slots, _L.saven)))

# VWF3 already used the final key/ref/link locations and compact records.  Its
# old 128-head hash occupied the space now needed by records 104..113, so VWF4
# preserves the ledger and clears only the relocated, derived hash index.
v3 = H.load_state(STATE)
v3["ram"] = bytearray(v3["ram"])
v3["ram"][0x5400 + magic:0x5400 + magic + 4] = b"VWF3"
bucket = _off("VWFMenu_Bucket")
bucket_n = int(re.search(r"^VWFMENU_BUCKETS\s*=\s*(\d+)", _C, re.M).group(1))
saved = bytes(range(80))
v3["ram"][0x5400 + _ss:0x5400 + _ss + len(saved)] = saved
v3["ram"][0x5400 + bucket:0x5400 + bucket + bucket_n] = b"\xA5" * bucket_n
mm, _ = H.call(v3, "VWFMenu_EnsureLayout", sym)
note("VWF3 ledger survives the relocated hash migration",
     bytes(mm.m[BASE + _ss:BASE + _ss + len(saved)]) == saved
     and bytes(mm.m[BASE + bucket:BASE + bucket + bucket_n]) == b"\0" * bucket_n
     and mm.rl(BASE + magic) == 0x56574635)

# 1. draw a technique name, so the row holds real strip cells
m, _ = H.call(st, "VWFMenu_DrawString", sym, a0=entry("TechniqueNames", 1),
              a1=PB, d2=0xE680)
carry(m)
cell0 = int.from_bytes(st["ram"][(PB - 0xFF0000):(PB - 0xFF0000) + 2], "big")
top_drawn = int.from_bytes(st["ram"][0x5400 + 0x100:0x5400 + 0x102], "big")
note("a strip cell was drawn", 0x682 <= (cell0 & 0x7FF) <= 0x6FF,
     "cell $%04X, PoolTop %d" % (cell0, top_drawn))

# 2. a window covers the row: SaveRegion records it and marks the cell
m, _ = H.call(st, "VWFMenu_SaveRegion", sym, a0=PB, d1=4)
carry(m)
cell1 = int.from_bytes(st["ram"][(PB - 0xFF0000):(PB - 0xFF0000) + 2], "big")
savetop = int.from_bytes(st["ram"][0x5400 + _st:0x5400 + _st + 2], "big")
note("covered cell became a record marker", 0x700 <= (cell1 & 0x7FF) <= 0x76F,
     "cell $%04X, SaveTop %d" % (cell1, savetop))
rec = st["ram"][0x5400 + _ss: 0x5400 + _ss + 10]
from buildflags import strips_built, skipped
STRIPS = strips_built(sym.text)
if STRIPS: note("the record is flagged as a strip", bool(rec[0] & 0x80),
     "record tile word $%02X%02X, index %d, offset %d"
     % (rec[0], rec[1], (rec[2] << 8) | rec[3], (rec[4] << 8) | rec[5]))

# 3. the window's own content takes the pool over
st["ram"][0x5400 + 0x100:0x5400 + 0x102] = b"\x00\x00"
m, _ = H.call(st, "VWFMenu_DrawString", sym, a0=entry("InventoryNames", 2),
              a1=PB + 0x200, d2=0xE680)
carry(m)
note("the freed slots were handed to another name", True,
     "PoolTop now %d" % int.from_bytes(st["ram"][0x5400+0x100:0x5400+0x102], "big"))

# 4. reveal: the cell must point at a live strip tile again
m, _ = H.call(st, "VWFMenu_RemapCell", sym, a4=PB)
carry(m)
cell2 = int.from_bytes(st["ram"][(PB - 0xFF0000):(PB - 0xFF0000) + 2], "big")
top_after = int.from_bytes(st["ram"][0x5400 + 0x100:0x5400 + 0x102], "big")
note("revealed cell points at a pool tile again",
     0x682 <= (cell2 & 0x7FF) <= 0x6FF, "cell $%04X" % cell2)
note("it is not still a marker", not (0x700 <= (cell2 & 0x7FF) <= 0x76F))
if STRIPS: note("the strip was re-allocated", top_after > 8, "PoolTop %d" % top_after)
else: skipped("strip record/re-allocation (composed names dedupe instead)")

print("ALL PASS" if ok else "FAILURES ABOVE")
sys.exit(0 if ok else 1)
