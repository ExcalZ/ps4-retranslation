"""Minimal Motorola 68000 disassembler - enough to read game logic.

Covers the instruction families that show up in Mega Drive game code. Anything
unrecognised is emitted as `dc.w $xxxx` so the stream stays aligned and a bad
decode is visible rather than silent.
"""
import struct

SIZES = {0: '.b', 1: '.w', 2: '.l'}
MOVE_SIZES = {1: '.b', 3: '.w', 2: '.l'}
CC = ['t', 'f', 'hi', 'ls', 'cc', 'cs', 'ne', 'eq',
      'vc', 'vs', 'pl', 'mi', 'ge', 'lt', 'gt', 'le']


class Cur:
    """Cursor over the ROM that pulls big-endian words as it decodes."""
    def __init__(self, data, pc):
        self.d = data
        self.pc = pc
        self.start = pc

    def w(self):
        v = struct.unpack('>H', self.d[self.pc:self.pc + 2])[0]
        self.pc += 2
        return v

    def sw(self):
        v = self.w()
        return v - 0x10000 if v & 0x8000 else v

    def l(self):
        return (self.w() << 16) | self.w()


def _idx(c):
    """Brief extension word for (d8,An,Xn) / (d8,PC,Xn)."""
    ext = c.w()
    reg = (ext >> 12) & 7
    kind = 'a' if ext & 0x8000 else 'd'
    size = '.l' if ext & 0x800 else '.w'
    disp = ext & 0xFF
    if disp & 0x80:
        disp -= 0x100
    return disp, f'{kind}{reg}{size}'


def ea(c, mode, reg, size='.w'):
    if mode == 0:
        return f'd{reg}'
    if mode == 1:
        return f'a{reg}'
    if mode == 2:
        return f'(a{reg})'
    if mode == 3:
        return f'(a{reg})+'
    if mode == 4:
        return f'-(a{reg})'
    if mode == 5:
        return f'({c.sw():d},a{reg})'
    if mode == 6:
        disp, ix = _idx(c)
        return f'({disp:d},a{reg},{ix})'
    if mode == 7:
        if reg == 0:
            return f'(${c.sw() & 0xFFFFFF:04X}).w'
        if reg == 1:
            return f'(${c.l():06X}).l'
        if reg == 2:
            d = c.sw()
            return f'(${(c.pc - 2 + d) & 0xFFFFFF:06X},pc)'
        if reg == 3:
            disp, ix = _idx(c)
            return f'({disp:d},pc,{ix})'
        if reg == 4:
            if size == '.l':
                return f'#${c.l():X}'
            v = c.w()
            if size == '.b':
                v &= 0xFF
            return f'#${v:X}'
    return '???'


def disasm_one(data, pc):
    """Returns (text, next_pc)."""
    c = Cur(data, pc)
    try:
        op = c.w()
    except Exception:
        return 'dc.w ????', pc + 2
    t = _decode(c, op)
    if t is None:
        return f'dc.w ${op:04X}', pc + 2
    return t, c.pc


def _decode(c, op):
    top = op >> 12
    m = (op >> 3) & 7
    r = op & 7

    # ---- MOVE / MOVEA ----
    if top in (1, 2, 3):
        sz = MOVE_SIZES[top]
        src = ea(c, m, r, sz)
        dm = (op >> 6) & 7
        dr = (op >> 9) & 7
        dst = ea(c, dm, dr, sz)
        return f'move{"a" if dm == 1 else ""}{sz} {src},{dst}'

    # ---- MOVEQ ----
    if top == 7 and not (op & 0x100):
        v = op & 0xFF
        if v & 0x80:
            v -= 0x100
        return f'moveq #{v},d{(op >> 9) & 7}'

    # ---- Bcc / BRA / BSR ----
    if top == 6:
        cc = (op >> 8) & 0xF
        disp = op & 0xFF
        if disp == 0:
            d = c.sw()
            tgt = c.start + 2 + d
        elif disp == 0xFF:
            d = c.l()
            tgt = c.start + 2 + d
        else:
            d = disp - 0x100 if disp & 0x80 else disp
            tgt = c.start + 2 + d
        name = 'bra' if cc == 0 else ('bsr' if cc == 1 else 'b' + CC[cc])
        return f'{name} ${tgt & 0xFFFFFF:06X}'

    # ---- ADDQ / SUBQ / Scc / DBcc ----
    if top == 5:
        if m == 1 and ((op >> 6) & 7) == 7:            # DBcc
            cc = (op >> 8) & 0xF
            d = c.sw()
            return f'db{CC[cc]} d{r},${(c.start + 2 + d) & 0xFFFFFF:06X}'
        if ((op >> 6) & 3) == 3:                        # Scc
            cc = (op >> 8) & 0xF
            return f's{CC[cc]} {ea(c, m, r, ".b")}'
        sz = SIZES[(op >> 6) & 3]
        n = (op >> 9) & 7 or 8
        name = 'subq' if op & 0x100 else 'addq'
        return f'{name}{sz} #{n},{ea(c, m, r, sz)}'

    # ---- bit ops / immediates ----
    if top == 0:
        if (op & 0xFF00) in (0x0000, 0x0200, 0x0400, 0x0600, 0x0A00, 0x0C00):
            names = {0x00: 'ori', 0x02: 'andi', 0x04: 'subi',
                     0x06: 'addi', 0x0A: 'eori', 0x0C: 'cmpi'}
            name = names[(op >> 8) & 0xFF]
            sz = SIZES.get((op >> 6) & 3)
            if sz is None:
                return None
            imm = ea(c, 7, 4, sz)
            return f'{name}{sz} {imm},{ea(c, m, r, sz)}'
        if op & 0x100:                                   # BTST/BCHG/BCLR/BSET Dn
            names = ['btst', 'bchg', 'bclr', 'bset']
            return f'{names[(op >> 6) & 3]} d{(op >> 9) & 7},{ea(c, m, r, ".b")}'
        if (op & 0xFF00) == 0x0800:
            names = ['btst', 'bchg', 'bclr', 'bset']
            bit = c.w()
            return f'{names[(op >> 6) & 3]} #{bit},{ea(c, m, r, ".b")}'
        return None

    # ---- misc (4xxx) ----
    if top == 4:
        if op == 0x4E71:
            return 'nop'
        if op == 0x4E75:
            return 'rts'
        if op == 0x4E73:
            return 'rte'
        if op == 0x4E77:
            return 'rtr'
        if (op & 0xFFF8) == 0x4E50:
            return f'link a{r},#{c.sw()}'
        if (op & 0xFFF8) == 0x4E58:
            return f'unlk a{r}'
        if (op & 0xFFC0) == 0x4E80:
            return f'jsr {ea(c, m, r)}'
        if (op & 0xFFC0) == 0x4EC0:
            return f'jmp {ea(c, m, r)}'
        if (op & 0xF1C0) == 0x41C0:
            return f'lea {ea(c, m, r, ".l")},a{(op >> 9) & 7}'
        if (op & 0xFFC0) == 0x4840:
            return f'swap d{r}' if m == 0 else f'pea {ea(c, m, r, ".l")}'
        if (op & 0xFFB8) == 0x4880:
            return f'ext{".w" if not (op & 0x40) else ".l"} d{r}'
        if (op & 0xFF80) == 0x4880 or (op & 0xFF80) == 0x4C80:
            # MOVEM
            sz = '.l' if op & 0x40 else '.w'
            mask = c.w()
            regs = _movem(mask, m == 4)
            body = ea(c, m, r, sz)
            return (f'movem{sz} {body},{regs}' if op & 0x400
                    else f'movem{sz} {regs},{body}')
        if (op & 0xFF00) in (0x4200, 0x4400, 0x4600, 0x4A00):
            names = {0x42: 'clr', 0x44: 'neg', 0x46: 'not', 0x4A: 'tst'}
            sz = SIZES.get((op >> 6) & 3)
            if sz is None:
                return None
            return f'{names[(op >> 8) & 0xFF]}{sz} {ea(c, m, r, sz)}'
        if (op & 0xFFF0) == 0x4E40:
            return f'trap #{op & 0xF}'
        return None

    # ---- 8/9/B/C/D: OR SUB CMP/EOR AND ADD ----
    if top in (8, 9, 0xB, 0xC, 0xD):
        names = {8: 'or', 9: 'sub', 0xB: 'cmp', 0xC: 'and', 0xD: 'add'}
        name = names[top]
        dn = (op >> 9) & 7
        opmode = (op >> 6) & 7
        # Must precede the opmode 3 / 7 blocks below: those call ea() to
        # decode suba/cmpa/adda, which advances the cursor past the operand.
        # Testing for the multiply afterwards would decode the NEXT word as
        # the immediate - which is how mulu.w #$000C became mulu.w #$321F.
        if top == 0xC and opmode in (3, 7):
            nm = 'mulu' if opmode == 3 else 'muls'
            return f'{nm}.w {ea(c, m, r, ".w")},d{dn}'
        if top == 8 and opmode in (3, 7):
            nm = 'divu' if opmode == 3 else 'divs'
            return f'{nm}.w {ea(c, m, r, ".w")},d{dn}'
        if opmode == 3:
            src = ea(c, m, r, '.w')
            if top == 9:
                return f'suba.w {src},a{dn}'
            if top == 0xB:
                return f'cmpa.w {src},a{dn}'
            if top == 0xD:
                return f'adda.w {src},a{dn}'
        if opmode == 7:
            src = ea(c, m, r, '.l')
            if top == 9:
                return f'suba.l {src},a{dn}'
            if top == 0xB:
                return f'cmpa.l {src},a{dn}'
            if top == 0xD:
                return f'adda.l {src},a{dn}'
        # Group 8 and C reuse opmode 3/7 for the word multiply/divide, and
        # opmode 4-6 for ABCD/SBCD/EXG. Decoding those as or/and produces
        # plausible-looking garbage and silently derails everything after,
        # which is exactly how $06AE86 was misread as `ori.b #$1F,a4`.
        if top in (8, 0xC) and opmode == 4 and m in (0, 1):
            nm = 'abcd' if top == 0xC else 'sbcd'
            return (f'{nm} d{r},d{dn}' if m == 0
                    else f'{nm} -(a{r}),-(a{dn})')
        if top == 0xC and opmode == 5 and m == 0:
            return f'exg d{dn},d{r}'
        if top == 0xC and opmode == 5 and m == 1:
            return f'exg a{dn},a{r}'
        if top == 0xC and opmode == 6 and m == 1:
            return f'exg d{dn},a{r}'
        sz = SIZES.get(opmode & 3)
        if sz is None:
            return None
        if top == 0xB and (opmode & 4):
            if m == 1:
                return f'cmpm{sz} (a{r})+,(a{dn})+'
            return f'eor{sz} d{dn},{ea(c, m, r, sz)}'
        if opmode & 4:
            return f'{name}{sz} d{dn},{ea(c, m, r, sz)}'
        return f'{name}{sz} {ea(c, m, r, sz)},d{dn}'

    # ---- E: shifts / rotates ----
    if top == 0xE:
        dirs = 'lr'
        kinds = ['as', 'ls', 'rox', 'ro']
        if ((op >> 6) & 3) == 3:                        # memory shift, 1 bit
            kind = kinds[(op >> 9) & 3]
            d = 'l' if op & 0x100 else 'r'
            return f'{kind}{d}.w {ea(c, m, r, ".w")}'
        sz = SIZES[(op >> 6) & 3]
        kind = kinds[(op >> 3) & 3]
        d = 'l' if op & 0x100 else 'r'
        cnt = (op >> 9) & 7
        if op & 0x20:
            return f'{kind}{d}{sz} d{cnt},d{r}'
        return f'{kind}{d}{sz} #{cnt or 8},d{r}'

    return None


def _movem(mask, predec):
    names = [f'd{i}' for i in range(8)] + [f'a{i}' for i in range(8)]
    bits = [(mask >> i) & 1 for i in range(16)]
    if predec:
        bits = bits[::-1]
    sel = [names[i] for i in range(16) if bits[i]]
    return '/'.join(sel) if sel else '-'


def disasm(data, pc, n=32, labels=None):
    out = []
    for _ in range(n):
        if pc + 2 > len(data):
            break
        text, nxt = disasm_one(data, pc)
        raw = data[pc:nxt].hex()
        tag = ''
        if labels and pc in labels:
            tag = f'  ; {labels[pc]}'
        out.append(f'{pc:06X}  {raw:<20} {text}{tag}')
        pc = nxt
    return '\n'.join(out)
