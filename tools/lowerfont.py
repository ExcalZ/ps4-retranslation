"""Lowercase and ligature glyphs for the 8x8 system font.

Metrics are fixed by the existing uppercase, which occupies rows 1-7 with the
baseline on row 7 (measured off 'A' at code $80). Lowercase sits with x-height
on rows 3-7 and ascenders from row 1. There is no room below row 7, so g j p q y
carry no descender - normal for an 8x8 face, and dropping the baseline to row 6
would misalign every mixed-case word against uppercase we are not redrawing.

Three things the first rendered mockup taught, all counter-intuitive:

1. STANDALONE LOWERCASE MUST BE WIDE, not narrow. The bank is fixed-pitch - one
   byte is one 8-pixel cell - so a 4px letter leaves a 4px hole after it and the
   word visibly falls apart ("Gi f e u er"). Filling the cell is what makes text
   read evenly, so the wide forms below run 5-6px against uppercase's 7px.
   Narrowing only ever happens inside a ligature, where two glyphs share a cell.

2. ONLY g SHIFTS UP. Three attempts at a descenderless g all read as a schwa:
   pinned to the row-7 baseline it cannot be told from a or q. It now sits on
   rows 2-6 with its tail on row 7. p q y were shifted too at first and it
   backfired - at that height their bodies read as CAPITALS ("SweePinɡ",
   "HolYword", "RudY"). They have nothing to be confused with, so they keep the
   row-7 baseline and simply go without descenders.

3. CAPITALISING BREAKS THE FIRST LIGATURE. "gifeuer" is gi|f|e|u|er = 5 cells,
   but "Gifeuer" is G|i|f|e|u|er = 6, over the technique limit. 15 of 39
   techniques break this way, so CAPS holds condensed uppercase forms for the
   five pairs that start a name: Gi, Li, Ra, Re, Sh.

The pixel budget comes from the original's own ligature $7B, which packs ォ into
columns 0-4 and ー into 6-7: seven columns of ink plus a one-column separator.
So ink(left) + ink(right) <= 7.
"""

WIDE = {}       # standalone forms, drawn to fill the cell
NARROW = {}     # condensed forms, used only inside a ligature
CAPS = {}       # condensed uppercase, used only as a ligature's left half


def _w(ch, top, *rows): WIDE[ch] = (top, rows)
def _n(ch, top, *rows): NARROW[ch] = (top, rows)
def _c(ch, top, *rows): CAPS[ch] = (top, rows)


# ------------------------------------------------------------ wide standalone
_w('a', 3, '.####.', '.....#', '.#####', '#....#', '.#####')
_w('b', 1, '#.....', '#.....', '#####.', '#....#', '#....#', '#....#', '#####.')
_w('c', 3, '.#####', '#.....', '#.....', '#.....', '.#####')
_w('d', 1, '.....#', '.....#', '.#####', '#....#', '#....#', '#....#', '.#####')
_w('e', 3, '.####.', '#....#', '######', '#.....', '.#####')
_w('f', 1, '..####', '.#....', '#####.', '.#....', '.#....', '.#....', '.#....')
_w('g', 2, '.####.', '#....#', '#....#', '#....#', '.#####', '####..')
_w('h', 1, '#.....', '#.....', '#####.', '#....#', '#....#', '#....#', '#....#')
_w('i', 1, '.#.', '...', '##.', '.#.', '.#.', '.#.', '###')
_w('j', 1, '...#.', '.....', '..##.', '...#.', '...#.', '...#.', '###..')
_w('k', 1, '#.....', '#.....', '#...#.', '#..#..', '###...', '#..#..', '#...#.')
_w('l', 1, '##.', '.#.', '.#.', '.#.', '.#.', '.#.', '###')
_w('m', 3, '##.##.', '#.#..#', '#.#..#', '#.#..#', '#.#..#')
_w('n', 3, '#####.', '#....#', '#....#', '#....#', '#....#')
_w('o', 3, '.####.', '#....#', '#....#', '#....#', '.####.')
_w('p', 3, '#####.', '#....#', '#####.', '#.....', '#.....')
_w('q', 3, '.#####', '#....#', '.#####', '.....#', '.....#')
_w('r', 3, '#.####', '##....', '#.....', '#.....', '#.....')
_w('s', 3, '.#####', '#.....', '.####.', '.....#', '#####.')
_w('t', 1, '.#....', '.#....', '#####.', '.#....', '.#....', '.#....', '..####')
_w('u', 3, '#....#', '#....#', '#....#', '#....#', '.#####')
_w('v', 3, '#....#', '#....#', '.#..#.', '.#..#.', '..##..')
_w('w', 3, '#....#', '#.##.#', '#.##.#', '##..##', '#....#')
_w('x', 3, '#....#', '.#..#.', '..##..', '.#..#.', '#....#')
_w('y', 3, '#....#', '#....#', '.#####', '.....#', '.####.')
_w('z', 3, '######', '....#.', '..##..', '.#....', '######')
_w('ü', 1, '#....#', '......', '#....#', '#....#', '#....#', '#....#', '.#####')

# ------------------------------------------------- narrow, ligature-interior
_n('a', 3, '##.', '.##', '#.#', '#.#', '.##')
_n('b', 1, '#..', '#..', '##.', '#.#', '#.#', '#.#', '##.')
_n('c', 3, '.##', '#..', '#..', '#..', '.##')
_n('d', 1, '..#', '..#', '.##', '#.#', '#.#', '#.#', '.##')
_n('e', 3, '.#.', '#.#', '###', '#..', '.##')
_n('f', 1, '.##', '#..', '###', '#..', '#..', '#..', '#..')
_n('g', 2, '.##', '#.#', '#.#', '.##', '..#', '##.')
_n('v', 3, '#.#', '#.#', '#.#', '#.#', '.#.')
_n('h', 1, '#..', '#..', '##.', '#.#', '#.#', '#.#', '#.#')
_n('i', 1, '#', '.', '#', '#', '#', '#', '#')
_n('j', 1, '.#', '..', '.#', '.#', '.#', '.#', '##')
_n('k', 1, '#..', '#..', '#.#', '##.', '##.', '#.#', '#.#')
_n('l', 1, '#', '#', '#', '#', '#', '#', '#')
_n('n', 3, '##.', '#.#', '#.#', '#.#', '#.#')
_n('o', 3, '.#.', '#.#', '#.#', '#.#', '.#.')
_n('p', 3, '##.', '#.#', '##.', '#..', '#..')
_n('r', 3, '#.#', '##.', '#..', '#..', '#..')
_n('s', 3, '.##', '#..', '.#.', '..#', '##.')
_n('t', 1, '.#.', '.#.', '###', '.#.', '.#.', '.#.', '..#')


# Completing NARROW to all 26 so it can double as a TIGHT standalone set: a name
# that needs ligatures can be drawn entirely in condensed forms, so its single
# letters match the density of its merged cells instead of towering over them.
_n('m', 3, '##.#.', '#.#.#', '#.#.#', '#.#.#', '#.#.#')
_n('q', 3, '.##', '#.#', '.##', '..#', '..#')
_n('u', 3, '#.#', '#.#', '#.#', '#.#', '.##')
_n('w', 3, '#...#', '#.#.#', '#.#.#', '##.##', '#...#')
_n('x', 3, '#.#', '#.#', '.#.', '#.#', '#.#')
_n('y', 3, '#.#', '#.#', '.##', '..#', '##.')
_n('z', 3, '###', '..#', '.#.', '#..', '###')
_n('ü', 1, '#.#', '...', '#.#', '#.#', '#.#', '#.#', '.##')

# ------------------------------ condensed uppercase, ligature left half only
_c('G', 1, '.##.', '#..#', '#...', '#.##', '#..#', '#..#', '.##.')
_c('L', 1, '#...', '#...', '#...', '#...', '#...', '#...', '####')
_c('R', 1, '###.', '#..#', '#..#', '###.', '#.#.', '#..#', '#..#')
_c('S', 1, '.###', '#...', '#...', '.##.', '...#', '...#', '###.')
_c('B', 1, '###.', '#..#', '###.', '#..#', '#..#', '#..#', '###.')
_c('D', 1, '###.', '#..#', '#..#', '#..#', '#..#', '#..#', '###.')
_c('M', 1, '#..#', '####', '####', '#..#', '#..#', '#..#', '#..#')
_c('P', 1, '###.', '#..#', '#..#', '###.', '#...', '#...', '#...')




# ------------------------------------------------------- small-caps alternative
# Lowercase drawn as small CAPITALS on x-height rows 3-7, baseline 7, matching
# the uppercase baseline exactly. This sidesteps the problem four passes at a
# lowercase g could not fix: with no double-storey forms in the face, a small G
# cannot be misread as a or q, so no descender is needed and the vertical
# metrics stay untouched. It also makes every letter the same height, which is
# the other thing the mixed-density words were suffering from.
SMALLCAP = {}
def _s(ch, *rows): SMALLCAP[ch] = (3, rows)
_s('a', '.####.', '#....#', '######', '#....#', '#....#')
_s('b', '#####.', '#....#', '#####.', '#....#', '#####.')
_s('c', '.#####', '#.....', '#.....', '#.....', '.#####')
_s('d', '#####.', '#....#', '#....#', '#....#', '#####.')
_s('e', '######', '#.....', '#####.', '#.....', '######')
_s('f', '######', '#.....', '#####.', '#.....', '#.....')
_s('g', '.#####', '#.....', '#..###', '#....#', '.#####')
_s('h', '#....#', '#....#', '######', '#....#', '#....#')
_s('i', '.###.', '..#..', '..#..', '..#..', '.###.')
_s('j', '....##', '....##', '....##', '#...##', '.####.')
_s('k', '#....#', '#..##.', '###...', '#..##.', '#....#')
_s('l', '#.....', '#.....', '#.....', '#.....', '######')
_s('m', '#....#', '##..##', '#.##.#', '#....#', '#....#')
_s('n', '#....#', '##...#', '#.#..#', '#..#.#', '#....#')
_s('o', '.####.', '#....#', '#....#', '#....#', '.####.')
_s('p', '#####.', '#....#', '#####.', '#.....', '#.....')
_s('q', '.####.', '#....#', '#....#', '#..##.', '.#####')
_s('r', '#####.', '#....#', '#####.', '#..##.', '#....#')
_s('s', '.#####', '#.....', '.####.', '.....#', '#####.')
_s('t', '######', '..##..', '..##..', '..##..', '..##..')
_s('u', '#....#', '#....#', '#....#', '#....#', '.####.')
_s('v', '#....#', '#....#', '#....#', '.#..#.', '..##..')
_s('w', '#....#', '#....#', '#.##.#', '##..##', '#....#')
_s('x', '#....#', '.#..#.', '..##..', '.#..#.', '#....#')
_s('y', '#....#', '.#..#.', '..##..', '..##..', '..##..')
_s('z', '######', '....#.', '..##..', '.#....', '######')
SMALLCAP['ü'] = (1, ('.#..#.', '......', '#....#', '#....#', '#....#', '#....#', '.####.'))


# Narrow small-caps forms for ligature interiors. Only the 17 letters that
# appear inside the tier-1 ligature set need one. Widths are chosen so every
# pair in that set satisfies ink(left) + ink(right) <= 7.
NARROWCAP = {}
def _sn(ch, *rows): NARROWCAP[ch] = (3, rows)
_sn('a', '.#.', '#.#', '###', '#.#', '#.#')
_sn('b', '###.', '#..#', '###.', '#..#', '###.')
_sn('c', '###', '#..', '#..', '#..', '###')
_sn('e', '###', '#..', '###', '#..', '###')
_sn('f', '###', '#..', '###', '#..', '#..')
_sn('g', '.###', '#...', '#.##', '#..#', '.###')
_sn('h', '#.#', '#.#', '###', '#.#', '#.#')
_sn('i', '#', '#', '#', '#', '#')
_sn('k', '#.#', '##.', '##.', '#.#', '#.#')
_sn('l', '#.', '#.', '#.', '#.', '##')
_sn('m', '#...#', '##.##', '#.#.#', '#...#', '#...#')
_sn('n', '#..#', '##.#', '#.##', '#..#', '#..#')
_sn('o', '###', '#.#', '#.#', '#.#', '###')
_sn('r', '##.', '#.#', '##.', '#.#', '#.#')
_sn('s', '###', '#..', '###', '..#', '###')
_sn('t', '###', '.#.', '.#.', '.#.', '.#.')
_sn('v', '#.#', '#.#', '#.#', '#.#', '.#.')

def _blank():
    return [[0] * 8 for _ in range(8)]


def _stamp(grid, spec, x0):
    top, rows = spec
    for dy, row in enumerate(rows):
        y = top + dy
        if not 0 <= y < 8:
            continue
        for dx, ch in enumerate(row):
            if ch == '#' and 0 <= x0 + dx < 8:
                grid[y][x0 + dx] = 1
    return grid


def width(spec):
    return max(len(r) for r in spec[1])


def glyph(ch, tight=False, smallcap=False):
    if smallcap and ch in SMALLCAP:
        src = SMALLCAP
    else:
        src = NARROW if (tight and ch in NARROW) else WIDE
    return _stamp(_blank(), src[ch], 0)


def ligature(pair, smallcap=False):
    """Two condensed glyphs sharing a cell, separated by one blank column."""
    a, b = pair
    src = NARROWCAP if smallcap else NARROW
    sa = CAPS[a] if a in CAPS and a.isupper() else src.get(a, WIDE.get(a))
    sb = src.get(b, WIDE.get(b))
    if sa is None or sb is None:
        raise KeyError(pair)
    wa, wb = width(sa), width(sb)
    if wa + wb > 7:
        raise ValueError(f'{pair!r}: {wa + wb}px of ink, 7 available')
    # Spread the pair over the cell rather than packing it left. A narrow pair
    # such as 'li' is only 3px of ink; left-aligned it reads as a fragment
    # floating before a five-column hole.
    gap = max(1, (7 - wa - wb))
    x0 = max(0, (8 - (wa + gap + wb)) // 2)
    return _stamp(_stamp(_blank(), sa, x0), sb, x0 + wa + gap)


def render(text, ligs):
    """Greedy longest-match layout, matching table.py."""
    cells, i = [], 0
    while i < len(text):
        two = text[i:i + 2]
        if len(two) == 2 and two in ligs:
            cells.append(ligature(two)); i += 2
        elif text[i] == ' ':
            cells.append(_blank()); i += 1
        else:
            cells.append(glyph(text[i])); i += 1
    return cells

# ----------------------------------------------- party-name-only ligatures
# Party names are the most-seen strings in the game and only five of the
# fourteen need a merged cell, so those five get bespoke glyphs at their own
# codes. Two freedoms the shared ligatures do not have:
#
#   * the full 8 columns are usable. A shared ligature must keep column 7 clear
#     as an inter-letter gap, because it cannot know what follows it. These are
#     only ever used in one word each, so the neighbouring cells' own margins
#     supply the separation.
#   * the halves can be wider than the shared 3px narrows, and placed by eye
#     rather than by the generic centre-and-spread rule.
#
# Written as explicit 8-column bitmaps so the kerning is visible in the source
# rather than computed. Rows are x-height 3-7.
PARTYLIG = {}
def _p(pair, *rows): PARTYLIG[pair] = (3, rows)
_p('ai', '.###..##', '#...#..#', '#####..#', '#...#..#', '#...#.##')
_p('rr', '##..##..', '#.#.#.#.', '##..##..', '#.#.#.#.', '#.#.#.#.')
_p('en', '###.#..#', '#...##.#', '###.#.##', '#...#..#', '###.#..#')
_p('re', '##...###', '#.#..#..', '##...###', '#.#..#..', '#.#..###')
_p('he', '#.#..###', '#.#..#..', '###..###', '#.#..#..', '#.#..###')
_p('hr', '#.#..##.', '#.#..#.#', '###..##.', '#.#..#.#', '#.#..#.#')


def party_ligature(pair):
    """Bespoke party glyph; falls back to the shared small-caps ligature."""
    if pair in PARTYLIG:
        return _stamp(_blank(), PARTYLIG[pair], 0)
    return ligature(pair, smallcap=True)



# Punctuation for the 8x8 system font.  A Japanese font has no ASCII period,
# comma or apostrophe -- it has 。 and 、 instead, which read as circles in
# English prose -- so these three are drawn here and installed over low-bank
# codes the script never uses.  They bottom-align on row 7 like every other
# glyph, and the comma has no descender because row 7 is the last row there is.
PUNCT = {
    '.': (7, ('#',)),
    ',': (6, ('.#', '#.')),
    "'": (2, ('#', '#')),
}


def punct(ch):
    """8x8 grid for one of the drawn punctuation marks, inset one column."""
    return _stamp(_blank(), PUNCT[ch], 1)
