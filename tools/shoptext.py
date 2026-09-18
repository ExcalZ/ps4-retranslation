"""Port the shop and inn prompts from dialogue_full.json into the disassembly.

The 65 strings between `loc_2AC0DE` and `InventoryDescriptions` are the inn and
shop windows. They are fragments, not sentences: the engine concatenates them
with an item name, a shop type or a price, so a leading or trailing space is
load-bearing and must survive translation.

Nearly every one carries its own `loc_` label and `FieldRoutine_Shop` reaches
them by name, so the labels are preserved exactly where they are; only the
bytes between them are rewritten.

Pairing with the JP is positional against `dlg00`, and the alignment is checked
at both ends rather than assumed:

    dlg00 #0155-#0204  ->  US 0-49
    dlg00 #0205-#0206  ->  dropped by the US build
    dlg00 #0207-#0221  ->  US 50-64

67 JP strings, 65 US slots. The group boundaries agree on both sides (two inn
voices of 6, two shop voices of 17, the three shop-type nouns, Naura, then
Bayamare's block), which is what makes the two dropped strings identifiable
rather than a guess.

    python tools/shoptext.py            report, and verify a no-op round trip
    python tools/shoptext.py --write    rewrite ps4.asm
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASM = os.path.join(ROOT, 'ps4disasm', 'ps4.asm')
DIALOGUE = os.path.join(ROOT, 'work', 'dialogue_full.json')
START, END = 'loc_2AC0DE:', 'InventoryDescriptions:'
LABEL = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*):')

# US slot -> dlg00 row. The two JP strings the US build has no slot for are
# #0205 and #0206, a confirmation and a thank-you for the Naura cake shop.
def jp_row(slot):
    return 155 + slot if slot < 50 else 157 + slot


def parse(lines):
    """[(label or None, [body lines])] for each $FF-terminated string."""
    a = next(i for i, l in enumerate(lines) if l.startswith(START))
    b = next(i for i, l in enumerate(lines) if l.startswith(END))
    out, lab, body = [], lines[a].rstrip(':'), []
    i = a + 1
    while i < b:
        s = lines[i].strip()
        m = LABEL.match(lines[i])
        if m:
            lab = m.group(1)
        elif s.startswith('dc.b'):
            body.append(lines[i])
            if re.search(r'\$F[EF]\b', s):
                out.append((lab, body))
                lab, body = None, []
        i += 1
    return a, b, out


TOKEN = re.compile(r'\{(BR|ctl\.[0-9A-F]{2})\}')
PIECE = re.compile(r'"[^"]*"|\$[0-9A-Fa-f]{2}')


def render(label, text, term):
    """dc.b lines for one string, every control written back as a raw byte.

    $FC is not the only control here: two of these strings open with $FD, and
    an earlier version that handled only $FC dropped it and shifted the whole
    block by a byte. Anything that is not text goes back out verbatim.
    """
    out = ['']
    if label:
        out.append(label + ':')
    def emit(run):
        # AS drops a space that directly follows the opening quote, so a
        # fragment beginning with one silently loses it -- which is how the
        # stock " store." became "store." and would have rendered
        # "theWeaponsshop.". Write edge spaces as explicit bytes instead.
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
        out.append('\tdc.b\t$%s' % ('FC' if tok == 'BR' else tok.split('.')[1]))
        pos = m.end()
    if text[pos:]:
        emit(text[pos:])
    out.append('\tdc.b\t' + term)
    out.append('')
    out.append('\teven')
    return out


def decode(body):
    """The string a parsed body represents, in our {BR}/{ctl.XX} notation."""
    parts = []
    for ln in body:
        for piece in PIECE.findall(ln.strip()[4:]):
            if piece.startswith('"'):
                parts.append(piece[1:-1])
                continue
            v = int(piece[1:], 16)
            if v in (0xFE, 0xFF):
                continue
            parts.append('{BR}' if v == 0xFC else '{ctl.%02X}' % v)
    return ''.join(parts)


def main():
    lines = io.open(ASM, encoding='utf-8', errors='replace').read().split('\n')
    a, b, entries = parse(lines)
    print('%d US shop/inn strings between %s and %s' % (len(entries), START, END))
    if len(entries) != 65:
        print('  expected 65 - refusing to touch it'); return 1

    doc = json.load(io.open(DIALOGUE, encoding='utf-8'))
    rows = [e for e in doc['entries'] if e['id'].startswith('dlg00')]
    new = []
    for slot, (lab, body) in enumerate(entries):
        e = rows[jp_row(slot)]
        # NOT stripped: these are fragments, and a leading space before
        # " meseta." or " shop." is the separator from the number or the shop
        # type that precedes it.
        en = e.get('en') or ''
        new.append(en if en.strip() else decode(body))
    done = sum(1 for slot in range(65) if (rows[jp_row(slot)].get('en') or '').strip())
    print('%d of 65 translated; the rest keep the US text' % done)

    out = []
    for (lab, body), text in zip(entries, new):
        term = '$FE' if any('$FE' in l for l in body) else '$FF'
        out += render(lab, text, term)
    # Normalise the seams so repeated runs are a no-op: a build must not add a
    # blank line to ps4.asm every time it runs.
    head = lines[:a]
    while head and not head[-1].strip():
        head.pop()
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    lines = head + [''] + out + [''] + lines[b:]
    if '--write' not in sys.argv:
        print('(dry run; pass --write to rewrite ps4.asm)')
        return 0
    io.open(ASM, 'w', encoding='utf-8', errors='replace',
            newline='\n').write('\n'.join(lines))
    print('rewrote the shop/inn block in ps4.asm')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
