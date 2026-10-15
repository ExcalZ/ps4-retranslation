"""The battle full-pack drop list stays inside the battle pool.

An item dropped with the 40-slot pack full opens a ten-page list.  The stock
code pre-rendered every page into $FFFF3600.. and paged by copying buffers,
so all 40 names composed at once and the 88-slot battle pool ran dry on page
three: "Want to discard?", its Yes/No and the "discarded."/"received!" tails
then drew blank (reported 2026-10-15).  Now only the visible page composes
(VWFMenu_PackPagesOpen and friends).  This runs the drop routines in order
against a pool already holding a 30-slot battle base, and fails if any cell
is refused or the pool reaches its cap.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import menuharness as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
symbols = H.Symbols()
rom = open(H.ROM, "rb").read()
state = H.load_state(os.path.join(ROOT, "work", "fixtures", "ps4en-fieldtech.exs"))
_CONST = open(os.path.join(ROOT, "ps4disasm", "ps4.constants.asm"),
              encoding="utf-8", errors="replace").read()


def vwfoff(name):
    m = re.search(r"^" + re.escape(name) + r"\s*=\s*VWF_RAM_Base\+\$([0-9A-Fa-f]+)", _CONST, re.M)
    assert m, name
    return int(m.group(1), 16)


BASE = symbols["VWF_RAM_Base"]
POOLTOP = BASE + 0x100
KEYS = BASE + 0x140
REFS = BASE + vwfoff("VWFMenu_Refs")
STRIPOF = BASE + vwfoff("VWFMenu_StripOf")
SLOTS = int(re.search(r"^VWFMENU_BATTLE_SLOTS\s*=\s*(\d+)", _CONST, re.M).group(1))
ROUTINE = 0xFFFF4190
BLANK = 0x680
START = 30                       # party names, enemy names, the COMD window

ok = True


def check(label, good, detail=""):
    global ok
    ok &= good
    print("  %s %-58s %s" % ("ok  " if good else "FAIL", label, detail))


def ww(m, at, v):
    m.wb(at, v >> 8)
    m.wb(at + 1, v)


m = H.Machine(rom, state)
m.m[BASE:BASE + 0xBA8] = bytes(0xBA8)
ww(m, symbols["Game_Mode_Index"], 0x14)
ww(m, POOLTOP, START)
ww(m, BASE + vwfoff("VWFMenu_BattleBase"), START)
for slot in range(SLOTS):
    ww(m, STRIPOF + slot * 2, 0xFFFE)
for slot in range(START):                    # occupied by keys no name will match
    m.m[KEYS + slot * 8:KEYS + slot * 8 + 8] = bytes([0xA5, slot]) * 4
    m.m[REFS + slot] = 1
# Forty distinct equipment and consumables; the drop is a duplicate of slot 2
items = [0x04, 0x7D, 0x8D, 0x0A] + list(range(0x01, 0x7C))[1::3][:36]
m.m[symbols["Inventory"]:symbols["Inventory"] + 40] = bytes(items)
m.wb(symbols["Dropped_Item"], 0x8D)
ww(m, symbols["Battle_Item_Index"], 0)
ww(m, symbols["Vehicle_Index"], 0)

FULL = symbols["VWFMenu_Alloc_FullReally"]
PACKMARK = BASE + vwfoff("VWFMenu_BattlePackMark")
PAGETOP = BASE + vwfoff("VWFMenu_BattlePackPageTop")
TRACE = "-v" in sys.argv
refused = {}


def run(label, routine, d5=0x20):
    m.a[7] = 0xFFFE00 - 4
    m.wl(m.a[7], m.SENTINEL)
    m.pc = symbols[routine]
    m.d[5] = d5
    n = 0
    for _ in range(3000000):
        if m.pc == FULL:
            n += 1
        if m.step():
            break
    else:
        raise RuntimeError(routine + " did not return")
    refused[label] = n
    if TRACE:
        print("    %-28s top %3d  mark %3d  page top %3d  refused %d" % (
            label, m.rw(POOLTOP), m.rw(PACKMARK), m.rw(PAGETOP), n))
    return n


def names(page):
    """Ink cells per item row of a page buffer (14 x 9, rows 1/3/5/7)."""
    buf = 0xFFFF3600 + page * 0x100
    return [sum((m.rw(buf + r * 28 + c * 2) & 0x7FF) != BLANK for c in range(2, 13))
            for r in (1, 3, 5, 7)]


run("found / pack full", "loc_3DE0")
run("pages 1-4", "loc_3BEC")
run("pages 4-8", "loc_3C5C")
run("pages 8-10 + dropped item", "loc_3C9E")
check("opening the list refuses no cell",
      not (refused["pages 1-4"] or refused["pages 4-8"] or refused["pages 8-10 + dropped item"]),
      "%r" % refused)
open_top = m.rw(POOLTOP)
check("the open list leaves the pool well below its cap",
      open_top <= SLOTS - 24, "top %d of %d" % (open_top, SLOTS))
check("page one is composed", all(names(0)), "%r" % names(0))
check("the other nine pages hold no tiles",
      all(not any(names(p)) for p in range(1, 10)))

page_tops = []
for page in range(1, 10):
    run("page right", "loc_3B04")
    page_tops.append(m.rw(POOLTOP))
    if refused["page right"]:
        break
check("paging right through all ten pages refuses no cell", not refused["page right"])
check("the last page is composed", all(names(9)), "%r" % names(9))
check("the page left behind is blanked", not any(names(8)))
# A page is at most four 11-cell names: anything more is a leak across turns
check("every page turn rewinds to the list's mark",
      max(page_tops) <= m.rw(PACKMARK) + 44, "tops %r, mark %d" % (page_tops, m.rw(PACKMARK)))
for page in range(9):
    run("page left", "loc_3B2A")
for page in range(8):
    run("page right", "loc_3B04")
check("paging back and forth again does not climb",
      m.rw(POOLTOP) <= max(page_tops), "top %d" % m.rw(POOLTOP))
run("page right", "loc_3B04")
run("page left", "loc_3B2A")
check("paging left refuses no cell", not refused["page left"])
check("the page paged back to is composed", all(names(8)), "%r" % names(8))

ww(m, symbols["Battle_Item_Index"], 0x21)    # page nine, second row
run("want to discard", "loc_3914")
run("yes/no", "loc_3882")
check("'Want to discard?' composes in full", not refused["want to discard"])
check("its Yes/No composes in full", not refused["yes/no"])
prompt_top = m.rw(POOLTOP)
for index in (0x22, 0x23, 0x20, 0x21):       # No, then prompt for another item
    run("back to the list", "VWFMenu_PackBackToList")
    ww(m, symbols["Battle_Item_Index"], index)
    run("want to discard", "loc_3914")
    run("yes/no", "loc_3882")
check("repeated prompts refuse no cell", not refused["want to discard"] and not refused["yes/no"])
check("repeated prompts do not climb", m.rw(POOLTOP) <= prompt_top + 12,
      "top %d, first prompt %d" % (m.rw(POOLTOP), prompt_top))
run("discarded / received", "loc_35F6")
check("'discarded.' / 'received!' compose in full", not refused["discarded / received"],
      "top %d" % m.rw(POOLTOP))

print("ALL PASS" if ok else "FAILURES ABOVE")
sys.exit(0 if ok else 1)
