"""The creep face, set proportionally.

Not a new typeface - the actual party-name glyphs, taken apart. `creepfont`
stores creep as PAIRS baked into 8x8 cells at fixed x=0 and x=4, so every
individual letterform is already there; it just has to be split out. Doing that
recovers 22 letters (F H L P R S T a d e h i j k l m n o r s u y) and, checked
across every pair that contains them, **no letter disagrees with itself** - the
split is lossless.

Those 22 cover every letter the eleven current party names use.

Creep keeps its own metrics, which are not the rest of the VWF face's: baseline
row 6, one above the small-caps baseline, which is what buys the real
descenders on y, g and j. That descender is the point - it is why Pyke does not
read as Puke.

Tracking is ZERO, not one pixel. Creep letters span all four columns of their
slot with no side bearings, so the typeface's own spacing is already in the
glyph; adding a gap would set it looser than the fixed pairs it replaces.
`creepfont` warns that trimming bearings made n read as r, and this is the same
fact from the other side.

What proportional setting buys, honestly:

* nothing in cells for the current names - creep at 4 px packed two per cell is
  already as dense as a 4 px face gets, and the narrow letters (T i j l) do not
  save enough to cross a cell boundary
* freedom from the pairing constraint: a name no longer has to decompose into
  pairs that exist as glyphs, so any name works from the 22 letters
* 25 codes back, since the pair glyphs are no longer needed
"""
import creepfont
import slotmap
import os

BASELINE = 6            # creep's own, one above the small-caps baseline
TRACK = 0               # creep has no side bearings; its spacing is in the glyph


def _split():
    """Individual letterforms, recovered from the pair glyphs."""
    out = {}
    for key in slotmap.PARTY:
        g = creepfont.GLYPHS.get(key)
        if g is None:
            continue
        parts = [(key[0], [r[0:4] for r in g])]
        if len(key) == 2:
            parts.append((key[1], [r[4:8] for r in g]))
        for ch, rows in parts:
            prev = out.get(ch)
            if prev is not None and prev != rows:
                raise ValueError(f'{ch!r} differs between pair glyphs')
            out[ch] = rows
    return out


LETTERS = _split()


def advance(ch):
    """Ink width. Trailing blank columns only - the left bearing is kept, so a
    glyph never shifts relative to how creep drew it."""
    hi = -1
    for r in LETTERS[ch]:
        for i, c in enumerate(r):
            if c == '1':
                hi = max(hi, i)
    return hi + 1


def width(text):
    return sum(advance(c) for c in text) + TRACK * max(0, len(text) - 1)


def cells(text):
    return max(1, -(-width(text) // 8))


def bitmap(text):
    """8 rows of pixels, creep's own vertical metrics preserved."""
    w = width(text)
    g = [[0] * max(1, w) for _ in range(8)]
    x = 0
    for ch in text:
        for y, r in enumerate(LETTERS[ch]):
            for dx, c in enumerate(r):
                if c == '1' and x + dx < w:
                    g[y][x + dx] = 1
        x += advance(ch) + TRACK
    return g


def missing(words):
    return sorted({c for w in words for c in w if c not in LETTERS and c != ' '})


def font_assets():
    """Build a menu-charset creep face for party names only."""
    code = {}
    for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        code[c] = 1 + i
    for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"):
        code[c] = 57 + i

    font = bytearray(128 * 8)
    widths = bytearray(128)
    for ch, rows in LETTERS.items():
        c = code[ch]
        widths[c] = advance(ch)
        for y, row in enumerate(rows):
            b = 0
            for x, pixel in enumerate(row):
                if pixel == '1':
                    b |= 0x80 >> x
            font[c * 8 + y] = b
    return bytes(font), bytes(widths)


def main():
    out = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                       "ps4disasm", "vwf")
    os.makedirs(out, exist_ok=True)
    font, widths = font_assets()
    open(os.path.join(out, "partyfont.bin"), "wb").write(font)
    open(os.path.join(out, "partywidth.bin"), "wb").write(widths)
    print("partyfont.bin  %d bytes" % len(font))
    print("partywidth.bin %d bytes" % len(widths))


if __name__ == '__main__':
    main()
