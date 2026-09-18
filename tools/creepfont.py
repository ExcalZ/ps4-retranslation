"""Party-name glyphs, derived from the creep typeface.

creep is by romeovs and released under the MIT Licence:

    Copyright romeovs 2015

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

Only the party-name field uses these. Techniques and skills use the small-caps
set in lowerfont.py, because creep is drawn for a 5px advance and reads sparse
when one glyph occupies a whole 8px cell - the party names avoid that by being
fully paired, two glyphs per cell at x=0 and x=4.

Placement is deliberately FIXED at x=0 and x=4 rather than fitted to each
glyph's ink extent. Fitting was tried and is worse: it discards creep's own
side bearings, so adjacent strokes merge and n starts reading as r.

Baseline is row 6, one above the small-caps baseline, which is what buys the
real descenders on y, g and j.
"""

# pair or single -> 8 rows of 8 columns, 1 = ink
GLYPHS = {
  'Fa': (
    '11110000',
    '10000000',
    '10000111',
    '11001001',
    '10001001',
    '10001001',
    '10000111',
    '00000000',
  ),
  'Fo': (
    '11110000',
    '10000000',
    '10000110',
    '11001001',
    '10001001',
    '10001001',
    '10000110',
    '00000000',
  ),
  'Fr': (
    '11110000',
    '10000000',
    '10001110',
    '11001001',
    '10001000',
    '10001000',
    '10001000',
    '00000000',
  ),
  'Ha': (
    '10010000',
    '10010000',
    '11110111',
    '10011001',
    '10011001',
    '10011001',
    '10010111',
    '00000000',
  ),
  'La': (
    '10000000',
    '10000000',
    '10000111',
    '10001001',
    '10001001',
    '10001001',
    '11110111',
    '00000000',
  ),
  'Py': (
    '11100000',
    '10010000',
    '10011001',
    '11101001',
    '10001001',
    '10001001',
    '10000111',
    '00001001',
  ),
  'Ra': (
    '11100000',
    '10010000',
    '10010111',
    '11101001',
    '11001001',
    '10101001',
    '10010111',
    '00000000',
  ),
  'Ru': (
    '11100000',
    '10010000',
    '10011001',
    '11101001',
    '11001001',
    '10101001',
    '10010111',
    '00000000',
  ),
  'Sh': (
    '01101000',
    '10011000',
    '10001110',
    '01101001',
    '00011001',
    '10011001',
    '01101001',
    '00000000',
  ),
  'Si': (
    '01100100',
    '10010000',
    '10001100',
    '01100100',
    '00010100',
    '10010100',
    '01100110',
    '00000000',
  ),
  'Th': (
    '11101000',
    '01001000',
    '01001110',
    '01001001',
    '01001001',
    '01001001',
    '01001001',
    '00000000',
  ),
  'a': (
    '00000000',
    '00000000',
    '01110000',
    '10010000',
    '10010000',
    '10010000',
    '01110000',
    '00000000',
  ),
  'am': (
    '00000000',
    '00000000',
    '01111001',
    '10011111',
    '10011001',
    '10011001',
    '01111001',
    '00000000',
  ),
  'dy': (
    '00010000',
    '00010000',
    '01111001',
    '10011001',
    '10011001',
    '10011001',
    '01110111',
    '00001001',
  ),
  'en': (
    '00000000',
    '00000000',
    '01101110',
    '10011001',
    '11111001',
    '10001001',
    '01111001',
    '00000000',
  ),
  'es': (
    '00000000',
    '00000000',
    '01100111',
    '10011000',
    '11110110',
    '10000001',
    '01111110',
    '00000000',
  ),
  'hn': (
    '10000000',
    '10000000',
    '11101110',
    '10011001',
    '10011001',
    '10011001',
    '10011001',
    '00000000',
  ),
  'il': (
    '01001000',
    '00001000',
    '11001000',
    '01001000',
    '01001000',
    '01001000',
    '01100100',
    '00000000',
  ),
  'ja': (
    '01000000',
    '00000000',
    '11000111',
    '01001001',
    '01001001',
    '01001001',
    '01000111',
    '01000000',
  ),
  'ke': (
    '10000000',
    '10000000',
    '10010110',
    '10101001',
    '11001111',
    '10101000',
    '10010111',
    '00000000',
  ),
  'l': (
    '10000000',
    '10000000',
    '10000000',
    '10000000',
    '10000000',
    '10000000',
    '01000000',
    '00000000',
  ),
  'ra': (
    '00000000',
    '00000000',
    '11100111',
    '10011001',
    '10001001',
    '10001001',
    '10000111',
    '00000000',
  ),
  'rr': (
    '00000000',
    '00000000',
    '11101110',
    '10011001',
    '10001000',
    '10001000',
    '10001000',
    '00000000',
  ),
  's': (
    '00000000',
    '00000000',
    '01110000',
    '10000000',
    '01100000',
    '00010000',
    '11100000',
    '00000000',
  ),
  'y': (
    '00000000',
    '00000000',
    '10010000',
    '10010000',
    '10010000',
    '10010000',
    '01110000',
    '10010000',
  ),
}


def bitmap(key):
    """8x8 grid of 0/1 for a pair or single letter."""
    return [[1 if c == '1' else 0 for c in row] for row in GLYPHS[key]]
