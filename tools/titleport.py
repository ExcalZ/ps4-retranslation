"""Port the attract-mode prologue into ps4.asm's TitleText / TitleText2.

The prologue is NOT a dialogue tree and NOT a stream - it is plain dc.b data
in ps4.asm, which is why treeport.py never touched it and the build still
showed the US text. In our JP extraction it is region 2.

Both blocks are indexed by GetOffsetByID, which counts $FF terminators from the
base, so the ENTRY COUNT must be preserved exactly: a short block means the
renderer indexes past it into whatever data follows. Our text is therefore
padded with empty entries up to the original count rather than simply replacing.

  python tools/titleport.py            report only
  python tools/titleport.py --write
"""
import io, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dialogue

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASM = os.path.join(ROOT, 'ps4disasm', 'ps4.asm')
LABEL = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*:')
# region 2 record ids: the verse, then the Algol backstory
VERSE = range(8, 15)
STORY = range(15, 39)


def block(lines, label):
    i = next(k for k, l in enumerate(lines) if l.startswith(label + ':'))
    k = i + 1
    n = 0
    while k < len(lines) and not LABEL.match(lines[k]):
        n += lines[k].count('$FF')
        k += 1
    return i + 1, k, n


def emit(texts, total):
    out = []
    for t in texts:
        out.append(f'\tdc.b\t"{t}", $FF' if t else '\tdc.b\t$FF')
    for _ in range(total - len(texts)):
        out.append('\tdc.b\t$FF')
    out.append('\teven')
    return out


def main():
    write = '--write' in sys.argv
    ents = {e['id']: e for e in dialogue.load(
        os.path.join(ROOT, 'work', 'dialogue_full.json')) if e.get('region') == 2}
    by = {}
    for k, e in ents.items():
        m = re.search(r'#(\d+)', k)
        if m:
            by[int(m.group(1))] = (e.get('en') or '').strip()

    lines = io.open(ASM, encoding='utf-8', errors='replace').read().split('\n')
    plan = []
    for label, rng, blanks in (('TitleText', VERSE, [14]),
                               ('TitleText2', STORY, [20, 31, 32])):
        a, b, n = block(lines, label)
        texts = []
        for i in rng:
            # A source narration row may be expanded into multiple English
            # scroll rows. Newlines are editorial structure, not ROM bytes;
            # each resulting row gets its own $FF terminator below.
            texts.extend(by.get(i, '').splitlines() or [''])
            if i in blanks:
                texts.append('')            # the JP's own blank-line beats
        if len(texts) > n:
            print(f'{label}: {len(texts)} entries exceeds the original {n}')
            return 1
        plan.append((label, a, b, n, texts))
        print(f'{label}: {len(texts)} of {n} entries used, '
              f'{n - len(texts)} padded blank')
    if write:
        for label, a, b, n, texts in sorted(plan, key=lambda x: -x[1]):
            lines[a:b] = emit(texts, n)
        io.open(ASM, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
        print('written')
    else:
        print('(dry run; pass --write)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
