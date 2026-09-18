"""Count live window-text cells in an Exodus savestate.

The pool for a menu VWF has to be at least as large as the number of text
cells visible at once.  Rather than infer that from window geometry - which
is how the Japanese attempt went wrong - read it straight out of VRAM.

Plane A's nametable is at VRAM $C000 (VDP reg 2 = $30), Plane B at $E000
(reg 4 = $07), both 64x32 entries of one word.  A word's low 11 bits are the
tile index; the window font occupies $681-$6D7, and $680 is the space.

usage: python tools/menucount.py <savestate.exs> [...]
"""
import sys, zipfile

FONT_LO, FONT_HI = 0x681, 0x6D7
SPACE            = 0x680
FRAME_LO, FRAME_HI = 0x6D8, 0x6FF

def vram_from(path):
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            if n.endswith("VRAM.bin"):
                return z.read(n)
    raise SystemExit("%s: no VRAM.bin inside" % path)

def plane(v, base):
    cells = []
    for i in range(64 * 32):
        w = (v[base + i*2] << 8) | v[base + i*2 + 1]
        cells.append((i % 64, i // 64, w & 0x7FF))
    return cells

for path in sys.argv[1:]:
    v = vram_from(path)
    print("=== %s  (VRAM %d bytes) ===" % (path, len(v)))
    for name, base in (("Plane A", 0xC000), ("Plane B", 0xE000)):
        cells = plane(v, base)
        text  = [c for c in cells if FONT_LO <= c[2] <= FONT_HI]
        space = [c for c in cells if c[2] == SPACE]
        frame = [c for c in cells if FRAME_LO <= c[2] <= FRAME_HI]
        print("  %-8s text cells %4d   space %4d   frame %4d" %
              (name, len(text), len(space), len(frame)))
        if text:
            rows = {}
            for x, y, t in text: rows.setdefault(y, []).append(x)
            print("           rows used: %d   widest run: %d cells" %
                  (len(rows), max(len(v2) for v2 in rows.values())))
            ys = sorted(rows)
            print("           row span y=%d..%d" % (ys[0], ys[-1]))
