"""Port the enemy and enemy-skill names from script_translated.json.

These two tables were validated by `trpatch8` and measured by `test_paths`, but
nothing ever wrote them: the ROM kept the US build's own list, in caps, so the
game showed HELEX and PROTECTBIT while the JSON said Herex and Protector Bit.
They render through the menu VWF at runtime, which is why they LOOKED like our
text -- the face was ours, the words were not. Same failure as the item
descriptions before `itemdesc.py` existed.

    EnemyNames        153 entries; the JSON covers the first 152
    EnemySkillNames   112 entries; the JSON covers all of them

The 153rd enemy slot has no JSON row and is left exactly as it is, the same
rule the shop block follows: port what the extraction actually paired, and do
not guess at the remainder.

Both assemble under `general/tables/wincharset.asm`, which carries A-Z, a-z,
0-9, space and `- ! ? : . ' ,`, so mixed case needs nothing new. A name using
anything else is reported and skipped rather than written and mis-encoded.

    python tools/enemynames.py            report, and verify a no-op round trip
    python tools/enemynames.py --write    rewrite ps4.asm
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASM = os.path.join(ROOT, 'ps4disasm', 'ps4.asm')
SCRIPT = os.path.join(ROOT, 'work', 'script_translated.json')
LABEL = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*):')
# Seven slots carry a trailing comment naming the boss they belong to
# (`dc.b "NOTHING", $FF   ; Dark Force (1)`).  Capture it and put it back:
# those annotations are the only record of which blank slot is which.
ENTRY = re.compile(r'^(\s*dc\.b\s+)"([^"]*)"(\s*,\s*\$FF)(.*)$')

TABLES = [('EnemyNames', 'r02s001', 153), ('EnemySkillNames', 'r02s002', 112)]
LEGAL = set(" !',-.0123456789:?ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "abcdefghijklmnopqrstuvwxyz")


def block(lines, label):
    a = next(i for i, l in enumerate(lines) if l.startswith(label + ':'))
    b = next(i for i in range(a + 1, len(lines)) if LABEL.match(lines[i]))
    return a, b


def main():
    lines = io.open(ASM, encoding='utf-8', errors='replace').read().split('\n')
    doc = json.load(io.open(SCRIPT, encoding='utf-8'))
    changed = skipped = 0

    for label, prefix, expect in TABLES:
        a, b = block(lines, label)
        idx = [i for i in range(a + 1, b) if ENTRY.match(lines[i])]
        if len(idx) != expect:
            print('%s: %d entries, expected %d - refusing to touch it'
                  % (label, len(idx), expect))
            return 1
        rows = [e for e in doc['entries'] if e['id'].startswith(prefix)]
        print('%s: %d slots, %d JSON rows' % (label, len(idx), len(rows)))
        for n, line_no in enumerate(idx):
            if n >= len(rows):
                break                      # slot with no row: leave it alone
            en = (rows[n].get('en') or '').strip()
            if not en:
                continue
            bad = sorted(set(en) - LEGAL)
            if bad:
                print('  %s: %r has no charset code for %s'
                      % (rows[n]['id'], en, ' '.join(repr(c) for c in bad)))
                skipped += 1
                continue
            m = ENTRY.match(lines[line_no])
            new = '%s"%s"%s%s' % (m.group(1), en, m.group(3), m.group(4))
            if new != lines[line_no]:
                changed += 1
            lines[line_no] = new

    print('%d line(s) would change, %d skipped' % (changed, skipped))
    if '--write' not in sys.argv:
        print('(dry run; pass --write to rewrite ps4.asm)')
        return 0
    io.open(ASM, 'w', encoding='utf-8', errors='replace',
            newline='\n').write('\n'.join(lines))
    print('rewrote both enemy tables in ps4.asm')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
