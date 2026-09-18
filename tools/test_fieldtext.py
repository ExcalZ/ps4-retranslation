"""Verify full field-message names and the restored slow fixed renderer."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fieldstrings as F
import menuharness as H


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "work", "fixtures", "ps4en-fieldtech.exs")
ROM = os.environ.get("PS4_ROM", os.path.join(ROOT, "ps4disasm", "ps4built.bin"))  # paired with PS4_LST via menuharness
VWF = os.path.join(ROOT, "ps4disasm", "vwf")


def split(blob):
    return [bytes(row) for row in blob.split(b"\xFE")[:-1]]


rev = {v: k for k, v in F.CODE.items()}


def decode(raw):
    return "".join(rev[c] for c in raw)


ok = True
sym = H.Symbols()
rom = open(ROM, "rb").read()
tech_blob = open(os.path.join(VWF, "fieldtechnames.bin"), "rb").read()
item_blob = open(os.path.join(VWF, "fielditemnames.bin"), "rb").read()
skill_blob = open(os.path.join(VWF, "fieldskillnames.bin"), "rb").read()
tech = list(map(decode, split(tech_blob)))
items = list(map(decode, split(item_blob)))


def check(label, good, detail=""):
    global ok
    ok &= good
    print("  %s %-47s %s" % ("ok  " if good else "FAIL", label, detail))


check("Resta keeps its complete translated name", tech[23] == "Resta", tech[23])
check("longest recovery Tech keeps its complete name",
      tech[28] == "Rasaresta", tech[28])
# Slot 38 was Rückkehr, the one name in any table carrying a diacritic, and
# this line existed to prove the field encoder round-tripped it. Adopting
# Sega's own transliterations renamed it to Ryuker and left no non-ASCII name
# anywhere, so that coverage is gone rather than passing: if a diacritic name
# is ever reintroduced, neither this path nor menustrip's SYNTH overlay has a
# test behind it any more. The positional round trip is still worth asserting.
check("last Tech slot round-trips through field encoding",
      tech[38] == "Ryuker", tech[38])
check("item table preserves all 160 ordinals", len(items) == 160, str(len(items)))
check("Tech table preserves all 40 ordinals", len(tech) == 40, str(len(tech)))
check("Skill table preserves all 54 ordinals", len(split(skill_blob)) == 54, str(len(split(skill_blob))))
check("assembled ROM contains the generated Skill table",
      rom[sym["VWFField_SkillNames"]:sym["VWFField_SkillNames"] + len(skill_blob)] == skill_blob,
      "$%06X" % sym["VWFField_SkillNames"])
check("assembled ROM contains the generated item table",
      rom[sym["VWFField_ItemNames"]:sym["VWFField_ItemNames"] + len(item_blob)] == item_blob,
      "$%06X" % sym["VWFField_ItemNames"])
check("assembled ROM contains the generated Tech table",
      rom[sym["VWFField_TechNames"]:sym["VWFField_TechNames"] + len(tech_blob)] == tech_blob,
      "$%06X" % sym["VWFField_TechNames"])

# Both presentations of the dynamic "<Tech/Skill> is used!" sentence are
# assembled in RAM.  They therefore need the forced wrapper: source-address
# range dispatch cannot recognize RAM as chrome, even when d4 selects the
# immediate renderer after the effect has been applied.  The Tech-side range
# also contains the RAM-built DYING-target warning added immediately before
# loc_61AD4, so it has one additional forced draw.
forced = bytes.fromhex("4EB9") + sym["VWFField_LoadWindowTiles"].to_bytes(4, "big")
tech_action = rom[sym["loc_60B32"]:sym["loc_61AD4"]]
skill_action = rom[sym["loc_61AD4"]:sym["loc_62028"]]
check("Tech usage and DYING-target sentences use the forced VWF renderer",
      tech_action.count(forced) == 3,
      "%d forced draws" % tech_action.count(forced))
check("Skill usage sentence is VWF before and after its effect",
      skill_action.count(forced) == 2,
      "%d forced draws" % skill_action.count(forced))

# With composed chrome there must be no alphabet-bearing slow fallback: those
# glyphs occupy the duplicate $7C0 bank that the expanded pool now reclaims.
# The assembled d4==0 leg therefore branches directly to the same atomic run
# composer as immediate mode.  Keep this check on machine code so a future
# source refactor cannot silently make the reclaimed tiles live again.
draw = sym["VWFMenu_DrawWindowRun"]
slow = rom[draw:draw + 8]
check("slow renderer routes alphabet through the atomic VWF composer",
      slow[:6] == bytes.fromhex("4A44 6616 6014"), slow.hex(" ").upper())

print("ALL PASS" if ok else "FAILURES ABOVE")
sys.exit(0 if ok else 1)
