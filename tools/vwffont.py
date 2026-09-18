"""Proportional small-caps face for the menu VWF.

Metrics match `lowerfont.SMALLCAP` exactly - five rows, top row 3, baseline
row 7 - so converted and unconverted text sit on the same line. What changes is
the ADVANCE: SMALLCAP is a near-uniform 6 px, which is why a VWF over it saves
only about 11%. Here each glyph is drawn at its natural width, 1 to 6 px, and
that is where the real saving comes from.

The narrow forms are NOT `lowerfont.NARROWCAP`. Those were authored for
ligature interiors, where a glyph shares a cell and legibility is carried by
the pair; at 1 px, standalone `i` is a stray dot. These are standalone shapes:
narrow where the letter is genuinely narrow, wide where it is not.

Widths are ink only. The renderer adds `GAP` between glyphs and does not pad
the trailing edge, so a run's pixel width is sum(ink) + GAP*(n-1).
"""

TOP = 3          # first pixel row, matching lowerfont.SMALLCAP
ROWS = 5
GAP = 1          # blank columns between adjacent glyphs
SPACE = 3        # advance for a space, in pixels

G = {}


def _g(ch, *rows):
    w = max(len(r) for r in rows)
    if len(rows) != ROWS:
        raise ValueError(f'{ch!r}: {len(rows)} rows, expected {ROWS}')
    G[ch] = tuple(r.ljust(w, '.') for r in rows)


_g('a', '.##.', '#..#', '####', '#..#', '#..#')
_g('b', '###.', '#..#', '###.', '#..#', '###.')
_g('c', '.###', '#...', '#...', '#...', '.###')
_g('d', '###.', '#..#', '#..#', '#..#', '###.')
_g('e', '####', '#...', '###.', '#...', '####')
_g('f', '####', '#...', '###.', '#...', '#...')
_g('g', '.###', '#...', '#.##', '#..#', '.###')
_g('h', '#..#', '#..#', '####', '#..#', '#..#')
_g('i', '#', '#', '#', '#', '#')
_g('j', '..#', '..#', '..#', '#.#', '.#.')
_g('k', '#..#', '#.#.', '##..', '#.#.', '#..#')
_g('l', '#..', '#..', '#..', '#..', '###')
_g('m', '#....#', '##..##', '#.##.#', '#....#', '#....#')
_g('n', '#...#', '##..#', '#.#.#', '#..##', '#...#')
_g('o', '.##.', '#..#', '#..#', '#..#', '.##.')
_g('p', '###.', '#..#', '###.', '#...', '#...')
_g('q', '.##.', '#..#', '#..#', '#.#.', '.#.#')
_g('r', '###.', '#..#', '###.', '#.#.', '#..#')
_g('s', '.###', '#...', '.##.', '...#', '###.')
_g('t', '###', '.#.', '.#.', '.#.', '.#.')
_g('u', '#..#', '#..#', '#..#', '#..#', '.##.')
_g('v', '#...#', '#...#', '#...#', '.#.#.', '..#..')
_g('w', '#....#', '#....#', '#.##.#', '##..##', '#....#')
_g('x', '#...#', '.#.#.', '..#..', '.#.#.', '#...#')
_g('y', '#...#', '.#.#.', '..#..', '..#..', '..#..')
_g('z', '####', '...#', '.##.', '#...', '####')
_g('ü', '#..#', '....', '#..#', '#..#', '.##.')

_g('0', '.##.', '#..#', '#..#', '#..#', '.##.')
_g('1', '.#.', '##.', '.#.', '.#.', '###')
_g('2', '###.', '...#', '.##.', '#...', '####')
_g('3', '###.', '...#', '.##.', '...#', '###.')
_g('4', '#..#', '#..#', '####', '...#', '...#')
_g('5', '####', '#...', '###.', '...#', '###.')
_g('6', '.###', '#...', '###.', '#..#', '.##.')
_g('7', '####', '...#', '..#.', '.#..', '#...')
_g('8', '.##.', '#..#', '.##.', '#..#', '.##.')
_g('9', '.##.', '#..#', '.###', '...#', '###.')

_g('.', '.', '.', '.', '.', '#')
_g(',', '.', '.', '.', '#', '#')
_g("'", '#', '#', '.', '.', '.')
_g('!', '#', '#', '#', '.', '#')
_g('?', '###', '..#', '.##', '...', '.#.')
_g('-', '...', '...', '###', '...', '...')
_g(':', '.', '#', '.', '#', '.')
_g('/', '...#', '...#', '.##.', '#...', '#...')
_g('(', '.#', '#.', '#.', '#.', '.#')
_g(')', '#.', '.#', '.#', '.#', '#.')


def ink(ch):
    """Advance width in pixels, excluding the inter-glyph gap."""
    if ch == ' ':
        return SPACE
    return len(G[ch.lower()][0])


def width(text):
    """Pixel width of a run: sum of inks plus one gap between neighbours."""
    if not text:
        return 0
    return sum(ink(c) for c in text) + GAP * (len(text) - 1)


def cells(text):
    """Nametable cells a run occupies."""
    return max(1, -(-width(text) // 8))


def bitmap(text):
    """Render `text` to a list of pixel rows (0/1), 8 rows tall."""
    w = width(text)
    grid = [[0] * w for _ in range(8)]
    x = 0
    for ch in text:
        if ch == ' ':
            x += SPACE + GAP
            continue
        rows = G[ch.lower()]
        for dy, r in enumerate(rows):
            for dx, p in enumerate(r):
                if p == '#':
                    grid[TOP + dy][x + dx] = 1
        x += len(rows[0]) + GAP
    return grid


def missing(texts):
    """Characters used by `texts` that this face cannot draw."""
    bad = set()
    for t in texts:
        for c in t:
            if c != ' ' and c.lower() not in G:
                bad.add(c)
    return sorted(bad)
