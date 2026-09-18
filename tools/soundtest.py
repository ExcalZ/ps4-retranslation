"""Port the sound-test track titles from script_translated.json into ps4.asm.

This table is the odd one out in the 8x8 bank: the JP staff wrote it in Latin
themselves, so it survives untouched in the US build, typos and all.  It is
stored as raw `dc.b` bytes in the high bank -- capitals at $80, digits at $9A,
and the four punctuation glyphs the Japanese font happens to carry, $B0 `-`,
$B1 `!`, $B2 `?`, $B4 `.`.

That is the whole character set available here.  There is no apostrophe and no
comma in the high bank, and the low bank the font install rewrites belongs to
the other pipeline, so a title has to be spelled without them.

    python tools/soundtest.py            report only
    python tools/soundtest.py --write    rewrite ps4.asm
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASM = os.path.join(ROOT, 'ps4disasm', 'ps4.asm')
SCRIPT = os.path.join(ROOT, 'work', 'script_translated.json')
SEGMENT = '01:004'
LABEL = 'loc_2AFA28'
TERM = 0xFE

CODE = {' ': 0x00, '-': 0xB0, '!': 0xB1, '?': 0xB2, '.': 0xB4}
for _i, _c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    CODE[_c] = 0x80 + _i
for _i, _c in enumerate('0123456789'):
    CODE[_c] = 0x9A + _i

BYTE = re.compile(r'\$([0-9A-Fa-f]{2})\b')
NEXT_LABEL = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*:')


def titles():
    d = json.load(io.open(SCRIPT, encoding='utf-8'))
    es = d['entries'] if isinstance(d, dict) else d
    rows = [e for e in es if (e.get('segment') or '') == SEGMENT]
    rows.sort(key=lambda e: int(e['id'].rsplit('#', 1)[1]))
    return [(e.get('en') or e.get('jp') or '') for e in rows]


def bounds(lines):
    a = next(i for i, ln in enumerate(lines) if ln.startswith(LABEL + ':'))
    b = next(i for i in range(a + 1, len(lines)) if NEXT_LABEL.match(lines[i]))
    return a, b


def original(lines, a, b):
    out = bytearray()
    for ln in lines[a:b]:
        for h in BYTE.findall(ln):
            out.append(int(h, 16))
    return bytes(out)


def encode(names):
    out = bytearray()
    for t in names:
        for ch in t:
            out.append(CODE[ch])
        out.append(TERM)
    return bytes(out)


def emit(data):
    lines = ['']
    for i in range(0, len(data), 16):
        row = data[i:i + 16]
        lines.append('\tdc.b\t' + ', '.join('$%02X' % v for v in row))
    lines.append('')
    return lines


def main():
    names = titles()
    bad = [(i, t, sorted({c for c in t if c not in CODE}))
           for i, t in enumerate(names) if any(c not in CODE for c in t)]
    print('%d track titles' % len(names))
    for i, t, miss in bad:
        print('  %02d has no glyph for %s: %s' % (i, miss, t))
    if bad:
        return 1

    lines = io.open(ASM, encoding='utf-8', errors='replace').read().split('\n')
    a, b = bounds(lines)
    old = original(lines, a, b)
    # everything past the last title's terminator is a different table's data
    end, n = 0, 0
    for j, v in enumerate(old):
        if v == TERM:
            n += 1
            if n == len(names):
                end = j + 1
                break
    new = encode(names) + old[end:]
    print('%d bytes -> %d bytes (%+d)' % (len(old), len(new), len(new) - len(old)))
    if '--write' not in sys.argv:
        print('(dry run; pass --write to rewrite ps4.asm)')
        return 0
    out = lines[:a + 1] + emit(new) + lines[b:]
    io.open(ASM, 'w', encoding='utf-8', errors='replace',
            newline='\n').write('\n'.join(out))
    print('rewrote the sound-test table in ps4.asm')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
