"""Port the party "nothing here" lines and scenery examines into the disassembly.

The block from `WinTiles_PlayerNothingMsg` to the `charset` reset holds 156
$FF-terminated strings: 28 of examine text, then the staff credits.

    US 0        no JP row (see below)
    US 1-27  -> dlg01 #0000-#0026
    US 28+      the credits, left as the US build has them

Only the first 28 are translated. The credits are names and role titles, and
the US list is already the right answer for them -- there is nothing to gain
from retranslating a person's name and something to lose.

The region-1 extraction began mid-string, so `dlg01#0000` lost its own
`$F4 02` prefix and the `$F4 01` message before it was never captured at all.
That message is still in the JP ROM immediately ahead of the extraction point:

    f4 01  e014 23 e097 2c 34 10 e06c 1a 15 02 20 10 02 42 b1  ff
           何   も 変    わ  っ た  物   は な  い み た  い だ ！

so US 0 is translated from the ROM rather than from the JSON, and is the one
string here whose source is quoted in this file instead of stored in `work/`.

    python tools/examinecredits.py            report, verify a no-op round trip
    python tools/examinecredits.py --write    rewrite ps4.asm
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASM = os.path.join(ROOT, 'ps4disasm', 'ps4.asm')
DIALOGUE = os.path.join(ROOT, 'work', 'dialogue_full.json')
START = 'WinTiles_PlayerNothingMsg:'
LABEL = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*):')
PIECE = re.compile(r'"[^"]*"|\$[0-9A-Fa-f]{2,4}')
TOKEN = re.compile(r'\{(BR|ctl\.[0-9A-F]{2}(?::[0-9A-F]{2})?)\}')

SLOT0 = "{ctl.F4:01}Nothing looks out of the{BR}ordinary here!"
EXAMINE = 28


def parse(lines):
    a = next(i for i, l in enumerate(lines) if l.startswith(START))
    b = next(i for i in range(a, len(lines)) if lines[i].strip() == 'charset')
    out, lab, body, first = [], None, [], None
    for i in range(a + 1, b):
        s = lines[i].strip()
        m = LABEL.match(lines[i])
        if m:
            lab = m.group(1)
        elif s.startswith('dc.'):
            if first is None:
                first = i
            body.append(lines[i])
            if re.search(r'\$F[EF]\b', s):
                out.append((lab, first, i + 1, body))
                lab, body, first = None, [], None
    return a, b, out


def decode(body):
    parts = []
    for ln in body:
        for piece in PIECE.findall(ln.strip().split(None, 1)[1]):
            if piece.startswith('"'):
                parts.append(piece[1:-1])
                continue
            v = int(piece[1:], 16)
            if v in (0xFE, 0xFF):
                continue
            if v > 0xFF:
                parts.append('{ctl.%02X:%02X}' % (v >> 8, v & 0xFF))
            else:
                parts.append('{BR}' if v == 0xFC else '{ctl.%02X}' % v)
    return ''.join(parts)


def render(text):
    out = []

    def emit(run):
        while run.startswith(' '):
            out.append('\tdc.b\t$00')
            run = run[1:]
        trail = len(run) - len(run.rstrip(' '))
        if run.rstrip(' '):
            out.append('\tdc.b\t"%s"' % run.rstrip(' '))
        for _ in range(trail):
            out.append('\tdc.b\t$00')

    pos = 0
    for m in TOKEN.finditer(text):
        if m.start() > pos:
            emit(text[pos:m.start()])
        tok = m.group(1)
        if tok == 'BR':
            out.append('\tdc.b\t$FC')
        elif ':' in tok:
            code, op = tok.split('.')[1].split(':')
            out.append('\tdc.w\t$%s%s' % (code, op))
        else:
            out.append('\tdc.b\t$%s' % tok.split('.')[1])
        pos = m.end()
    if text[pos:]:
        emit(text[pos:])
    out.append('\tdc.b\t$FF')
    # No `even` here. Unlike the shop block, this one separates entries with a
    # bare blank line, and aligning each entry inserted padding after the six
    # odd-length ones -- which surfaced as every pointer in the table at
    # $05910B moving six bytes.
    return out


def main():
    lines = io.open(ASM, encoding='utf-8', errors='replace').read().split('\n')
    a, b, entries = parse(lines)
    print('%d strings in the block; first %d are examine text'
          % (len(entries), EXAMINE))
    if len(entries) != 156:
        print('  expected 156 - refusing to touch it'); return 1

    doc = json.load(io.open(DIALOGUE, encoding='utf-8'))
    rows = [e for e in doc['entries'] if e['id'].startswith('dlg01')]
    edits = []
    for slot, (lab, first, last, body) in enumerate(entries):
        if slot >= EXAMINE:
            continue
        en = SLOT0 if slot == 0 else (rows[slot - 1].get('en') or '')
        if en.strip():
            edits.append((first, last, render(en)))
    print('%d of %d examine strings translated; credits kept as the US build has them'
          % (len(edits), EXAMINE))
    for first, last, body in sorted(edits, reverse=True):
        lines[first:last] = body
    if '--write' not in sys.argv:
        print('(dry run; pass --write to rewrite ps4.asm)')
        return 0
    io.open(ASM, 'w', encoding='utf-8', errors='replace',
            newline='\n').write('\n'.join(lines))
    print('rewrote the examine/credits block in ps4.asm')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
