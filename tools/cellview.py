"""Render name tables in the real menu VWF, on the cell grid, as a PNG.

The proofreader draws this live for one row at a time; this is the same picture
for a whole table at once, which is what you want when checking a set of names
reads consistently rather than checking one name fits.

Vertical rules are 8-pixel cell boundaries. The heavier rule is the segment's
cell limit -- anything reaching past it would be clipped in game.

    python tools/cellview.py 02:001 02:002 -o work/cells.png
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import png
from menustrip import compose

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIMITS = {'00:001': 10, '00:002': 7, '00:003': 8, '00:004': 10,
          '02:001': 10, '02:002': 10}

SCALE = 3
CELLS = 13                 # drawn width, a little past the widest limit
ROW_H = 11                 # 8px glyph + breathing room
GUTTER = 26                # room for the index label
COL_W = GUTTER + CELLS * 8 + 6

PAPER, RULE, LIMIT_RULE, INK, OVER = 240, 214, 150, 24, 190


def digits(n):
    """Tiny 3x5 numerals, so a row can be found by index without a font."""
    F = {'0': "111101101101111", '1': "010110010010111", '2': "111001111100111",
         '3': "111001111001111", '4': "101101111001001", '5': "111100111001111",
         '6': "111100111101111", '7': "111001001010010", '8': "111101111101111",
         '9': "111101111001111"}
    out = []
    for ch in '%03d' % n:
        out.append(F[ch])
    return out


def render(segments, out_path):
    d = json.load(open(os.path.join(ROOT, 'work', 'script_translated.json'),
                       encoding='utf-8'))
    es = d['entries'] if isinstance(d, dict) else d

    blocks = []
    for seg in segments:
        rows = [e for e in es
                if (e.get('segment') or '') == seg and (e.get('en') or '').strip()]
        blocks.append((seg, rows))

    total = sum(len(r) for _, r in blocks) + 2 * len(blocks)
    cols = 4
    per_col = (total + cols - 1) // cols
    W = cols * COL_W
    H = per_col * ROW_H + 4
    img = [bytearray([PAPER] * W) for _ in range(H)]

    def put(x, y, v):
        if 0 <= x < W and 0 <= y < H:
            img[y][x] = v

    col = row = 0

    def advance():
        nonlocal col, row
        row += 1
        if row >= per_col:
            row, col = 0, col + 1

    for seg, rows in blocks:
        limit = LIMITS.get(seg, 10)
        # a separator band naming the segment by its limit marker alone
        for i in range(2):
            y = row * ROW_H + 2 + i
            for x in range(col * COL_W + GUTTER, col * COL_W + GUTTER + CELLS * 8):
                put(x, y, INK)
            advance()
        for n, e in enumerate(rows):
            ox = col * COL_W + GUTTER
            oy = row * ROW_H + 2
            cells, span = compose(e['en'])
            for c in range(CELLS + 1):
                shade = LIMIT_RULE if c == limit else RULE
                for y in range(8):
                    put(ox + c * 8, oy + y, shade)
            if cells > limit:
                for y in range(8):
                    for x in range(ox + limit * 8, ox + CELLS * 8):
                        if img[oy + y][x] == PAPER:
                            put(ox + limit * 8 + (x - ox - limit * 8), oy + y, OVER)
            for y in range(8):
                for xb in range(16):
                    b = span[y * 16 + xb]
                    for bit in range(8):
                        if b & (0x80 >> bit):
                            put(ox + xb * 8 + bit, oy + y, INK)
            for k, glyph in enumerate(digits(n)):
                for gy in range(5):
                    for gx in range(3):
                        if glyph[gy * 3 + gx] == '1':
                            put(col * COL_W + 2 + k * 4 + gx, oy + 2 + gy, RULE)
            advance()

    big = []
    for r in img:
        rr = bytearray()
        for v in r:
            rr += bytes([v]) * SCALE
        for _ in range(SCALE):
            big.append(rr)
    png.write_gray(out_path, big, W * SCALE, len(big))
    return sum(len(r) for _, r in blocks), out_path


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    out = 'work/cells.png'
    if '-o' in sys.argv:
        out = sys.argv[sys.argv.index('-o') + 1]
        args = [a for a in args if a != out]
    n, path = render(args or ['02:001', '02:002'], out)
    print('rendered %d names to %s' % (n, path))


if __name__ == '__main__':
    main()
