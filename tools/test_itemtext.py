"""The camp Item window: LOOK and DSCD draw with the menu VWF.

Both options were still fixed-width, and DSCD additionally printed the US
build's cell-limited abbreviation - LTHRSHIELD - because the sentence it
assembles in RAM is copied out of InventoryNames.  Menu lists never read that
table (they draw prerendered strips keyed by its offsets), so nothing had ever
noticed the abbreviations were still there.

Two things are checked, because the fix has two halves:

  * the four draw sites in the region now ask for the proportional face and
    the translated name table, and no longer reference the fixed-width pair;
  * VWFMenu_DrawWindowRun really composes in LoadWindowTiles' *slow* mode when
    the caller has forced composition, and pays the per-character delay once
    per cell so the line still types itself out.  The delay is what made this
    non-trivial: the composer swallows a whole run, so without the pacing the
    description would appear all at once.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import menuharness as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "Exodus_2.1", "Savestates", "ps4en-fieldtech.exs")
ROM = os.environ.get("PS4_ROM", os.path.join(ROOT, "ps4disasm", "ps4built.bin"))  # paired with PS4_LST via menuharness

ok = True
sym = H.Symbols()
rom = open(ROM, "rb").read()


def check(label, good, detail=""):
    global ok
    ok &= good
    print("  %s %-47s %s" % ("ok  " if good else "FAIL", label, detail))


def jsr(name):
    return b"\x4e\xb9" + sym[name].to_bytes(4, "big")


def lea_a0(name):
    return b"\x41\xf9" + sym[name].to_bytes(4, "big")


# ---------------------------------------------------------------- call sites
def span(a, b):
    return rom[sym[a]:sym[b]]


# The Item page is the one safe reclamation scope: its field Window_Create
# records covered cells for remap, while battle's private window copies do
# not.  Keep the sweep and permission byte paired exactly once around the
# synchronous list repaint so neither can leak into battle or run per row.
itemlist = span("Win_ItemList", "Win_ItemListMain")
constants = open(os.path.join(ROOT, "ps4disasm", "ps4.constants.asm"),
                 encoding="utf-8", errors="replace").read()
def vwf_offset(name):
    m = re.search(r"^" + re.escape(name) +
                  r"\s*=\s*VWF_RAM_Base\+\$([0-9A-Fa-f]+)", constants, re.M)
    assert m, name
    return int(m.group(1), 16)
reuse_addr = 0xFFFF0000 | ((0x5400 + int(re.search(
    r"^VWFMenu_StripReuseOK\s*=\s*VWF_RAM_Base\+\$([0-9A-Fa-f]+)",
    constants, re.M).group(1), 16)) & 0xFFFF)
reuse_on = b"\x13\xfc\x00\x01" + reuse_addr.to_bytes(4, "big")
reuse_off = b"\x42\x39" + reuse_addr.to_bytes(4, "big")
sweep = jsr("VWFMenu_Sweep")
on_at = itemlist.find(reuse_on)
sweep_at = itemlist.find(sweep)
off_at = itemlist.find(reuse_off)
page_cmp_at = itemlist.find(b"\xba\x78\xe2\x06",
                            sweep_at + len(sweep))
check("Item page scopes one reclaim sweep",
      itemlist.count(reuse_on) == itemlist.count(sweep) ==
      itemlist.count(reuse_off) == 1 and
      0 <= on_at < sweep_at < page_cmp_at < off_at)

# LOOK descriptions are static two-line records and every translated line fits
# the stock 28-cell field. Keeping them fixed-width costs no pool slots; the
# proportional path could exhaust after line one and truncate Hunter Knife or
# Claw even when a sweep found nothing else reclaimable.
look = span("Win_ItemActionLook", "LookOpt_ChkCreateEquipWindow")
check("LOOK descriptions use the pool-free fixed renderer",
      look.count(jsr("LoadWindowTiles")) == 1
      and look.count(jsr("VWFField_LoadWindowTiles")) == 0,
      "$%06X" % sym["Win_ItemActionLook"])

# The equip sub-window between them is chrome and a party-name list, and both
# are already right: the "equip" label is meant to stay fixed-width, and
# Character_Stats names are recognised by the composer's own address test.
# Asserting they are untouched keeps this test honest about its scope.
equip = span("LookOpt_ChkCreateEquipWindow", "Win_ItemActionDiscard")
check("the equip sub-window is left alone",
      equip.count(jsr("LoadWindowTiles")) == 2
      and equip.count(jsr("VWFField_LoadWindowTiles")) == 0)

# The three discard notices: the prompt, the confirmation, and the refusal.
dscd = span("Win_ItemActionDiscard", "Win_TelepipePlaceList")
# The one LoadWindowTiles left in the region draws the YES/NO option window,
# which is chrome and matches every other YES/NO window in the game.
# All three notices draw fixed-width now, like the LOOK description: one cell
# per character, costing the tile pool nothing.  With the YES/NO window that
# is four fixed draws in the region and no proportional ones.
check("every discard notice uses the pool-free fixed renderer",
      dscd.count(jsr("LoadWindowTiles")) == 4)
check("none of them still composes",
      dscd.count(jsr("VWFField_LoadWindowTiles")) == 0)
check("none still reads InventoryNames",
      dscd.count(lea_a0("InventoryNames")) == 0)
check("all three read the translated name table",
      dscd.count(lea_a0("VWFField_ItemNames")) == 3)

# The three USE notices.  "X is used!" is built twice - once for a single
# target, once for the whole party - and the healing result is drawn into the
# same window directly underneath it, so both halves have to change together
# or one box shows two different faces.
single = span("Win_ItemUsedMsg", "ItemUsed_MoonDew")
check("USE names the item from the translated table",
      single.count(lea_a0("VWFField_ItemNames")) == 1
      and single.count(lea_a0("InventoryNames")) == 0)
check("USE draws its notice with the fixed renderer",
      single.count(jsr("LoadWindowTiles")) == 1
      and single.count(jsr("VWFField_LoadWindowTiles")) == 0)

# The recovered-HP numerals keep their fixed cells: they are a numeric field
# in their own window and the columns have to line up.
party = span("ItemUsed_AllAlliesLoop", "Win_ItemUsedMsgMain")
check("both healing results draw fixed-width",
      party.count(jsr("VWFField_LoadWindowTiles")) == 0
      and party.count(lea_a0("VWFField_ItemNames")) == 1)
check("the recovered-HP numerals stay fixed-width",
      party.count(jsr("LoadWindowTiles")) == 4
      and party.count(lea_a0("InventoryNames")) == 0)

nothing = span("ItemAction_Nothing", "Win_ItemActionLook")
check("the no-effect notices follow suit",
      nothing.count(jsr("LoadWindowTiles")) == 2
      and nothing.count(jsr("VWFField_LoadWindowTiles")) == 0
      and nothing.count(lea_a0("VWFField_ItemNames")) == 1
      and nothing.count(lea_a0("InventoryNames")) == 0)

# ------------------------------------------------------------ the prompt text
CODE = {' ': 0}
for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"): CODE[c] = 1 + i
for i, c in enumerate("0123456789"): CODE[c] = 27 + i
for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"): CODE[c] = 57 + i
CODE['-'] = 0x31; CODE['!'] = 0x32; CODE['?'] = 0x33; CODE['.'] = 0x53
widths = open(os.path.join(ROOT, "ps4disasm", "vwf", "menuwidth.bin"), "rb").read()
rev = {v: k for k, v in CODE.items()}
raw = rom[sym["loc_2AA132"]:]
raw = raw[:raw.index(0xFF)]
prompt = "".join("{FC}" if c == 0xFC else rev.get(c, "?") for c in raw)
# One shape for all three: the item name alone on line 1, the verb phrase on
# line 2.  Line 1 can then never overflow, whatever the name.
check("the prompt puts the name on its own line",
      prompt == ".{FC}Discard this?", repr(prompt))

# ------------------------------------------------------------------- widths
# Fixed-width, so the budget is characters, not pixels.  Line 1 of every notice
# is the item name (plus a period on the prompt) and line 2 is a fixed string,
# so the whole family is bounded by the longest item name.
def text_of(addr, terms=(0xFE, 0xFF)):
    out, i = [], addr
    while rom[i] not in terms:
        out.append(rom[i]); i += 1
    return out

def table_rows(addr, count, term=0xFE):
    """Split a terminated name table into its entries, as byte lists."""
    out, cur, i = [], [], addr
    while len(out) < count:
        b = rom[i]; i += 1
        if b == term:
            out.append(cur); cur = []
        else:
            cur.append(b)
    return out

names = table_rows(sym["VWFField_ItemNames"], 160)
longest = max(len(n) for n in names)
check("the longest item name fits line 1 with its period",
      longest + 1 <= 28, "%d + 1 of 28 cells" % longest)

for label, at in (("prompt", "loc_2AA132"), ("confirmation", "loc_2AA14C"),
                  ("refusal", "loc_2AA162")):
    body = text_of(sym[at])
    lines = [len(x) for x in bytes(body).split(bytes([0xFC]))]
    worst = max(lines + [longest])
    check("the %s fits its 28-cell field" % label, worst <= 28,
          "widest line %d cells" % worst)

# --------------------------------------------------------------- paced draw
# Feed the composer real strings in slow mode with composition forced, exactly
# as Win_ItemActionLook now does.  DMAPlane_A_VInt is stubbed to an rts: the
# harness has no VDP timing, and counting entries to it is the only direct
# evidence that the pacing ran at all.
FORCE = sym["VWF_RAM_Base"] + 0x12B

state = H.load_state(STATE)
plane = sym["Plane_A_Buffer"]
paced = [0]


def machine():
    m = H.Machine(rom, state)
    m.m[sym["DMAPlane_A_VInt"]:sym["DMAPlane_A_VInt"] + 2] = b"Nu"
    m.wb(FORCE, 1)
    m.wb(sym["Message_Speed"], 0)
    m.wb(sym["Message_Speed"] + 1, 0)
    m.wb(sym["Joypad_Held"], 0)
    paced[0] = 0
    m.on_pc[sym["DMAPlane_A_VInt"]] = lambda _c: paced.__setitem__(0, paced[0] + 1)
    m.a[1] = plane
    return m


def segment(m, addr):
    """One trip through DrawWindowRun, the way LoadWindowTiles enters it:
    the first character already fetched into d1 and a0 stepped past it."""
    # Each return consumes the harness's sentinel, so a second segment needs
    # its own or the rts leaves the composer entirely.
    m.a[7] -= 4
    m.wl(m.a[7], m.SENTINEL)
    m.pc = sym["VWFMenu_DrawWindowRun"]
    m.d[1] = rom[addr]
    m.d[2] = 0x680
    m.d[4] = 0
    m.a[0] = addr + 1
    steps = 0
    while steps < 400000 and not m.step():
        steps += 1
    return m.a[0]


def cells_written(m):
    n = (m.a[1] - plane) // 2
    return [m.rw(plane + 2 * i) & 0x7FF for i in range(n)]


# A whole description line, composed and paced.
text = sym["InventoryDescriptions2"]
run = []
i = text
while rom[i] < 0x80:
    run.append(rom[i])
    i += 1
want = (sum(widths[c] for c in run) + 7) // 8

m = machine()
end = segment(m, text)
tiles = cells_written(m)
check("the whole run was consumed", end == text + len(run),
      "%d characters" % len(run))
check("it composed rather than writing one fixed cell", len(tiles) == want,
      "%d cells for %dpx" % (len(tiles), sum(widths[c] for c in run)))
check("every cell is a pool tile", all(0x680 <= t <= 0x6FF for t in tiles),
      " ".join("$%03X" % t for t in tiles[:6]) + " ...")
# The composer must be atomic with respect to the window stack.  It used to
# pay the stock per-character delay inside the cell loop so the line still
# typed itself out, and that crashed Item > LOOK: a delay is DMAPlane_A_VInt,
# which waits for the VInt, and the window-open animation on the far side of
# it calls VWFMenu_Release, freeing the tiles the half-finished run had just
# allocated.  Yielding mid-run is the bug, so assert it cannot happen.
check("the composer never yields to the VInt mid-run", paced[0] == 0,
      "%d delays" % paced[0])

# ------------------------------------------------------------- HP/TP glyphs
# The healing notices open with the two-tile HP/TP graphic at $78/$79, which
# has width 0 and no proportional art.  The composer has to break its run for
# it and emit the stock tile, or the line reads " fully recovered!" with the
# subject silently deleted.  Drive it a segment at a time, which is what
# LoadWindowTiles does when its character is not part of a composed run.
hp = sym["WinTiles_HPFullyRecoveredStr"] + 1        # past the leading $FC
check("the notice really starts with the glyph pair",
      rom[hp] == 0x78 and rom[hp + 1] == 0x79,
      "$%02X $%02X" % (rom[hp], rom[hp + 1]))

m = machine()
at = hp
for _ in range(3):                                  # $78, $79, then the words
    at = segment(m, at)
tiles = cells_written(m)
tail = []
i = hp + 2
while rom[i] < 0x80:
    tail.append(rom[i])
    i += 1
words = (sum(widths[c] for c in tail) + 7) // 8

check("the glyph pair survives the composed run",
      tiles[:2] == [0x6F8, 0x6F9], " ".join("$%03X" % t for t in tiles[:2]))
check("the words after it are still composed",
      len(tiles) == 2 + words, "%d cells, %d of them composed"
      % (len(tiles), len(tiles) - 2))
check("the whole notice was consumed", at == hp + 2 + len(tail))

# ------------------------------------------------------- pool headroom
# A forced dynamic run must reserve enough room for all of its cells before
# drawing. Recovery needs both the field game mode and a managed window
# lifetime. Battle owns private page buffers full of raw tile IDs that Sweep
# cannot see, so identical pressure there must fail visibly without reclaiming
# any staged tile.
BASE = sym["VWF_RAM_Base"]
POOLTOP = BASE + 0x100
KEYS = BASE + 0x140
REFS = BASE + vwf_offset("VWFMenu_Refs")
STRIPOF = BASE + vwf_offset("VWFMenu_StripOf")
FIELD_DEPTH = BASE + vwf_offset("VWFMenu_FieldReuseDepth")
FIELD_BLOCKED = BASE + vwf_offset("VWFMenu_FieldReuseBlocked")
RECLAIM_INHIBIT = BASE + vwf_offset("VWFMenu_ReclaimInhibit")
SLOTS = int(re.search(r"^VWFMENU_SLOTS\s*=\s*(\d+)", constants, re.M).group(1))


def pressured(mode, managed=False):
    m = machine()
    m.wb(sym["Game_Mode_Index"], 0)
    m.wb(sym["Game_Mode_Index"] + 1, mode)
    m.wb(FIELD_DEPTH, int(managed))
    m.wb(FIELD_BLOCKED, 0)
    m.wb(RECLAIM_INHIBIT, 0)
    m.m[plane:plane + 64 * 32 * 2] = bytes(64 * 32 * 2)
    prefill = SLOTS - 5
    m.wb(POOLTOP, prefill >> 8)
    m.wb(POOLTOP + 1, prefill)
    L = H.SlotLayout()
    for slot in range(SLOTS):          # base and tail, as the allocator sees them
        m.m[L.key(slot):L.key(slot) + 8] = bytes([0xA5]) * 8
        m.wb(L.ref(slot), 1)
        at = STRIPOF + slot * 2
        m.wb(at, 0xFF)
        m.wb(at + 1, 0xFE)
    segment(m, text)
    return cells_written(m), bytes(m.rb(L.ref(s)) for s in range(prefill))


field_tiles, field_old_refs = pressured(0x0C, managed=True)
check("managed field overflow reclaims before the complete run",
      len(field_tiles) == want and all(t != 0x680 for t in field_tiles),
      "%d/%d cells have ink" % (sum(t != 0x680 for t in field_tiles), want))

mode_only_tiles, mode_only_refs = pressured(0x0C)
check("field mode alone never sweeps without managed capability",
      len(mode_only_tiles) == want and any(t == 0x680 for t in mode_only_tiles)
      and all(mode_only_refs),
      "%d/%d cells have ink" % (sum(t != 0x680 for t in mode_only_tiles), want))

battle_tiles, battle_old_refs = pressured(0x14, managed=True)
check("battle overflow never sweeps private page references",
      len(battle_tiles) == want and any(t == 0x680 for t in battle_tiles)
      and all(battle_old_refs),
      "%d/%d cells have ink" % (sum(t != 0x680 for t in battle_tiles), want))

# ------------------------------------------- battle cannot acquire the capability
# The pressure tests above prove battle is denied at run time.  These assert the
# structure that makes it so, which a refactor could remove without any of them
# going red: the gate really consults Game_Mode_Index, and the three capability
# counters are driven only by the VWF engine's own Mark/SaveMarkPop pair.
gate = rom[sym["VWFMenu_FieldReclaimAllowed"]:
           sym["VWFMenu_FieldReclaimAllowed"] + 0x40]
check("the gate tests Game_Mode_Index for field mode",
      bytes.fromhex("0c40000c") in gate, "cmpi.w #$C,d0")

game_src = open(os.path.join(ROOT, "ps4disasm", "ps4.asm"),
                encoding="utf-8", errors="replace").read()
for counter in ("VWFMenu_FieldReuseDepth", "VWFMenu_FieldReuseBlocked",
                "VWFMenu_ReclaimInhibit"):
    check("%s is engine-driven only" % counter,
          game_src.count(counter) == 0,
          "%d reference(s) from ps4.asm" % game_src.count(counter))
# The one explicit scope is the field Item page repaint: one set, one clear.
check("only one explicit reuse scope outside the engine",
      game_src.count("VWFMenu_StripReuseOK") == 2,
      "%d reference(s)" % game_src.count("VWFMenu_StripReuseOK"))

print("ALL PASS" if ok else "FAILURES ABOVE")
sys.exit(0 if ok else 1)
