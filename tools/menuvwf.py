"""Generate the menu VWF face: proportional mixed case (vwfmixed).

One alphabet, one baseline: capitals on rows 0-6, lowercase with a 5-row
x-height on 2-6 and a 1-row descender, digits and marks at cap height.
Baseline row 6 is the stock 8x8 font's, so composed text sits level with
the fixed labels and stock lowercase.  The small caps + true capitals face
this replaced (vwffont.G under vwfcase.CAPS, bottoming on row 7) is still
in those modules for the legacy JP pipeline (vwfpatch) but is no longer
what the menus draw.

Emits, into ps4disasm/vwf/:
    menufont.bin   128 glyphs x 8 bytes, 1bpp, indexed by window charset code
    menuwidth.bin  128 bytes, advance in pixels

Codes follow general/tables/wincharset.asm, whose numbers are DECIMAL:
    space 0, A-Z 1-26, 0-9 27-36, a-z 57-82, plus punctuation in hex.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vwfmixed

GAP = 1
OUT = "ps4disasm/vwf"

code = {' ': 0}
for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"): code[c] = 1 + i
for i, c in enumerate("0123456789"):                 code[c] = 27 + i
for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"): code[c] = 57 + i
code['-'] = 0x31; code['!'] = 0x32; code['?'] = 0x33; code[':'] = 0x34
code['.'] = 0x53; code["'"] = 0x54; code[','] = 0x55
# $57 is unnamed by the stock charset and its last font tile is otherwise
# unused.  Give it to u-diaeresis so Rueckkehr can remain Rueckkehr's proper
# German spelling in dynamic field text as well as in prerendered strips.
code['ü'] = 0x57

def spec(ch):
    """(top row, rows, ink width) for one character, or None."""
    g = vwfmixed.G.get(ch)
    if g is None:
        return None
    top, rows = g
    return top, rows, max(len(r) for r in rows)

font  = bytearray(128 * 8)
width = bytearray(128)
# A word space, not a cell.  This table is read in exactly one place - the
# composer - and the strings that pad with spaces to position themselves
# (WinTiles_Meseta "        MST", "      LV", the button legends) are all
# chrome, which takes the fixed label path and never consults a width at all.
# Every composed source was checked for padding before this changed: the four
# name tables, the 160 item descriptions and every string reachable through
# ForceCompose carry single spaces only, no leading or trailing ones.
#
# At 8px the space was wider than every letter except M and W, against a 5.1px
# lowercase average, and multi-word names paid a whole cell for it: "Conduct
# Thunder" measured 81px in an 80px field on the strength of its one space.
#
# 3px, matching vwffont.SPACE in the dialogue face -- and matching what
# menustrip has always used for strips.  It has to be the SAME number: the
# strip generator's count is what trpatch8 previews in the JSON, so any
# difference means the width shown while editing a name is not the width the
# runtime composer gives it.  menustrip now reads this byte rather than
# carrying its own copy, so the two cannot drift.
width[0] = 3
placed, widest = 0, 0
for ch, c in sorted(code.items(), key=lambda kv: kv[1]):
    if c == 0: continue
    s = spec(ch)
    if s is None:
        print("  no glyph for %r (code $%02X)" % (ch, c)); continue
    top, rows, iw = s
    if iw > 8:
        raise SystemExit("glyph %r is %dpx wide - will not fit an 8px cell" % (ch, iw))
    for dy, r in enumerate(rows):
        b = 0
        for dx, p in enumerate(r):
            if p == '#': b |= 1 << (7 - dx)
        font[c * 8 + top + dy] = b
    width[c] = iw + GAP
    placed += 1; widest = max(widest, iw + GAP)

# --- fall back to the shipped glyph for every code the face does not cover ---
# Font.bin holds 87 glyphs at codes $01-$57: letters, digits, punctuation, and
# roughly eighteen symbols the charset never names - the slash, the equip
# arrows, and similar.  Those must still draw, at their original fixed width,
# or they vanish and take the layout with them.
import decomp
stock = decomp.decompress(open("ps4disasm/general/art/nemesis/Font.bin", "rb").read() + bytes(32), 0)
fallback = 0
for c in range(1, 0x58):
    if width[c]:
        continue                       # the proportional face already has it
    blob = c - 1                       # Font.bin loads at tile $681
    if (blob + 1) * 32 > len(stock):
        continue
    ink = False
    for y in range(8):
        b = 0
        for x in range(8):
            v = stock[blob*32 + y*4 + (x >> 1)]
            v = (v >> 4) if x % 2 == 0 else (v & 0xF)
            if v == 0xF:
                b |= 0x80 >> x
                ink = True
        font[c*8 + y] = b
    if ink:
        width[c] = 8                   # keep the shipped cell width
        fallback += 1
print("stock fallback glyphs: %d" % fallback)

os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "menufont.bin"), "wb").write(font)
open(os.path.join(OUT, "menuwidth.bin"), "wb").write(width)
print("menufont.bin  %d bytes  (%d glyphs placed)" % (len(font), placed))
print("menuwidth.bin %d bytes  widest advance %d px" % (len(width), widest))
low = sum(width[code[c]] for c in "abcdefghijklmnopqrstuvwxyz") / 26
cap = sum(width[code[c]] for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ") / 26
print("mean lowercase %.2f   mean capital %.2f   (fixed 8)" % (low, cap))
