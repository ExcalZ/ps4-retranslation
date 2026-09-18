"""Port the spaceship destination menu from script_translated.json.

Three window-charset strings behind the Landale's "where to?" screen, which
the extraction never covered and which the US abbreviated to fit 7 fixed
cells (`A.CASTL`):

    loc_2AAA46   "Where do you want to go?"        the prompt window
    loc_2AAA60   " will be" {FC} "the destination."  appended after the
                 chosen name in RAM (the name comes FIRST, by code)
    loc_2AAA7A   six $FE-terminated destination names, walked by ordinal

The JP originals sit in the same order at $2ABC88 in work/rom.bin (found by
encoding モタビア with ps4.tbl and searching; the whole block mirrors the US
one string for string).  Segment `00:008` in the JSON, ROM order.

All three COMPOSE, via VWFMENU_SPACE_LO/HI for the two ROM strings and the
name list, and via VWFField_LoadWindowTiles for the RAM-assembled
confirmation - so the names can say what the Japanese says.  Budgets, from
the window group (WinGroup_Event 5-$A) and the US text:

    prompt         24 cells  (window 5 is 25 wide, text at x+1)
    names           7 cells  (windows 6-$A are 10 wide, name at x+3)
    confirmation   two lines; line 1 carries the longest name in front

    python tools/spacemenu.py --export   add segment 00:008 to the JSON
    python tools/spacemenu.py            report
    python tools/spacemenu.py --write    rewrite ps4.asm from the JSON
"""
import io
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASM = os.path.join(ROOT, 'ps4disasm', 'ps4.asm')
SCRIPT = os.path.join(ROOT, 'work', 'script_translated.json')
JPROM = os.path.join(ROOT, 'work', 'rom.bin')
SEGMENT = '00:008'
JP_BASE = 0x2ABC88

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from menustrip import glyph_of
from table import Table

LEGAL = set(" !',-.0123456789:?ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "abcdefghijklmnopqrstuvwxyz")
PROMPT_CELLS, NAME_CELLS = 24, 7
# (label, terminator, kind)
STRINGS = [('loc_2AAA46', 0xFE, 'prompt'),
           ('loc_2AAA60', 0xFF, 'confirm'),
           ('loc_2AAA7A', 0xFE, 'names')]
NAMES = 6


def cells(text):
    """Composed width in cells, the composer's own arithmetic."""
    px = sum(glyph_of(c, text)[1] for c in text)
    return max(1, math.ceil(px / 8))


def block(lines, label):
    """Indices of the dc.b lines under `label`, up to and including the last
    terminator of that string (the names block holds six)."""
    a = next(i for i, l in enumerate(lines) if l.startswith(label + ':'))
    out, terms = [], 0
    want = NAMES if label == 'loc_2AAA7A' else 1
    for i in range(a + 1, len(lines)):
        s = lines[i].strip()
        if not s:
            continue
        if not s.startswith('dc.'):
            break
        out.append(i)
        if re.search(r'\$F[CEF]\b', s) and not re.search(r'\$FC\b', s):
            terms += 1
            if terms == want:
                return out
    raise SystemExit('%s: string not terminated' % label)


def asm_text(lines, idx):
    """The English currently in ps4.asm for a block, {FC}-joined."""
    parts, out = [], []
    for i in idx:
        s = lines[i].strip()
        m = re.match(r'dc\.b\s+"([^"]*)"(.*)$', s)
        if m:
            parts.append(m.group(1))
            tail = m.group(2)
        else:
            tail = s
        if re.search(r'\$FC\b', tail):
            parts.append('{FC}')
        if re.search(r'\$F[EF]\b', tail):
            out.append(''.join(parts)); parts = []
    return out


def render(text, term):
    out = []
    for i, line in enumerate(text.split('{FC}')):
        end = ', $FC' if i < text.count('{FC}') else ', $%02X' % term
        out.append('\tdc.b\t"%s"%s' % (line, end))
    return out


def jp_entries():
    rom = open(JPROM, 'rb').read()
    tbl = Table()
    out, a = [], JP_BASE
    for _ in range(2 + NAMES):
        b = a
        while rom[b] < 0xFE:
            b += 1
        raw = rom[a:b]
        out.append({'offset': a, 'term': rom[b], 'raw_len': b - a + 1,
                    'hex': raw.hex(), 'jp': tbl.decode_str(raw)})
        a = b + 1
    return out


def export(doc, lines):
    if any((e.get('segment') or '') == SEGMENT for e in doc['entries']):
        print('segment %s already exported' % SEGMENT)
        return 0
    us = []
    for label, term, kind in STRINGS:
        us += asm_text(lines, block(lines, label))
    assert len(us) == 2 + NAMES, us
    jp = jp_entries()
    seg_start, seg_end = jp[0]['offset'], jp[-1]['offset'] + jp[-1]['raw_len']
    new = []
    for i, (j, u) in enumerate(zip(jp, us)):
        new.append({'id': 'r00s%s#%03d' % (SEGMENT.split(':')[1], i),
                    'region': 0, 'segment': SEGMENT,
                    'seg_start': seg_start, 'seg_end': seg_end,
                    'offset': j['offset'], 'term': j['term'],
                    'raw_len': j['raw_len'], 'hex': j['hex'], 'jp': j['jp'],
                    'en': u, 'note': '', 'us': u})
    # keep the file's segment order: after the last 00:007 row
    last = max(i for i, e in enumerate(doc['entries'])
               if (e.get('segment') or '') == '00:007')
    doc['entries'][last + 1:last + 1] = new
    io.open(SCRIPT, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(doc, ensure_ascii=False, indent=1) + '\n')
    print('exported %d rows as %s' % (len(new), SEGMENT))
    for e in new:
        print('  %s  %-16s %r' % (e['id'], e['jp'], e['en']))
    return 0


def main():
    lines = io.open(ASM, encoding='utf-8', errors='replace').read().split('\n')
    doc = json.load(io.open(SCRIPT, encoding='utf-8'))
    if '--export' in sys.argv:
        return export(doc, lines)
    rows = [e for e in doc['entries'] if (e.get('segment') or '') == SEGMENT]
    rows.sort(key=lambda e: int(e['id'].rsplit('#', 1)[1]))
    if len(rows) != 2 + NAMES:
        print('%s has %d rows, expected %d (run --export first)'
              % (SEGMENT, len(rows), 2 + NAMES))
        return 1
    en = [(r.get('en') or '').rstrip() for r in rows]   # a leading space is part of the tail
    if any(not t.strip() for t in en):
        print('every %s row needs an English text' % SEGMENT)
        return 1
    for r, t in zip(rows, en):
        bad = sorted(set(t.replace('{FC}', '')) - LEGAL)
        if bad:
            print('  %s: %r has no charset code for %s'
                  % (r['id'], t, ' '.join(repr(c) for c in bad)))
            return 1
    prompt, confirm, names = en[0], en[1], en[2:]
    problems = []
    if cells(prompt) > PROMPT_CELLS:
        problems.append('prompt %r is %d cells, the window holds %d'
                        % (prompt, cells(prompt), PROMPT_CELLS))
    for n in names:
        if cells(n) > NAME_CELLS:
            problems.append('%r is %d cells, the list field holds %d'
                            % (n, cells(n), NAME_CELLS))
    lines_c = confirm.split('{FC}')
    if len(lines_c) > 2:
        problems.append('confirmation has %d lines, the box holds 2' % len(lines_c))
    longest = max(names, key=cells)
    if cells(longest + lines_c[0]) > PROMPT_CELLS:
        problems.append('%r + %r is %d cells on line 1'
                        % (longest, lines_c[0], cells(longest + lines_c[0])))
    if problems:
        for p in problems:
            print('  ' + p)
        return 1

    edits = []
    for (label, term, kind), texts in zip(STRINGS, [[prompt], [confirm], names]):
        idx = block(lines, label)
        body = []
        for t in texts:
            body += render(t, term)
        edits.append((idx, body, label))
    print('  prompt        %2d cells  %r' % (cells(prompt), prompt))
    print('  confirmation  %s' % ' / '.join('%d cells %r' % (cells(l), l) for l in lines_c))
    for n in names:
        print('  name          %2d cells  %r' % (cells(n), n))
    if '--write' not in sys.argv:
        print('(dry run; pass --write to rewrite ps4.asm)')
        return 0
    changed = 0
    for idx, body, label in sorted(edits, key=lambda e: -e[0][0]):
        if lines[idx[0]:idx[-1] + 1] != body:
            changed += 1
        lines[idx[0]:idx[-1] + 1] = body
    io.open(ASM, 'w', encoding='utf-8', errors='replace',
            newline='\n').write('\n'.join(lines))
    print('rewrote %d of %d blocks in ps4.asm' % (changed, len(edits)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
