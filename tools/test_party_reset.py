"""Verify mode-transition reset and party-name substitution/VWF rendering."""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import menuharness as H


sym = H.Symbols()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "work", "fixtures", "loctest1-status.exs")
BASE = 0x5400                    # offset inside the savestate's 64K RAM image


def const_offset(name):
    src = open(H.CONSTANTS, encoding="utf-8", errors="replace").read()
    m = re.search(r"^" + re.escape(name) +
                  r"\s*=\s*VWF_RAM_Base\+\$([0-9A-Fa-f]+)", src, re.M)
    assert m, name
    return int(m.group(1), 16)


FIELDS = [("PoolTop", "VWFMenu_PoolTop", 2),
          ("SaveTop", "VWFMenu_SaveTop", 2),
          ("BattleBase", "VWFMenu_BattleBase", 2),
          ("BattleActionMark", "VWFMenu_BattleActionMark", 2),
          ("BattleEnemyMark", "VWFMenu_BattleEnemyMark", 2),
          ("BattleResultMark", "VWFMenu_BattleResultMark", 2),
          ("BattleResultActive", "VWFMenu_BattleResultActive", 1),
          ("Mark", "VWFMenu_Mark_Cur", 2),
          ("WrapFlag", "VWFMenu_WrapFlag", 1),
          ("StripReuse", "VWFMenu_StripReuseOK", 1),
          ("FieldReuseDepth", "VWFMenu_FieldReuseDepth", 1),
          ("FieldReuseBlocked", "VWFMenu_FieldReuseBlocked", 1),
          ("ReclaimInhibit", "VWFMenu_ReclaimInhibit", 1)]


def carry(machine, state):
    state["ram"] = bytearray(machine.m[0xFF0000:0x1000000])
    state["vram"] = bytes(machine.vram)


def text_at(buf, off, terminator=0xFE):
    out = ""
    while buf[off] < terminator:
        out += H.CHAR.get(buf[off], "?")
        off += 1
    return out


ok = True
st = H.load_state(STATE)
st["ram"] = bytearray(st["ram"])

# Poison every state field.  A mode transition must forget all of it because
# battle/map loaders rebuild the reclaimed VRAM underneath those records.
for _, name, size in FIELDS:
    at = BASE + const_offset(name)
    st["ram"][at:at + size] = b"\xA5" * size
m, steps = H.call(st, "VWFMenu_Reset", sym)
carry(m, st)
for label, name, size in FIELDS:
    at = BASE + const_offset(name)
    value = bytes(st["ram"][at:at + size])
    good = value == b"\0" * size
    ok &= good
    print("  %s reset %-10s %s" % ("ok  " if good else "FAIL", label,
                                     value.hex()))
# Battle reads A-H (MACRO) and the vehicle HUD label straight from the $7C0
# font copy, which the field pool composes into; Reset restores the letters.
alpha = open("ps4disasm/vwf/menualpha.bin", "rb").read()
good = len(alpha) == 26 * 32 and bytes(m.vram[0xF800:0xF800 + len(alpha)]) == alpha
ok &= good
print("  %s reset restores the stock A-Z at $7C0 (%d VRAM writes)" %
      ("ok  " if good else "FAIL", len(m.vram_writes)))
magic_at = BASE + const_offset("VWFMenu_LayoutMagic")
magic = bytes(st["ram"][magic_at:magic_at + 4])
good = magic == b"VWF5"          # the 146-slot layout with its RAM tails
ok &= good
print("  %s reset compact save layout %s" %
      ("ok  " if good else "FAIL", magic.hex()))

# This US savestate really contains Alys in party slot 1.  DrawString must not
# render those stale RAM bytes: it maps the record index to translated
# CharNameData and composes it through the standard menu VWF.
party = 0xF500 + 0x80
old = text_at(st["ram"], party)
plane = sym["Plane_A_Buffer"]
for i in range(0x80):
    st["ram"][(plane & 0xFFFF) + i] = 0
m, steps = H.call(st, "VWFMenu_DrawString", sym,
                  a0=0xFFFF0000 + party, a1=plane, d2=0xE680)

char_names = sym["CharNameData"]
rom = open(H.ROM, "rb").read()
expected_end = char_names
for _ in range(2):
    while rom[expected_end] < 0xFE:
        expected_end += 1
    if _ == 0:
        expected_end += 1
cells = (m.a[1] - plane) // 2
checks = [("savestate source is the US name", old == "Alys", old),
          ("source changed to translated Laila", m.a[0] == expected_end,
           "$%06X" % m.a[0]),
          ("Laila VWF occupies three cells", cells == 3, "%d cells" % cells)]
for label, good, detail in checks:
    ok &= good
    print("  %s %-40s %s" % ("ok  " if good else "FAIL", label, detail))

# The weapon-shop state caught a subtler failure: item strips had reused pool
# slots whose old compositor keys still spelled party names.  A later Laila /
# Rudy / Hahn draw hit those stale keys and displayed fragments of DAGGER and
# HUNTER KNIFE.  Every party tile returned from that exact state must now be a
# compositor-owned slots ($FFFE), never item/Technique/Skill strip slots.
from buildflags import strips_built, skipped
shop_path = os.path.join(ROOT, "work", "fixtures", "ps4en-weaponshop.exs")
if os.path.exists(shop_path) and not strips_built(sym.text):
    skipped("weapon-shop party tiles are composer-owned slots",
            "no strip slots exist in the composed-name build")
elif os.path.exists(shop_path):
    shop = H.load_state(shop_path)
    shop["ram"] = bytearray(shop["ram"])
    tile_slot = open("ps4disasm/vwf/pooltile.bin", "rb").read()
    strip_base = BASE + const_offset("VWFMenu_StripOf")
    for cid, label in ((1, "Laila"), (0, "Rudy"), (2, "Hahn")):
        for i in range(0x80):
            shop["ram"][(plane & 0xFFFF) + i] = 0
        source = 0xF500 + cid * 0x80
        m, steps = H.call(shop, "VWFMenu_DrawString", sym,
                          a0=0xFFFF0000 + source, a1=plane, d2=0xE680)
        cells = (m.a[1] - plane) // 2
        owners = []
        for i in range(cells):
            tile = m.rw(plane + i * 2) & 0x7FF
            off = tile - 0x680
            slot = tile_slot[off] if 0 <= off < len(tile_slot) else 0xFF
            owners.append(m.rw(0xFF0000 + strip_base + slot * 2)
                          if slot != 0xFF else -1)
        good = bool(owners) and all(v == 0xFFFE for v in owners)
        ok &= good
        print("  %s weapon-shop %-28s %s" %
              ("ok  " if good else "FAIL", label,
               " ".join("$%04X" % (v & 0xFFFF) for v in owners)))
        carry(m, shop)

print("ALL PASS" if ok else "FAILURES ABOVE")
sys.exit(0 if ok else 1)
