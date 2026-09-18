"""Reproduce and guard battle transient-name pool exhaustion.

Technique User reads title-case Resta from EnemySkillNames and composes it.
The level-up message reaches the legacy RES entry only as the key for the
translated Resta strip.  With two pool slots left, those two paths reproduce
the reported pair exactly: a partial enemy name and a wholly blank learned
Technique.  Dedicated window marks must return both allocations when their
raw battle buffers cease to be reachable.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import menuharness as H


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "Exodus_2.1", "Savestates",
                     "ps4en-fieldtech.exs")
symbols = H.Symbols()
rom = open(H.ROM, "rb").read()
state = H.load_state(STATE)

BASE = symbols["VWF_RAM_Base"]
POOLTOP = BASE + 0x100
_CONST = open(os.path.join(ROOT, "ps4disasm", "ps4.constants.asm"),
             encoding="utf-8", errors="replace").read()
def vwfoff(name):
    """Offset from VWF_RAM_Base, read from the constants, never hardcoded:
    the sized arrays move whenever VWFMENU_SLOTS changes."""
    m = re.search(r"^" + re.escape(name) + r"\s*=\s*VWF_RAM_Base\+\$([0-9A-Fa-f]+)",
                  _CONST, re.M)
    assert m, name
    return int(m.group(1), 16)
REFS = BASE + vwfoff("VWFMenu_Refs")
KEYS = BASE + 0x140
STRIPOF = BASE + vwfoff("VWFMenu_StripOf")
ACTION = BASE + vwfoff("VWFMenu_BattleActionMark")
ENEMY = BASE + vwfoff("VWFMenu_BattleEnemyMark")
RESULT = BASE + vwfoff("VWFMenu_BattleResultMark")
RESULT_ACTIVE = BASE + vwfoff("VWFMenu_BattleResultActive")
# Read the battle capacity rather than restating it.  The field pool appends
# the duplicate-uppercase bank, but battle sprite art can occupy that bank and
# must remain capped at the original safe range.
SLOTS = int(re.search(r'^VWFMENU_BATTLE_SLOTS\s*=\s*(\d+)', _CONST,
                      re.M).group(1))
FIELD_SLOTS = int(re.search(r'^VWFMENU_SLOTS\s*=\s*(\d+)', _CONST,
                            re.M).group(1))
PLANE = symbols["Plane_A_Buffer"]

ok = True


def check(label, good, detail=""):
    global ok
    ok &= good
    print("  %s %-55s %s" %
          ("ok  " if good else "FAIL", label, detail))


check("battle excludes the field-only alphabet slots",
      SLOTS == 88 and FIELD_SLOTS > SLOTS,
      "%d battle, %d field" % (SLOTS, FIELD_SLOTS))


def entry(table, ident, terminator):
    at = symbols[table]
    for _ in range(ident - 1):
        while rom[at] != terminator:
            at += 1
        at += 1
    return at


def decode(at, terminator):
    out = ""
    while rom[at] != terminator:
        out += H.CHAR.get(rom[at], "?")
        at += 1
    return out


def write_word(m, at, value):
    m.wb(at, value >> 8)
    m.wb(at + 1, value)


def machine(top):
    m = H.Machine(rom, state)
    m.m[BASE:BASE + 0xFF6] = bytes(0xFF6)
    m.m[PLANE:PLANE + 64 * 32 * 2] = bytes(64 * 32 * 2)
    write_word(m, symbols["Game_Mode_Index"], 0x14)  # battle: no plane sweep
    write_word(m, POOLTOP, top)
    m.m[KEYS:KEYS + SLOTS * 8] = bytes([0xA5]) * (SLOTS * 8)
    m.m[REFS:REFS + SLOTS] = bytes([1]) * SLOTS
    for slot in range(SLOTS):
        write_word(m, STRIPOF + slot * 2, 0xFFFE)
    return m


def draw(m, at):
    m.a[7] -= 4
    m.wl(m.a[7], m.SENTINEL)
    m.pc = symbols["VWFMenu_DrawString"]
    m.a[0] = at
    m.a[1] = PLANE
    m.d[2] = 0xE680
    for _ in range(400000):
        if m.step():
            break
    else:
        raise RuntimeError("VWFMenu_DrawString did not return")
    count = (m.a[1] - PLANE) // 2
    return [m.rw(PLANE + i * 2) & 0x7FF for i in range(count)]


enemy_resta = entry("EnemySkillNames", 0x45, 0xFF)
legacy_res = entry("TechniqueNames", 24, 0xFE)
check("Technique User source is the full EnemySkillNames entry",
      decode(enemy_resta, 0xFF) == "Resta",
      decode(enemy_resta, 0xFF))
check("legacy table really contains RES, but only as a strip key",
      decode(legacy_res, 0xFE) == "RES",
      decode(legacy_res, 0xFE))

# Two remaining slots reproduce the user's exact distinction: composition can
# succeed partly, while a three-cell strip is atomic and fails as a whole.
composed_full = draw(machine(0), enemy_resta)
strip_full = draw(machine(0), legacy_res)
composed_tight = draw(machine(SLOTS - 2), enemy_resta)
strip_tight = draw(machine(SLOTS - 2), legacy_res)
from buildflags import strips_built, skipped
# Cell counts come from the face, not from a constant: a trailing gap that
# spills over a cell boundary gives the run a cell with no ink, which the
# composed build points at the blank tile and the strip build draws as a
# paper tile of its own.  (Under the small-caps face Resta was four cells,
# the last one blank; the mixed-case face fits it in three.)
import menustrip
RESTA_CELLS, _span = menustrip.compose("Resta")
RESTA_INKED = sum(1 for c in range(RESTA_CELLS)
                  if any(_span[y * 16 + c] for y in range(8)))
RESTA_INK = RESTA_CELLS if strips_built(symbols.text) else RESTA_INKED
check("full-capacity enemy Resta is a %d-cell VWF run" % RESTA_CELLS,
      len(composed_full) == RESTA_CELLS and sum(t != 0x680 for t in composed_full) == RESTA_INK,
      "%d ink" % sum(t != 0x680 for t in composed_full))
check("two free slots truncate composed Resta after two cells",
      len(composed_tight) == RESTA_CELLS
      and sum(t != 0x680 for t in composed_tight) == 2,
      "%d/%d ink" % (sum(t != 0x680 for t in composed_tight), RESTA_CELLS))
if not strips_built(symbols.text):
    skipped("pressure blanks the atomic learned-Tech strip",
            "composed names are charged per cell, like enemy Resta above")
else: check("the same pressure blanks the atomic learned-Tech strip",
      len(strip_tight) == RESTA_CELLS and all(t == 0x680 for t in strip_tight),
      "%d/%d ink" % (sum(t != 0x680 for t in strip_tight), RESTA_CELLS))
check("rolling back to an exact window mark restores the full strip",
      len(strip_full) == RESTA_CELLS and sum(t != 0x680 for t in strip_full) == RESTA_INK,
      "%d/%d ink" % (sum(t != 0x680 for t in strip_full), RESTA_CELLS))


def move_abs(src, dst):
    # The assembler sign-extends $FFxxxx RAM addresses in absolute-long
    # operands, while the emulator symbol resolver returns 24-bit addresses.
    src |= 0xFF000000
    dst |= 0xFF000000
    return b"\x33\xF9" + src.to_bytes(4, "big") + dst.to_bytes(4, "big")


def body(start, end):
    return rom[symbols[start]:symbols[end]]


captures = [
    ("player action captures its exact mark", "loc_4A94", "loc_4ABC",
     move_abs(POOLTOP, ACTION)),
    ("player action releases only after teardown", "loc_4B6E", "loc_4BA4",
     move_abs(ACTION, POOLTOP)),
    ("enemy action captures its exact mark", "loc_B4E0", "loc_B542",
     move_abs(POOLTOP, ENEMY)),
    ("enemy action releases only after teardown", "loc_B59A", "loc_B59E",
     move_abs(ENEMY, POOLTOP)),
]
for label, start, end, instruction in captures:
    check(label, body(start, end).count(instruction) == 1)

results = body("loc_4624", "loc_4640")
check("results panel tests its first-use flag",
      results.count(b"\x4A\x39"
                    + (RESULT_ACTIVE | 0xFF000000).to_bytes(4, "big")) == 1)
check("results panel preserves the visible panel while composing",
      results.count(move_abs(RESULT, POOLTOP)) == 0)
check("results panel captures its base only on first use",
      results.count(move_abs(POOLTOP, RESULT)) == 1)
check("results panel marks its scope active",
      results.count(b"\x50\xF9"
                    + (RESULT_ACTIVE | 0xFF000000).to_bytes(4, "big")) == 1)

commit = body("VWFMenu_BattleResultCommit", "VWFMenu_BattleResultCommit_End")
plane_call = bytes.fromhex("4EB9") + symbols["PlaneMapToRAM"].to_bytes(4, "big")
sweep_jump = bytes.fromhex("4EF9") + symbols["VWFMenu_Sweep"].to_bytes(4, "big")
check("results commit publishes the new plane before sweeping",
      commit.find(plane_call) >= 0 and commit.find(sweep_jump) > commit.find(plane_call))

# ------------------------------------------- item page rebuild (Checkpoint C)
# The four page buffers are pre-rendered when the item menu opens, allocating a
# strip run for every item in the inventory - four pages against the measured
# root of 26 is far past the cap, so later pages drew blank.  Battle cannot
# reclaim, so the lever is to let only the VISIBLE page own tiles: rewind to the
# battle root and rebuild the page being moved to.
#
# These are STRUCTURAL checks.  Whether the rebuild renders correctly in a live
# battle is a playtest question, not a harness one.
render = symbols["Battle_ItemPageRender"]
body = rom[render:render + 0x50]

sweep_call = bytes.fromhex("4eb9") + symbols["VWFMenu_Sweep"].to_bytes(4, "big")
check("the page rebuild never sweeps", sweep_call not in body,
      "battle keeps no saved-region bookkeeping")
reuse = (symbols["VWF_RAM_Base"] + 0x12A).to_bytes(4, "big")[1:]
check("the page rebuild never takes StripReuseOK", reuse not in body)
base = (symbols["VWF_RAM_Base"] + vwfoff("VWFMenu_BattleBase")).to_bytes(4, "big")[1:]
check("the page rebuild rewinds to the battle root", base in body,
      "VWFMenu_BattleBase")

# Both page directions must go through it, or one of them still displays a
# buffer whose tiles the other direction's rewind has already reused.
src = open(os.path.join(ROOT, "ps4disasm", "ps4.asm"),
           encoding="utf-8", errors="replace").read()
# Every way of arriving at a page must rebuild it, or that page displays a
# buffer whose tiles another arrival's rewind has already handed out.
def span(a, b):
    return src[src.index(NL0 + a):src.index(NL0 + b)]
NL0 = chr(10)
for label, (a, b) in {
        "page right": ("loc_2310:", "Battle_ItemNextWin:"),
        "page left":  ("loc_235C:", "Battle_ItemPrevWin:"),
        "menu open":  ("loc_2024:", "loc_204E:")}.items():
    check("rebuild is wired into " + label,
          "Battle_ItemPageRender" in span(a, b))

# Battle_ItemWindow gates paging on the low byte of the two arrow words in the
# page buffer.  loc_204E wipes them, so the rebuild MUST put them back or the
# rebuilt page cannot be paged out of.  Offsets here must match the gate.
rebuild = span("Battle_ItemPageRender:", "loc_2310:")
check("rebuild restores the left arrow", "#$66E6, (a0)" in rebuild)
check("rebuild restores the right arrow", "#$6EE6, $1A(a0)" in rebuild)
gate = span("Battle_ItemWindow:", "loc_21E4:")
check("left gate reads the restored left arrow", "#$E6, $1(a2)" in gate)
check("right gate reads the restored right arrow", "#$E6, $1B(a2)" in gate)

anim = src[src.index(NL0 + "loc_FBE:"):src.index(NL0 + "Battle_FillTechList:")]
check("the rebuild is not wired into the open animation",
      "Battle_ItemPageRender" not in anim,
      "loc_FBE re-enters once per frame")

print("ALL PASS" if ok else "FAILURES ABOVE")
sys.exit(0 if ok else 1)
