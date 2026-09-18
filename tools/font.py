"""Export / import for the two 16x16 dialogue fonts.

Both fonts store a glyph as 32 bytes: four 8x8 tiles, 1bpp, **row-major**
(TL TR BL BR), 8 bytes per tile, MSB = leftmost pixel. Reading a glyph as 16
rows of 2 bytes - the obvious interpretation of a 16x16 bitmap - produces
noise. That mistake has been made twice in this project; the layout is
asserted by font-check rather than trusted.

Addresses come from the glyph selector at $06A9FA:

    cmpi.b #$E0,d0        single byte or kanji?
    bcs $06AA1C           -> single byte
    lsl.w #8,d0 / move.b (a0)+,d0 / andi.w #$FFF,d0
    lsl.l #5,d1           index * 32
    lea ($1F62BA).l,a1    kanji font base
  $06AA1C:
    move.w d0,d1 / lsl.w #5,d1
    lea ($2A3452).l,a1    single-byte font base

The exported sheet is 1:1 - one image pixel per glyph pixel, 16 glyphs per
row, black on white. No grid lines or padding, so import is unambiguous. Zoom
in your editor rather than exporting scaled; use font-sheet for a readable
reference image.
"""
import os

GLYPH_BYTES = 32
COLS = 16                 # glyphs per row in an exported sheet

# name -> (base address, glyph count)
#   single byte: codes $00-$DF, 224 slots (>= $E0 is a kanji lead byte)
#   kanji: 12-bit index, 4096 possible but the table runs to $4DD
FONTS = {
    'kana':  (0x2A3452, 224),
    'kanji': (0x1F62BA, 1246),
}


def _glyph_to_bitmap(g):
    """32 bytes -> 16x16 list of 0/1. Tiles are row-major: TL TR BL BR."""
    p = [[0] * 16 for _ in range(16)]
    for t in range(4):
        ox, oy = (t % 2) * 8, (t // 2) * 8
        for y in range(8):
            b = g[t * 8 + y]
            for x in range(8):
                p[oy + y][ox + x] = (b >> (7 - x)) & 1
    return p


def _bitmap_to_glyph(p):
    """16x16 list of 0/1 -> 32 bytes, inverse of _glyph_to_bitmap."""
    out = bytearray(32)
    for t in range(4):
        ox, oy = (t % 2) * 8, (t // 2) * 8
        for y in range(8):
            b = 0
            for x in range(8):
                if p[oy + y][ox + x]:
                    b |= 1 << (7 - x)
            out[t * 8 + y] = b
    return bytes(out)


def sheet_size(n):
    rows = (n + COLS - 1) // COLS
    return COLS * 16, rows * 16


def export(rom, font, path):
    """Write the font as a 1:1 black-on-white sheet."""
    import png
    base, n = FONTS[font]
    w, h = sheet_size(n)
    img = [bytearray([255] * w) for _ in range(h)]
    for i in range(n):
        cx, cy = (i % COLS) * 16, (i // COLS) * 16
        p = _glyph_to_bitmap(rom[base + i * GLYPH_BYTES:][:GLYPH_BYTES])
        for y in range(16):
            for x in range(16):
                if p[y][x]:
                    img[cy + y][cx + x] = 0
    png.write_gray(path, [bytes(r) for r in img], w, h)
    return n, w, h


def load_sheet(path, font):
    """Read a sheet back into a list of 32-byte glyphs."""
    import pngread
    base, n = FONTS[font]
    ew, eh = sheet_size(n)
    w, h, px = pngread.read(path)
    if (w, h) != (ew, eh):
        raise ValueError(f'{path}: expected {ew}x{eh} for font {font!r}, '
                         f'got {w}x{h}. The sheet must be 1:1 and uncropped.')
    glyphs = []
    for i in range(n):
        cx, cy = (i % COLS) * 16, (i // COLS) * 16
        p = [[0] * 16 for _ in range(16)]
        for y in range(16):
            for x in range(16):
                r, g, b = px[cy + y][cx + x][:3]
                # luminance threshold: anything darker than mid-grey is ON
                p[y][x] = 1 if (r * 299 + g * 587 + b * 114) // 1000 < 128 else 0
        glyphs.append(_bitmap_to_glyph(p))
    return glyphs


def import_(rom, font, path):
    """Write an edited sheet back into the ROM. Returns (rom, changed)."""
    base, n = FONTS[font]
    glyphs = load_sheet(path, font)
    out = bytearray(rom)
    changed = 0
    for i, g in enumerate(glyphs):
        off = base + i * GLYPH_BYTES
        if out[off:off + GLYPH_BYTES] != g:
            out[off:off + GLYPH_BYTES] = g
            changed += 1
    return bytes(out), changed


def check(rom, font):
    """Export -> import must reproduce every glyph byte for byte."""
    base, n = FONTS[font]
    bad = []
    for i in range(n):
        g = rom[base + i * GLYPH_BYTES:][:GLYPH_BYTES]
        if _bitmap_to_glyph(_glyph_to_bitmap(g)) != g:
            bad.append(i)
    return n, bad


def sheet(rom, font, path, scale=3, gap=1):
    """A readable reference image: scaled, with grid lines. NOT importable."""
    import png
    base, n = FONTS[font]
    cell = 16 * scale + gap
    rows = (n + COLS - 1) // COLS
    w, h = COLS * cell + gap, rows * cell + gap
    img = [bytearray([170] * w) for _ in range(h)]      # grey grid
    for i in range(n):
        cx, cy = (i % COLS) * cell + gap, (i // COLS) * cell + gap
        p = _glyph_to_bitmap(rom[base + i * GLYPH_BYTES:][:GLYPH_BYTES])
        for y in range(16 * scale):
            for x in range(16 * scale):
                img[cy + y][cx + x] = 0 if p[y // scale][x // scale] else 255
    png.write_gray(path, [bytes(r) for r in img], w, h)
    return n, w, h
