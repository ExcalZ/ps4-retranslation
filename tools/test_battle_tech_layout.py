"""Check the assembled battle-Tech window geometry and TP-cost column."""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import menuharness as H


symbols = H.Symbols()
rom = open(H.ROM, "rb").read()
listing = open(H.LST, encoding="utf-8", errors="replace").read()


def sym(name):
    m = re.search(r"/\s*([0-9A-F]{4,6}) :\s+" + re.escape(name) + r":",
                  listing)
    if not m:
        m = re.search(r"^\s*\d+/\s*([0-9A-F]{1,6}) :\s+"
                      + re.escape(name) + r":", listing, re.M)
    return int(m.group(1), 16) if m else symbols[name]

# Five separate paths create, copy, reveal, or erase this window.  Missing one
# gives a menu that looks correct until paging or backing out of it.
sites = [("active window", "loc_18DA", 4),
         ("setup", "loc_18F2", 0),
         ("setup copy-out", "loc_18F2", 0x3C),
         ("next page", "Battle_TechNextWin", 4),
         ("previous page", "loc_E8C", 4),
         ("cleanup", "loc_1BC6", 0x14)]
ok = True
for label, name, off in sites:
    at = sym(name) + off
    word = int.from_bytes(rom[at:at + 2], "big")
    good = word == 0x720E             # moveq #14,d1
    ok &= good
    print("  %s %-16s $%06X: %04X" %
          ("ok  " if good else "FAIL", label, at, word))

# The cost begins 14 bytes (seven nametable cells) after the name.  The widened
# window is 14 cells; these are deliberately different units.
at = sym("loc_193C") + (0x19A6 - 0x1958)
word = int.from_bytes(rom[at:at + 2], "big")
ext = int.from_bytes(rom[at + 2:at + 4], "big")
good = (word, ext) == (0x43E9, 0x000E)  # lea $E(a1),a1
ok &= good
print("  %s %-16s $%06X: %04X %04X" %
      ("ok  " if good else "FAIL", "TP cost column", at, word, ext))

# Private page buffers own their strip tiles only until the submenu closes.
# Each final exit must restore the command-level pool baseline; page-to-page
# transitions deliberately do not, because their raw tile IDs remain reachable.
_C = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "ps4disasm", "ps4.constants.asm"),
          encoding="utf-8", errors="replace").read()
def _vwf(name):
    """Absolute address read from the constants.  These fields move whenever
    VWFMENU_SLOTS changes, so the instruction bytes cannot be spelled out."""
    m = re.search(r"^" + re.escape(name) + r"\s*=\s*VWF_RAM_Base\+\$([0-9A-Fa-f]+)",
                  _C, re.M)
    assert m, name
    return 0xFFFF5400 + int(m.group(1), 16)
rollback = (bytes.fromhex("33F9") + _vwf("VWFMenu_BattleBase").to_bytes(4, "big")
            + _vwf("VWFMenu_PoolTop").to_bytes(4, "big"))
release_spans = [
    ("Tech selected", "Battle_TechSelected", "loc_1BC6"),
    ("Tech cancelled", "Battle_BackFromTechs", "Battle_OpenSkills"),
    ("Skill selected", "Battle_SkillSelected", "loc_1F4E"),
    ("Skill cancelled", "Battle_BackFromSkills", "Battle_OpenItems"),
    ("Item selected", "Battle_ItemSelected", "loc_23CA"),
    ("Item cancelled", "Battle_BackFromItems", "Fighter_TakeDamage"),
]
for label, start, end in release_spans:
    body = rom[sym(start):sym(end)]
    good = body.count(rollback) == 1
    ok &= good
    print("  %s %-16s returns PoolTop to BattleBase" %
          ("ok  " if good else "FAIL", label))

print("ALL PASS" if ok else "FAILURES ABOVE")
sys.exit(0 if ok else 1)
