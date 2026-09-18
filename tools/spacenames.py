"""Port the space-travel destination banners into the disassembly.

Six centred one-line banners, each under its own `SpaceTravelName_*` label and
reached through `SpaceTravel_PlaceNamePtrs`. Only the `dc.b` lines under a
label are replaced, so anything not translated is left exactly as it was.

Two corrections to the US text come from the JP rather than from taste:

    RYKROS               -> RYUCROSS   リュクロス, per work/glossary.md
    ARTIFICIAL SATELLITE -> ARTIFICIAL PLANET   人工惑星

Motavia has no `dlg02` row: like `dlg01#0000`, region 2's extraction began
after it. Its US text already matches our glossary, so it is left alone.

The leading spaces centre the line and are meaningful. They are emitted as
explicit `dc.b $00`, which is the same byte a quoted space assembles to.

    python tools/spacenames.py            report
    python tools/spacenames.py --write    rewrite ps4.asm
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASM = os.path.join(ROOT, 'ps4disasm', 'ps4.asm')
DIALOGUE = os.path.join(ROOT, 'work', 'dialogue_full.json')

# label -> dlg02 row. Motavia is absent: no JP row exists for it.
BANNERS = [('SpaceTravelName_Dezolis', 0),
           ('SpaceTravelName_Rykros', 1),
           ('SpaceTravelName_Zelan', 2),
           ('SpaceTravelName_Kuran', 3),
           ('SpaceTravelName_AirCastle', 4)]


def block(lines, label):
    """(first dc line, last dc line + 1) for the string under `label`."""
    a = next(i for i, l in enumerate(lines) if l.startswith(label + ':'))
    first = None
    for i in range(a + 1, len(lines)):
        s = lines[i].strip()
        if not s:
            continue
        if not s.startswith('dc.'):
            break
        if first is None:
            first = i
        if re.search(r'\$F[EF]\b', s):
            return first, i + 1
    raise SystemExit('%s: no terminated string' % label)


def render(text):
    out = []
    lead = len(text) - len(text.lstrip(' '))
    for _ in range(lead):
        out.append('\tdc.b\t$00')
    body = text.strip(' ')
    if body:
        out.append('\tdc.b\t"%s"' % body)
    for _ in range(len(text) - len(text.rstrip(' ')) if text.strip() else 0):
        out.append('\tdc.b\t$00')
    out.append('\tdc.b\t$FF')
    return out


def main():
    lines = io.open(ASM, encoding='utf-8', errors='replace').read().split('\n')
    doc = json.load(io.open(DIALOGUE, encoding='utf-8'))
    rows = [e for e in doc['entries'] if e['id'].startswith('dlg02')]
    edits = []
    for label, idx in BANNERS:
        en = rows[idx].get('en') or ''
        if not en.strip():
            continue
        first, last = block(lines, label)
        edits.append((first, last, render(en), label, en))
    print('%d of %d banners translated' % (len(edits), len(BANNERS)))
    for _, _, _, label, en in edits:
        print('  %-28s %r' % (label, en))
    if '--write' not in sys.argv:
        print('(dry run; pass --write to rewrite ps4.asm)')
        return 0
    for first, last, body, _, _ in sorted(edits, reverse=True):
        lines[first:last] = body
    io.open(ASM, 'w', encoding='utf-8', errors='replace',
            newline='\n').write('\n'.join(lines))
    print('rewrote the space-travel banners in ps4.asm')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
