"""Port the combination and vehicle attack names from script_translated.json.

Neither table was ever extracted and neither was ever written.  They sit
together at $29F69C, outside every range the extraction covered and outside
both ranges the menu composer recognised, so all twenty-two entries were still
the US build's abbreviations drawn in the fixed-width face -- TRIBLASTER for
what the JP ROM calls トリニティブラスター, X-BURST for ゼランバスター.

The JP tables are at $285474 and $285556 in work/rom.bin.  They were found
through the dispatch that selects between the five battle name tables: the JP
ROM has the same five `lea`/`bra.s` pairs at the same eight-byte stride, and
three of the five targets match segments the extraction already carried, which
is what makes the other two trustworthy.

    python tools/combonames.py            report
    python tools/combonames.py --write    rewrite ps4.asm
"""
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASM = os.path.join(ROOT, 'ps4disasm', 'ps4.asm')
SCRIPT = os.path.join(ROOT, 'work', 'script_translated.json')

# label, segment, ROM slots, JSON rows, field width in CELLS.
#
# Cells, measured with menustrip.compose, because that is the count trpatch8
# previews in the JSON and the count the runtime composer arrives at -- both
# are ceil(sum of advances / 8).  Summing pixels here instead over-measured by
# the final glyph's trailing gap, which no cell has to hold: it made "Cathode
# Ray Tube" 11 cells when it is 10.
#
# ComboNames: the name is drawn one cell into a region loc_27DD04 copies
# twelve cells wide, so cells 1..11 land inside it -- but ten of the fourteen
# US names are exactly ten characters, which puts the frame's right border at
# cell 11.  Ten cells it is, and a name needing eleven would draw over the
# border rather than be clipped, so this refuses instead of writing it.
#
# VehicleAttackNames: Battle_VehOpenSkills frames fourteen cells, writes its
# cursor at column 1 and the two state icons at columns 11 and 12, and starts
# the name at column 3.  Columns 3..10 is eight cells -- one more than the US
# names use.  Its eighth slot has no JP counterpart and no JSON row, and is
# left exactly as it is, the same rule enemynames.py follows for the 153rd
# enemy: port what the extraction actually paired, and do not guess.
TABLES = [('ComboNames', '00:005', 14, 14, 10),
          ('VehicleAttackNames', '00:006', 8, 7, 8)]

from menustrip import compose

LABEL = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*):')
ENTRY = re.compile(r'^(\s*dc\.b\s+)"([^"]*)"(\s*,\s*\$FF)(.*)$')

CODE = {' ': 0}
for i, c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'): CODE[c] = 1 + i
for i, c in enumerate('0123456789'): CODE[c] = 27 + i
for i, c in enumerate('abcdefghijklmnopqrstuvwxyz'): CODE[c] = 57 + i
CODE['-'] = 0x31; CODE['!'] = 0x32; CODE['?'] = 0x33; CODE[':'] = 0x34
CODE['.'] = 0x53; CODE["'"] = 0x54; CODE[','] = 0x55; CODE['ü'] = 0x57


def block(lines, label):
    a = next(i for i, l in enumerate(lines) if l.startswith(label + ':'))
    b = next(i for i in range(a + 1, len(lines)) if LABEL.match(lines[i]))
    return a, b


def main():
    lines = io.open(ASM, encoding='utf-8', errors='replace').read().split('\n')
    doc = json.load(io.open(SCRIPT, encoding='utf-8'))
    changed = 0

    for label, segment, slots, expect, field in TABLES:
        a, b = block(lines, label)
        idx = [i for i in range(a + 1, b) if ENTRY.match(lines[i])]
        rows = [e for e in doc['entries'] if (e.get('segment') or '') == segment]
        rows.sort(key=lambda e: int(e['id'].rsplit('#', 1)[1]))
        if len(idx) != slots or len(rows) != expect:
            print('%s: %d slots and %d JSON rows, expected %d and %d'
                  % (label, len(idx), len(rows), slots, expect))
            return 1

        blank = 0
        for n, line_no in enumerate(idx):
            if n >= len(rows):
                break
            en = (rows[n].get('en') or '').strip()
            if not en:
                blank += 1
                continue
            bad = sorted(set(en) - set(CODE))
            if bad:
                print('  %s: %r has no charset code for %s'
                      % (rows[n]['id'], en, ' '.join(repr(c) for c in bad)))
                return 1
            n_cells = compose(en)[0]
            if n_cells > field:
                print('  %s: %r is %d cells in the %d-cell field'
                      % (rows[n]['id'], en, n_cells, field))
                return 1
            m = ENTRY.match(lines[line_no])
            new = '%s"%s"%s%s' % (m.group(1), en, m.group(3), m.group(4))
            if new != lines[line_no]:
                changed += 1
            lines[line_no] = new
        print('%-20s %2d slots, %2d translated, %2d left as the US name'
              % (label, slots, expect - blank, slots - (expect - blank)))

    print('%d line(s) would change' % changed)
    if '--write' not in sys.argv:
        print('(dry run; pass --write to rewrite ps4.asm)')
        return 0
    io.open(ASM, 'w', encoding='utf-8', errors='replace',
            newline='\n').write('\n'.join(lines))
    print('rewrote both battle name tables in ps4.asm')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
