"""Pack the label glyphs that stay fixed-width into the bottom of the bank.

Numbers are not here: HP/TP, levels and stat values are drawn from the
second font copy at $7C0, which this does not touch.  What remains in the
$680 bank as fixed-width is the static UI chrome, which keeps the shipped
artwork so labels look exactly as they did.

Emits, into ps4disasm/vwf/:
    menufixed.bin  the packed 4bpp tiles, stock art, in slot order
    menufixmap.bin 128 bytes, charset code -> slot, $FF if not a fixed glyph
    menualpha.bin  the stock A-Z, 26 tiles in order: what the $7C0 font copy
                   holds at $7C0-$7D9.  The field pool composes into those
                   tiles (slots 88..113) and the bank is loaded only at the
                   title screen, but battle still reads letters from it
                   (MACRO's A-H, the vehicle HUD label), so VWFMenu_Reset
                   puts the stock letters back on every battle entry.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decomp

SLOTS = 26          # reserved at $681-$69A; 22 used, 4 spare for unsampled labels
OUT = "ps4disasm/vwf"

LABELS = ["STRNGTH:", "MENTAL :", "AGILITY:", "LV  :", "HP", "TP", "MST",
          "SKILL BTL", "SKILL CAMP", "TECH BTL", "TECH CAMP",
          "TECH", "SKILL", "EQUIP", "STATE", "WHO"]

code = {' ': 0}
for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"): code[c] = 1 + i
for i, c in enumerate("0123456789"):                 code[c] = 27 + i
for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"): code[c] = 57 + i
code[':'] = 0x34; code['-'] = 0x31; code['.'] = 0x53

need = sorted({code[c] for lab in LABELS for c in lab if c != ' '})
if len(need) > SLOTS:
    raise SystemExit("%d label glyphs need packing but only %d slots" % (len(need), SLOTS))

art = decomp.decompress(open("ps4disasm/general/art/nemesis/Font.bin", "rb").read() + bytes(32), 0)

tiles = bytearray()
fixmap = bytearray([0xFF] * 128)
for slot, c in enumerate(need):
    blob = c - 1                       # Font.bin loads at tile $681, codes start at $680
    tiles += art[blob*32:(blob+1)*32]
    fixmap[c] = slot
tiles += bytes(32 * (SLOTS - len(need)))   # pad the spare slots blank

os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "menufixed.bin"), "wb").write(tiles)
open(os.path.join(OUT, "menualpha.bin"), "wb").write(art[:26 * 32])
open(os.path.join(OUT, "menufixmap.bin"), "wb").write(fixmap)
inv = {v: k for k, v in code.items()}
print("label glyphs packed: %d of %d slots" % (len(need), SLOTS))
print("   %s" % " ".join(inv.get(c, "$%02X" % c) for c in need))
print("menufixed.bin  %d bytes (%d tiles)" % (len(tiles), len(tiles)//32))
print("menufixmap.bin %d bytes" % len(fixmap))
print("spare slots for labels not yet sampled: %d" % (SLOTS - len(need)))
