"""An outer window's cell may share a slot with an inner window's cell.

Composed text is allocated by CONTENT, so when an outer window is redrawn
while an inner window is open, its cells hit the inner window's slots.  The
equip screen does exactly this: after equipping, the equipped-items panel
(outer) redraws the new weapon while the item list (inner) still shows the
same name.  The list is then destroyed and rebuilt - Release rolls PoolTop
back to the list's mark - and the rebuilt list allocates from there, in
whatever order it now draws.  If the panel's cells still point into that
range, they show whatever landed there: `P:Force Cand` on the equip screen
(work/compose-slot0.state, 2026-09-10).

Two rules keep the shared slots intact, both in VWFMenu_Alloc:
  * a dedup hit may land anywhere in the key table, not only below
    PoolTop - a key above the frontier still has its tile in VRAM, and the
    rebuilt list then re-finds the very slots the panel points at;
  * growth never takes a slot the last sweep marked live, so a live cell
    above the frontier is skipped rather than overwritten.
And Release leaves the refcounts to the sweep that Window_Destroy runs
right after it, instead of clearing everything above the mark blind.

Only the composed-name build has these rules; the strip build's chains are
found by index and re-land LIFO, which is what hid the problem there.

Later additions (all composed-build behaviour, same harness):
  * a full-but-unswept pool is swept before a cell is refused;
  * consecutive Window_Destroys defer their reveals until the plane is sent;
  * SaveRegion records immutable keys across active windows, and pins a raw
    backup tile if those historical keys fill the ledger.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import menuharness as H
from emu68k import CPU
from buildflags import strips_built, skipped
import menustrip

sym = H.Symbols()
rom = open(H.ROM, "rb").read()
if strips_built(sym.text):
    skipped("shared cells across a window release", "strip build: names are found by index")
    print("ALL PASS")
    sys.exit(0)

BASE = 0xFF5400
C = open("ps4disasm/ps4.constants.asm", encoding="utf-8", errors="replace").read()
ramaddr = lambda n: 0xFF0000 + (int(re.search(r"^%s\s*=\s*ramaddr\(\$([0-9A-Fa-f]+)\)" % n, C, re.M).group(1), 16) & 0xFFFF)
PLANE, WIN = ramaddr("Plane_A_Buffer"), ramaddr("Windows_Opened_Num")
SLOTS = int(re.search(r"^VWFMENU_SLOTS\s*=\s*(\d+)", C, re.M).group(1))
SAVEN = int(re.search(r"^VWFMENU_SAVEN\s*=\s*(\d+)", C, re.M).group(1))
L = H.SlotLayout()
class _Refs:
    """mem[REFS + slot] resolves base or tail, like VWFMenu_RefAddr."""
    def __add__(self, slot): return L.ref(slot)
REFS = _Refs()
SAVETOP = BASE + int(re.search(
    r"^VWFMenu_SaveTop\s*=\s*VWF_RAM_Base\+\$([0-9A-Fa-f]+)", C, re.M).group(1), 16)
SAVEMARK = BASE + int(re.search(
    r"^VWFMenu_SaveMark\s*=\s*VWF_RAM_Base\+\$([0-9A-Fa-f]+)", C, re.M).group(1), 16)
SAVESTACK = BASE + int(re.search(
    r"^VWFMenu_SaveStack\s*=\s*VWF_RAM_Base\+\$([0-9A-Fa-f]+)", C, re.M).group(1), 16)
BLOCKED = BASE + int(re.search(
    r"^VWFMenu_FieldReuseBlocked\s*=\s*VWF_RAM_Base\+\$([0-9A-Fa-f]+)", C, re.M).group(1), 16)
smap = open("ps4disasm/vwf/menustripmap.bin", "rb").read()
names_txt = open("ps4disasm/vwf/menunames.bin", "rb").read()
names_idx = open("ps4disasm/vwf/menunameidx.bin", "rb").read()
tileslot = open("ps4disasm/vwf/pooltile.bin", "rb").read()
INV = {v: k for k, v in menustrip.code.items()}
LO = sym["InventoryNames"]
def text(i):
    o = int.from_bytes(names_idx[i * 2:i * 2 + 2], "big"); s = ""
    while names_txt[o] < 0xFE:
        s += INV[names_txt[o]]; o += 1
    return s
addr = {}
for o in range(0, len(smap), 2):
    i = (smap[o] << 8) | smap[o + 1]
    if i != 0xFFFF:
        addr.setdefault(text(i), LO + o // 2)

mem = bytearray(0x1000000); mem[:len(rom)] = rom
mem[0xFF0000 + 0xEF00:0xFF0000 + 0xEF02] = (0xC).to_bytes(2, "big")
def run(entry, **regs):
    cpu = CPU(mem, sym[entry])
    for k, v in regs.items():
        if k[0] == "a": cpu.a[int(k[1])] = v
        else: cpu.setd_w(int(k[1]), v)
    for _ in range(4000000):
        if cpu.step(): break
    else: raise SystemExit(entry + ": no exit")
def draw(name, row, col):
    mem[BASE + 0x128] = 1
    run("VWFMenu_DrawString", a0=addr[name], a1=PLANE + row * 128 + col * 2, d2=0xE680)
def clear_row(row, col, n):
    for c in range(col, col + n):
        mem[PLANE + row * 128 + c * 2:PLANE + row * 128 + c * 2 + 2] = b"\x06\x80"
def row_keys(row, col, n):
    out = []
    for c in range(col, col + n):
        t = int.from_bytes(mem[PLANE + row * 128 + c * 2:PLANE + row * 128 + c * 2 + 2], "big") & 0x7FF
        o = t - 0x680
        s = tileslot[o] if 0 <= o < len(tileslot) else 0xFF
        out.append(None if s == 0xFF else bytes(mem[L.key(s):L.key(s) + 8]))
    return out
def expect(name):
    """Cell keys, with an ink-less cell as None: the composed build points
    such a cell at the blank tile rather than spending a slot on it."""
    cells, span = menustrip.compose(name)
    keys = [bytes(span[y * 16 + c] for y in range(8)) for c in range(cells)]
    return [None if k == bytes(8) else k for k in keys]
def top():
    return int.from_bytes(mem[BASE + 0x100:BASE + 0x102], "big")

ok = True
def check(label, good, detail=""):
    global ok
    ok &= good
    print("  %s %-52s %s" % ("ok  " if good else "FAIL", label, detail))

for r in range(32):
    clear_row(r, 0, 64)
# window 0: the equipped-items panel, drawn with the OLD weapon
mem[WIN] = 0
run("VWFMenu_SaveMarkPush"); run("VWFMenu_Mark"); mem[WIN] = 1
draw("Psi Ring", 12, 19); draw("Psycho Wand", 14, 19); draw("Frad Mantle", 18, 19)
# window 1: the item list
run("VWFMenu_SaveMarkPush"); run("VWFMenu_Mark"); mem[WIN] = 2
listing = ["Wood Cane", "Graphite Shield", "Circlet", "Laser Barrier", "Psi Robe", "Force Cane"]
for i, n in enumerate(listing):
    draw(n, 2 + 2 * i, 36)
mark1 = top()
# the player equips Force Cane: the panel (outer) redraws its weapon row
clear_row(14, 19, 10)
draw("Force Cane", 14, 19)
check("panel row shares the list's slots (dedup across windows)",
      row_keys(14, 19, len(expect("Force Cane"))) == expect("Force Cane") and top() == mark1,
      "PoolTop %d, list mark %d" % (top(), mark1))
# the list window is destroyed: Release, then the sweep Window_Destroy runs
mem[WIN] = 1
run("VWFMenu_Release")
for i in range(len(listing)):
    clear_row(2 + 2 * i, 36, 10)
run("VWFMenu_Sweep")
check("after release+sweep the panel's cells are still marked live",
      all(mem[REFS + tileslot[(int.from_bytes(mem[PLANE + 14 * 128 + c * 2:PLANE + 14 * 128 + c * 2 + 2], "big") & 0x7FF) - 0x680]]
          for c in range(19, 19 + len(expect("Force Cane"))) if expect("Force Cane")[c - 19] is not None))
# ...and rebuilt in a different order, as a scrolled list would be
run("VWFMenu_SaveMarkPush"); run("VWFMenu_Mark"); mem[WIN] = 2
for i, n in enumerate(reversed(listing)):
    draw(n, 2 + 2 * i, 36)
check("panel weapon row survives the list being rebuilt in another order",
      row_keys(14, 19, len(expect("Force Cane"))) == expect("Force Cane"), "PoolTop %d" % top())
check("head and body rows untouched",
      row_keys(12, 19, len(expect("Psi Ring"))) == expect("Psi Ring") and row_keys(18, 19, len(expect("Frad Mantle"))) == expect("Frad Mantle"))
# and rebuilt with names that no longer include the shared one
mem[WIN] = 1
run("VWFMenu_Release")
for i in range(len(listing)):
    clear_row(2 + 2 * i, 36, 10)
run("VWFMenu_Sweep")
run("VWFMenu_SaveMarkPush"); run("VWFMenu_Mark"); mem[WIN] = 2
others = ["Titanium Axe", "Cure Paralysis", "Ceramic Sword", "Shadowblade", "Graphite Suit", "Moon Atomizer"]
for i, n in enumerate(others):
    draw(n, 2 + 2 * i, 36)
check("panel weapon row survives the list scrolling to other names",
      row_keys(14, 19, len(expect("Force Cane"))) == expect("Force Cane"), "PoolTop %d" % top())
check("the rebuilt list itself is intact",
      all(row_keys(2 + 2 * i, 36, len(expect(n))) == expect(n) for i, n in enumerate(others)))
check("the pool did not saturate doing it", top() < SLOTS, "PoolTop %d of %d" % (top(), SLOTS))

# PoolTop is not occupancy on this build: after a Release to a low mark the
# revived cells sit above it, so a pool can be entirely live-or-dead-unswept
# while PoolTop says there is room.  Alloc must then sweep once before it
# reports the pool full (PlasmaDagger's two blank cells, 2026-09-10).
mem[WIN] = 1
run("VWFMenu_Release")                      # back to the panel's mark
for i in range(len(others)):
    clear_row(2 + 2 * i, 36, 10)
run("VWFMenu_Sweep")
run("VWFMenu_SaveMarkPush"); run("VWFMenu_Mark"); mem[WIN] = 2
filler = ["Titanium Axe", "Cure Paralysis", "Ceramic Sword", "Shadowblade", "Graphite Suit",
          "Moon Atomizer", "Laser Barrier", "Circlet", "Wood Cane", "Graphite Shield"]
r = 0
for n in filler:
    draw(n, r, 40); r += 2
mark_full = top()
mem[WIN] = 1
run("VWFMenu_Release")                      # PoolTop drops; the cells stay live
low = top()
# the filler rows are gone from the plane but nobody has swept yet
for i in range(len(filler)):
    clear_row(2 * i, 40, 10)
draw("Dream Rod", 30, 40)
check("a full-but-unswept pool is swept before a cell is refused",
      row_keys(30, 40, len(expect("Dream Rod"))) == expect("Dream Rod"),
      "PoolTop was %d with %d cells live above it" % (low, mark_full - low))

# Two windows destroyed in a row.  Revealing the first synchronously would
# allocate while the second window's content is still live; deferring both
# reveals until the plane is next sent lets every revealed cell find a slot
# (Rudy's status Tech page, back from Skills: Procedan drawn with two holes).
WIN_GROUP = ramaddr("Win_Group_Start_Addr")
DEFERN = BASE + int(re.search(r"^VWFMenu_DeferN\s*=\s*VWF_RAM_Base\+\$([0-9A-Fa-f]+)", C, re.M).group(1), 16)
geom = {}
def wcreate(idx, w, h, x, y):
    """Window_Create's VWF half: a fake group entry, SaveRegion over the rect, Mark."""
    g = 0xFF2000
    geom[idx] = (w, h, x, y)
    mem[g + idx * 8:g + idx * 8 + 4] = bytes([w, h, x, y])
    mem[WIN_GROUP:WIN_GROUP + 4] = g.to_bytes(4, "big")
    run("VWFMenu_SaveMarkPush")
    for r in range(y, y + h):
        run("VWFMenu_SaveRegion", a0=PLANE + r * 128 + x * 2, d1=w)
    run("VWFMenu_Mark"); mem[WIN] += 1
def wdestroy(idx):
    mem[WIN] -= 1
    run("VWFMenu_Release")
    run("VWFMenu_DeferReveal", d0=idx)
    run("VWFMenu_SaveMarkPop")
def flush_with_walk():
    """FlushReveal calls RemapRegion, whose geometry walk uses addressing
    forms the harness lacks; stand in for the walk (as test_strip does) by
    remapping every cell of the queued window's rect from the hook, then
    skipping to the loop's tail.  Own stack: the hook runs nested CPUs."""
    cpu = CPU(mem, sym["VWFMenu_FlushReveal"], sp=0xFFE000)
    def ready(c):
        w, h, x, y = geom[c.d[0] & 0xFF]
        for r in range(y, y + h):
            for col in range(x, x + w):
                run("VWFMenu_RemapCell", a4=PLANE + r * 128 + col * 2)
        c.pc = sym["VWFMenu_RemapRegion_NextRow"] + 4
    cpu.on_pc[sym["VWFMenu_RemapRegion_Ready"]] = ready
    for _ in range(4000000):
        if cpu.step(): break
    else: raise SystemExit("flush: no exit")
def fresh():
    for r in range(32): clear_row(r, 0, 64)
    mem[BASE + 0x100:BASE + 0x102] = (0).to_bytes(2, "big")
    mem[SAVETOP:SAVETOP + 2] = (0).to_bytes(2, "big")
    mem[SAVEMARK:SAVEMARK + 32] = bytes(32)
    mem[BLOCKED] = 0
    for s_ in range(SLOTS):
        mem[REFS + s_] = 0
        mem[L.key(s_):L.key(s_) + 8] = bytes([0xFF] * 8)
    mem[WIN] = 0
    run("VWFMenu_SaveMarkPush"); run("VWFMenu_Mark"); mem[WIN] = 1

# Alloc_Take unlinks the stale key of the slot it is claiming before writing
# the new one.  When that stale key shares a bucket with a live slot and is
# not the chain head, KeyUnlink walks the chain - and used to come back with
# d0 pointing at the node it stopped on, so Take linked, counted and RETURNED
# the wrong slot: the cell drew the head's tile.  Every fresh slot's all-ones
# key hashes to bucket 0, so with 32 buckets this hit one glyph in 32.
fresh()
draw("Force Cane", 0, 4)
row0 = [tileslot[(int.from_bytes(mem[PLANE + c * 2:PLANE + c * 2 + 2], "big") & 0x7FF) - 0x680]
        for c in range(4, 4 + len(expect("Force Cane")))]
row0 = [s for s in row0 if s != 0xFF]
victim, live = row0[0], row0[-1]              # IndexRebuild links ascending, so
assert victim < live                           # the higher slot heads the chain
mem[PLANE + 4 * 2:PLANE + 4 * 2 + 2] = b"\x06\x80"   # free the victim's cell
mem[REFS + victim] = 0                         # FreeScan will claim it next
mem[L.key(victim):L.key(victim) + 8] = mem[L.key(live):L.key(live) + 8]
run("VWFMenu_IndexRebuild")                    # chain: live -> victim
draw("Psi Ring", 1, 4)
got = int.from_bytes(mem[PLANE + 128 + 4 * 2:PLANE + 128 + 4 * 2 + 2], "big") & 0x7FF
check("a take that had to walk its bucket returns the slot it claimed",
      tileslot[got - 0x680] == victim and mem[REFS + victim] == 1
      and mem[REFS + live] == 1,
      "wanted slot %d, cell holds slot %d; refs %d/%d"
      % (victim, tileslot[got - 0x680], mem[REFS + victim], mem[REFS + live]))

# A content-keyed slot may be referenced by multiple visible plane cells.
# Sweep must rebuild that multiplicity, not flatten it to one: otherwise
# overwriting either cell frees and recycles the tile under the other cell.
fresh()
draw("Force Cane", 0, 4)
cell0 = PLANE + 4 * 2
cell1 = PLANE + 20 * 2
mem[cell1:cell1 + 2] = mem[cell0:cell0 + 2]
tileword = int.from_bytes(mem[cell0:cell0 + 2], "big")
tile = tileword & 0x7FF
slot = tileslot[tile - 0x680]
run("VWFMenu_Sweep")
check("sweep counts two visible references to one slot",
      mem[REFS + slot] == 2,
      "refs %d" % mem[REFS + slot])
run("VWFMenu_Deref", d0=tileword)
check("overwriting one shared cell leaves the other reference live",
      mem[REFS + slot] == 1,
      "refs %d" % mem[REFS + slot])

# SaveRegion replaces each successfully recorded pool cell with a marker.  Its
# original physical tile is no longer present in the backup, so that reference
# must be released immediately.  Otherwise a deep Status > Tech > Skills path
# can markerize most of the screen, overflow on the remaining raw cells, block
# sweeping, and falsely leave all 114 slots live.
fresh()
draw("Force Cane", 0, 4)
draw("Force Cane", 2, 4)
visible = PLANE + 2 * 128 + 4 * 2
backup = 0xFFA000
mem[backup:backup + 2] = mem[PLANE + 4 * 2:PLANE + 4 * 2 + 2]
tileword = int.from_bytes(mem[backup:backup + 2], "big")
slot = tileslot[(tileword & 0x7FF) - 0x680]
# Model a stale multiplicity: both visible cells share this slot, but an older
# window operation left only one cached reference.  The captured corruption
# recycled Guardian Mail's middle cells this way when a covered Tech cell
# shared their key.
mem[REFS + slot] = 1
run("VWFMenu_SaveMarkPush")
run("VWFMenu_SaveRegion", a0=backup, d1=1)
marker = int.from_bytes(mem[backup:backup + 2], "big") & 0x7FF
check("SaveRegion refreshes shared-cell multiplicity before dereferencing",
      0x700 <= marker < 0x700 + SAVEN and mem[REFS + slot] == 1 and
      row_keys(2, 4, len(expect("Force Cane"))) == expect("Force Cane"),
      "marker $%03X surviving refs %d" % (marker, mem[REFS + slot]))

fresh()
draw("Force Cane", 0, 4)
draw("Force Cane", 2, 4)
cell = PLANE + 4 * 2
tileword = int.from_bytes(mem[cell:cell + 2], "big")
slot = tileslot[(tileword & 0x7FF) - 0x680]
before_refs = mem[REFS + slot]
run("VWFMenu_SaveMarkPush")
run("VWFMenu_SaveRegion", a0=cell, d1=1)
marker = int.from_bytes(mem[cell:cell + 2], "big") & 0x7FF
check("marker-backed cells release their physical pool reference",
      0x700 <= marker < 0x700 + SAVEN and mem[REFS + slot] == before_refs - 1,
      "marker $%03X refs %d -> %d" % (marker, before_refs, mem[REFS + slot]))

# The active saved-key ledger can contain historical keys no longer resident
# in the pool.  Once all 114 records are occupied, a newly covered pool cell
# must remain a raw tile reference and be pinned for that window's lifetime;
# otherwise its slot is recycled and the later reveal displays unrelated text.
fresh()
draw("Force Cane", 0, 4)
cell = PLANE + 4 * 2
raw = bytes(mem[cell:cell + 2])
tileword = int.from_bytes(raw, "big")
slot = tileslot[(tileword & 0x7FF) - 0x680]
mem[SAVETOP:SAVETOP + 2] = SAVEN.to_bytes(2, "big")
mem[SAVESTACK:SAVESTACK + SAVEN * 8] = bytes([0xFF]) * (SAVEN * 8)
mem[BLOCKED] = 0
run("VWFMenu_SaveMarkPush")
run("VWFMenu_SaveRegion", a0=cell, d1=1)
mark = int.from_bytes(mem[SAVEMARK + 2:SAVEMARK + 4], "big")
check("a full reveal ledger preserves the raw backup tile",
      bytes(mem[cell:cell + 2]) == raw and mem[REFS + slot] == 0xFF,
      "raw %s now %s slot %d key %s mark $%04X refs $%02X" %
      (raw.hex(), bytes(mem[cell:cell + 2]).hex(), slot,
       bytes(mem[L.key(slot):L.key(slot) + 8]).hex(),
       mark, mem[REFS + slot]))
check("ledger overflow blocks reclamation for exactly this window",
      mark == (0x8000 | SAVEN) and mem[BLOCKED] == 1,
      "mark $%04X blocked %d" % (mark, mem[BLOCKED]))
run("VWFMenu_Deref", d0=tileword)
check("the covered raw tile remains pinned after its visible cell is replaced",
      mem[REFS + slot] == 0xFE,
      "refs $%02X" % mem[REFS + slot])
run("VWFMenu_Mark"); mem[WIN] += 1
mem[WIN] -= 1
run("VWFMenu_SaveMarkPop")
check("closing the overflowed window restores its ledger mark and gate",
      int.from_bytes(mem[SAVETOP:SAVETOP + 2], "big") == SAVEN and mem[BLOCKED] == 0,
      "top %d blocked %d" % (int.from_bytes(mem[SAVETOP:SAVETOP + 2], "big"), mem[BLOCKED]))

fresh()
# the page beneath: two columns of names, 60-odd cells
page = ["Resta", "Grants", "Anti", "Zan", "Limpas", "Giresta", "Gigrants", "Procedan",
        "Gizan", "Reverser", "Ragrants", "Hinas", "Ryuker"]
for i, n in enumerate(page):
    draw(n, 2 * (i % 8), 4 + 10 * (i // 8))
before = {(2 * (i % 8), 4 + 10 * (i // 8), n): row_keys(2 * (i % 8), 4 + 10 * (i // 8), len(expect(n))) for i, n in enumerate(page)}
# two covering windows over it, filled with enough other names to leave no room
wcreate(1, 12, 18, 2, 0)
wcreate(2, 12, 18, 12, 0)
snapshot = bytes(mem[PLANE:PLANE + 32 * 128])   # what loc_6881E will restore: markers included
filler = ["Titanium Axe", "Cure Paralysis", "Ceramic Sword", "Shadowblade", "Graphite Suit",
          "Moon Atomizer", "Laser Barrier", "Circlet", "Wood Cane", "Graphite Shield",
          "Laconia Sword", "Reflect Mail", "Swift Helm", "Force Cane"]
for i, n in enumerate(filler):
    draw(n, 2 * (i % 8), 3 + 10 * (i // 8))
# back out: both windows destroyed in a row, then the plane is sent
for idx in (2, 1):
    wdestroy(idx)
mem[PLANE:PLANE + 32 * 128] = snapshot      # both saved blocks restored
queued = mem[DEFERN]
flush_with_walk()
after = {k: row_keys(k[0], k[1], len(expect(k[2]))) for k in before}
intact = [k[2] for k in before if after[k] == expect(k[2])]
check("two deferred reveals were queued, none run early", queued == 2, "queued %d" % queued)
check("every revealed name is whole after the flush", len(intact) == len(page),
      "%d of %d (PoolTop %d)" % (len(intact), len(page), top()))
check("the queue is empty afterwards", mem[DEFERN] == 0)

# SaveRegion dedups records by tile, and used to search EVERY record, not
# just its own pass's.  A slot covered by window A (record: its key then),
# freed, and reassigned to another name that window B then covers, made B's
# marker point at A's record: on reveal the cell was repointed to A's old
# content (Swift Helm's second cell became Force Cane's, 2026-09-11).
fresh()
draw("Force Cane", 0, 4)                     # slots 0..
wcreate(1, 12, 4, 2, 0)                      # A covers it: records 0.. by tile
run("VWFMenu_Sweep")                         # the covered slots are dead now
draw("Swift Helm", 10, 4)                    # ...and Swift Helm takes them
wcreate(2, 12, 4, 2, 8)                      # B covers Swift Helm
snapshot = bytes(mem[PLANE:PLANE + 32 * 128])
wdestroy(2)
mem[PLANE:PLANE + 32 * 128] = snapshot
flush_with_walk()
good = row_keys(10, 4, len(expect("Swift Helm"))) == expect("Swift Helm")
check("a marker never matches an older window's record for a reused slot", good)

# Composed records with the SAME immutable key may safely be shared across
# save passes.  Without this global key dedup, deeply nested Status subpages
# filled the 88-record stack even though sixteen of those records were exact
# duplicates; the next windows then restored raw references to recycled tiles.
fresh()
draw("Force Cane", 0, 4)
wcreate(1, 12, 4, 2, 0)
saved_once = int.from_bytes(mem[BASE + 0xA88:BASE + 0xA8A], "big")
draw("Force Cane", 0, 4)
wcreate(2, 12, 4, 2, 0)
saved_twice = int.from_bytes(mem[BASE + 0xA88:BASE + 0xA8A], "big")
check("nested save passes reuse records with the same composition key",
      saved_twice == saved_once,
      "SaveTop %d then %d" % (saved_once, saved_twice))

print("ALL PASS" if ok else "FAILURES ABOVE")
sys.exit(0 if ok else 1)
