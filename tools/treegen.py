"""Regenerate a dialogue tree .asm from its compressed .bin.

Recovery path for sources overwritten before ps4disasm was under version
control: the .bin files still hold the originals, so decompress and re-emit.

Byte fidelity is the requirement, not byte-identical formatting - the check
that matters is that compress_script.py --no-compress on the output reproduces
the decompressed bytes exactly.
"""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kosinski
from dialogue import CTRL_OPERANDS, F2_SUB_EXTRA

CH = {0: ' '}
for i, c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    CH[1 + i] = c
for i, c in enumerate('abcdefghijklmnopqrstuvwxyz'):
    CH[27 + i] = c
for v, c in zip(range(0x35, 0x3C), ".',\u00b7:!?"):
    CH[v] = c
CH[0x3C] = '-'
CH[0x3F] = '%'
for i, c in enumerate('0123456789'):
    CH[64 + i] = c
# $3D/$3E are the quote pair: no bare spelling inside a dc.b string
RAW = {0x3D, 0x3E}


def to_asm(plain: bytes) -> str:
    out, text, idx = [], [], 0
    out.append('; 0')

    def flush():
        if text:
            out.append('\tdc.b\t"' + ''.join(text) + '"')
            text.clear()

    i = 0
    while i < len(plain):
        b = plain[i]
        if b >= 0xF0:
            flush()
            if b == 0xFF:
                out.append('\tdc.b\t$FF')
                idx += 1
                i += 1
                if i < len(plain):
                    out.append(f'; ${idx:X}')
                continue
            n = CTRL_OPERANDS.get(b, 0)
            if b == 0xF2 and i + 1 < len(plain):
                n += F2_SUB_EXTRA.get(plain[i + 1], 0)
            ops = plain[i + 1:i + 1 + n]
            out.append(f'\tdc.b\t${b:02X}')
            if ops:
                out.append('\tdc.b\t' + ', '.join(f'${o:02X}' for o in ops))
            i += 1 + n
        elif b in CH and b not in RAW:
            text.append(CH[b]); i += 1
        else:
            flush()
            out.append(f'\tdc.b\t${b:02X}'); i += 1
    flush()
    return '\n'.join(out) + '\n'


def main():
    if len(sys.argv) < 3:
        print('usage: treegen.py <in.bin> <out.asm>'); return 1
    plain = kosinski.decompress(open(sys.argv[1], 'rb').read())
    io.open(sys.argv[2], 'w', encoding='utf-8', newline='\n').write(to_asm(plain))
    print(f'{sys.argv[1]}: {len(plain)} bytes -> {sys.argv[2]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
