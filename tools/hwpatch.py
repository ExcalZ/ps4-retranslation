"""Half-width text rendering patch.

The dialogue renderers draw one 16x16 glyph per cell and wrap at 16 columns,
then at 2 rows. Sixteen characters a line is fine for Japanese and hopeless for
English. This patch makes d1 count HALF cells (0..31) so an 8-pixel glyph
occupies half a cell: 32 characters per line.

Two renderers, not one
----------------------
The glyph pipeline ($06A9FA select, $06AA30 expand, $06AA7E send) has TWO
callers:

    $06AE32  dispatch table of mostly bare rts
    $06A1A6  real handlers for all 16 controls  <- ordinary dialogue

Patching only the first leaves normal dialogue rendering stock, which looks
like 8-pixel glyphs double-spaced inside 16-pixel cells. Both are patched here.

d4 is a mode flag
-----------------
When d4 is zero the expander stages one glyph at $FFFF7000 and each cell is
DMA'd immediately ($FFFF7000 >> 1 == $7FFFB800, the constant $06AA7E uses).
When d4 is non-zero it writes into a whole-page buffer at
$FFFF7000 + d1*128 + d2*2048 and nothing is sent until the page is finished,
at which point $06AAA4 ships all $800 bytes at once. Renderer 2 also skips its
per-cell DMA in that mode. An earlier version of this patch forced d4 = 0,
which would have corrupted the page-buffer mode.

Cell geometry
-------------
A cell is four 8x8 tiles at buffer offsets 0/32/64/96 (TL TR BL BR), so the
left half is 0+64 and the right half is 32+96. A half-width glyph lives in the
LEFT half of its 16x16 font cell: source bytes 0-7 and 16-23.

Width is data-driven
--------------------
A 28-byte bitmap covers codes $00-$DF, one bit each, MSB first; a set bit means
half-width. Kanji ($E0-$EF) are always full-width. The table ships all zero, so
a freshly patched ROM renders exactly as before.
"""

# ---------------------------------------------------------------- layout
# $0E7130-$0E7FFF is $FF filler at a bank boundary (3792 bytes).
TBL  = 0x0E7140           # 28-byte width bitmap
CODE = 0x0E7160           # patch code

CALLSITE      = 0x06AE4A  # renderer 1: draw sequence
CALLSITE_END  = 0x06AE6E
CALLSITE2     = 0x06A1BE  # renderer 2: draw sequence + advance
CALLSITE2_END = 0x06A1F0

GLYPH_SEL = 0x06A9FA      # -> a1 = glyph source; advances a0 past a kanji
EXPAND    = 0x06AA30      # 1bpp -> 4bpp, whole cell
DMA_CELL  = 0x06AA7E      # queue DMA of the staged cell; uses d1 (col), d2 (row)
PAGE      = 0x06B056      # renderer 1: page / wait handler
CONT      = 0x06AE6E      # renderer 1: inter-character delay
R2_CONT   = 0x06A1F0      # renderer 2: after the advance
R2_F5     = 0x06A3B4      # renderer 2: $F5 at end of line
R2_PAGE   = 0x06A4D8      # renderer 2: page handler
STAGING   = 0xFFFF7000

# renderer 3: the narration/full-screen renderer at $06AAC4. It has its own
# pipeline - it expands straight into a whole-line buffer at $FFFF0000 with
# $06AD70 and flushes with $06ADB4 - so it needs its own draw routine rather
# than the staging/DMA one the other two share. Eighteen callers reach it, most
# of them still Japanese, which is why width stays table-driven here too.
# $0E7300-$0E745F belongs to relocate.py (stream remap code + table),
# so renderer 3 sits above it with room for that table to grow.
NCODE      = 0x0E7500     # renderer 3 draw routine
NBUF       = 0xFFFF0000   # whole-line cell buffer, cleared per line at $06ABB2
SEND_FULL  = 0x06AD70     # stock full-cell expander: a1 = source, d1 = CELL
CALLSITE3     = 0x06AAFA
CALLSITE3_END = 0x06AB24  # $06AB24 is a branch target; must stay intact
R3_LOOP    = 0x06AAE2     # top of the character loop
R3_FLUSH   = 0x06AB24     # end-of-line: bra $06ADB4
R3_PERCHAR = 0x06ADB4     # flush; DMAs ($FFED5A) CELLS worth of buffer
ED5A       = 0xED5A       # renderer 3 column counter -> flush length
COUNTER   = 0xED5B        # renderer 1's glyph counter, drives its hold delay
BLANK     = 0xEEEEEEEE    # eight pixels in the OFF colour ($E)

D0, D1, D2, D3, D4, D5, D6, D7 = range(8)
A0, A1, A2 = 0, 1, 2

# movem masks. -(An) stores the list reversed: bit0=a7 .. bit7=a0, bit8=d7 ..
# bit15=d0. (An)+ uses the natural order: bit0=d0 .. bit15=a7.
PUSH_MASK = (1 << 12) | (1 << 11) | (1 << 10) | (1 << 9) | (1 << 8) | (1 << 6) | (1 << 5)
POP_MASK  = (1 << 3) | (1 << 4) | (1 << 5) | (1 << 6) | (1 << 7) | (1 << 9) | (1 << 10)


class Asm:
    """Two-pass assembler for the forms this patch needs.

    Encodings are not taken on trust: the build script disassembles the result
    with m68k.py so it can be read back and compared against intent.
    """

    def __init__(self, org):
        self.org = org
        self.items = []
        self.labels = {}
        self.pc = org

    def _raw(self, *words):
        b = b''.join(w.to_bytes(2, 'big') for w in words)
        self.items.append((len(b), lambda L, b=b: b))
        self.pc += len(b)

    def label(self, name):
        if name in self.labels:
            raise ValueError('duplicate label ' + name)
        self.labels[name] = self.pc

    def _rel(self, op, target):
        addr = self.pc

        def emit(L, op=op, target=target, addr=addr):
            disp = L[target] - (addr + 2)
            if not -0x8000 <= disp <= 0x7FFF:
                raise ValueError('branch out of range: ' + target)
            return bytes([op, 0]) + (disp & 0xFFFF).to_bytes(2, 'big')
        self.items.append((4, emit))
        self.pc += 4

    # ---- instructions -------------------------------------------------
    def movem_push(self, m):        self._raw(0x48E7, m)
    def movem_pop(self, m):         self._raw(0x4CDF, m)
    def push_a0(self):              self._raw(0x2F08)
    def push_d0_w(self):            self._raw(0x3F00)
    def push_d1_w(self):            self._raw(0x3F01)
    def pop_d0_w(self):             self._raw(0x301F)
    def pop_d1_w(self):             self._raw(0x321F)
    def pop_a0_l(self):             self._raw(0x205F)
    def moveq(self, n, r):          self._raw(0x7000 | (r << 9) | (n & 0xFF))
    def move_l_imm(self, v, r):     self._raw(0x203C | (r << 9),
                                              (v >> 16) & 0xFFFF, v & 0xFFFF)
    def move_w_dd(self, s, d):      self._raw(0x3000 | (d << 9) | s)
    def move_b_idx(self, an, ix, dn):
        self._raw(0x1000 | (dn << 9) | 0x30 | an, (ix << 12))
    def move_b_postinc(self, an, dn):
        self._raw(0x1000 | (dn << 9) | 0x18 | an)
    def move_l_postinc(self, dn, an):
        self._raw(0x2000 | (an << 9) | 0xC0 | dn)
    def add_w_dd(self, s, d):       self._raw(0xD040 | (d << 9) | s)
    def cmpi_w(self, v, r):         self._raw(0x0C40 | r, v)
    def cmpi_b_ind(self, v, an):    self._raw(0x0C10 | an, v & 0xFF)
    def andi_w(self, v, r):         self._raw(0x0240 | r, v)
    def eori_w(self, v, r):         self._raw(0x0A40 | r, v)
    def ori_b(self, v, r):          self._raw(0x0000 | r, v & 0xFF)
    def addq_w(self, n, r):         self._raw(0x5040 | ((n & 7) << 9) | r)
    def addq_b(self, n, r):         self._raw(0x5000 | ((n & 7) << 9) | r)
    def addq_l_sp(self, n):         self._raw(0x508F | ((n & 7) << 9))
    def subq_l_an(self, n, r):      self._raw(0x5188 | ((n & 7) << 9) | r)
    def addq_b_absw(self, n, a):    self._raw(0x5038 | ((n & 7) << 9), a)
    def move_b_absw(self, r, a):    self._raw(0x11C0 | r, a)
    def tst_w(self, r):             self._raw(0x4A40 | r)
    def btst_imm(self, bit, r):     self._raw(0x0800 | r, bit)
    def btst_dd(self, s, d):        self._raw(0x0100 | (s << 9) | d)
    def lea_abs(self, addr, an):    self._raw(0x41F9 | (an << 9),
                                              (addr >> 16) & 0xFFFF, addr & 0xFFFF)
    def lea_disp(self, d, src, dst):self._raw(0x41E8 | (dst << 9) | src, d & 0xFFFF)
    def lea_idx(self, src, ix, dst):self._raw(0x41F0 | (dst << 9) | src, (ix << 12))
    def lsr_w(self, n, r):          self._raw(0xE048 | ((n & 7) << 9) | r)
    def lsl_w(self, n, r):          self._raw(0xE148 | ((n & 7) << 9) | r)
    def lsl_l(self, n, r):          self._raw(0xE188 | ((n & 7) << 9) | r)
    def lsl_b(self, n, r):          self._raw(0xE108 | ((n & 7) << 9) | r)
    def jsr_abs(self, a):           self._raw(0x4EB9, (a >> 16) & 0xFFFF, a & 0xFFFF)
    def cmpa_l_ind(self, src, dst):  self._raw(0xB1D0 | (dst << 9) | src)
    def movea_l_disp(self, d, src, dst):
        self._raw(0x2068 | (dst << 9) | src, d & 0xFFFF)
    def subq_l_sp(self, n):         self._raw(0x518F | ((n & 7) << 9))
    def move_b_postinc_disp_sp(self, d):
        self._raw(0x1F58, d & 0xFFFF)   # move.b (a0)+,(d,a7)
    def jmp_abs(self, a):           self._raw(0x4EF9, (a >> 16) & 0xFFFF, a & 0xFFFF)
    def rts(self):                  self._raw(0x4E75)
    def nop(self):                  self._raw(0x4E71)

    def dbf(self, r, target):
        addr = self.pc

        def emit(L, r=r, target=target, addr=addr):
            disp = L[target] - (addr + 2)
            return (0x51C8 | r).to_bytes(2, 'big') + (disp & 0xFFFF).to_bytes(2, 'big')
        self.items.append((4, emit))
        self.pc += 4

    def bra(self, t): self._rel(0x60, t)
    def bsr(self, t): self._rel(0x61, t)
    def bcc(self, t): self._rel(0x64, t)
    def bne(self, t): self._rel(0x66, t)
    def beq(self, t): self._rel(0x67, t)

    def build(self):
        out = bytearray()
        for size, emit in self.items:
            b = emit(self.labels)
            assert len(b) == size, (len(b), size)
            out += b
        return bytes(out)


def assemble():
    """Draw one glyph, advance the column, report whether the line wrapped.

    entry: d0.w = code, d1.w = half-column, d2.w = row, d4.w = mode,
           a0 = script pointer
    exit : d0.w = 1 if the column wrapped to 0, else 0; d1 advanced.
           d2 is untouched - each renderer does its own row/page handling,
           and they do it differently.
    """
    a = Asm(CODE)

    a.movem_push(PUSH_MASK)
    a.push_a0()
    a.push_d0_w()

    # ---- width -> d3 (1 = half, 0 = full). d4 must survive: it is the mode.
    a.moveq(0, D3)
    a.cmpi_w(0xE0, D0)
    a.bcc('align')
    a.move_w_dd(D0, D5)
    a.lsr_w(3, D5)
    a.lea_abs(TBL, A1)
    a.move_b_idx(A1, D5, D6)
    a.move_w_dd(D0, D5)
    a.andi_w(7, D5)
    a.eori_w(7, D5)
    a.btst_dd(D5, D6)
    a.beq('align')
    a.moveq(1, D3)

    # ---- a full-width glyph must start on an even half-column ----
    a.label('align')
    a.tst_w(D3)
    a.bne('fetch')
    a.btst_imm(0, D1)
    a.beq('fetch')
    a.addq_w(1, D1)
    a.andi_w(0x1F, D1)
    a.bne('fetch')
    a.addq_l_sp(2)
    a.pop_a0_l()
    a.subq_l_an(1, A0)               # rewind onto the code byte
    a.movem_pop(POP_MASK)
    a.moveq(1, D0)                   # report the wrap, draw nothing
    a.rts()

    a.label('fetch')
    a.pop_d0_w()
    a.addq_l_sp(4)
    a.jsr_abs(GLYPH_SEL)
    a.tst_w(D3)
    a.beq('full')

    # ---- half width ----
    a.lea_abs(STAGING, A2)
    a.tst_w(D4)
    a.beq('nooff')
    a.move_w_dd(D1, D5)              # page-buffer mode: add the cell offset
    a.lsr_w(1, D5)
    a.lsl_w(7, D5)                   # cell * 128
    a.move_w_dd(D2, D6)
    a.lsl_w(8, D6)
    a.lsl_w(3, D6)                   # row * 2048
    a.add_w_dd(D6, D5)
    a.lea_idx(A2, D5, A2)
    a.label('nooff')
    a.move_w_dd(D1, D5)
    a.andi_w(1, D5)
    a.lsl_w(5, D5)                   # 0 = left half, 32 = right half
    a.tst_w(D5)
    a.bne('noclear')
    # a fresh cell: blank its right half or the previous glyph lingers there
    a.move_l_imm(BLANK, D7)
    a.lea_disp(32, A2, A2)
    a.moveq(7, D6)
    a.label('clr1')
    a.move_l_postinc(D7, A2)
    a.dbf(D6, 'clr1')
    a.lea_disp(32, A2, A2)
    a.moveq(7, D6)
    a.label('clr2')
    a.move_l_postinc(D7, A2)
    a.dbf(D6, 'clr2')
    a.lea_disp(-128, A2, A2)         # back to the start of the cell
    a.label('noclear')
    a.lea_idx(A2, D5, A2)
    a.bsr('expand8')                 # top tile:    source bytes 0-7
    a.lea_disp(8, A1, A1)
    a.lea_disp(32, A2, A2)
    a.bsr('expand8')                 # bottom tile: source bytes 16-23
    a.bra('send')

    # ---- full width: stock expander, which wants a CELL column in d1 ----
    a.label('full')
    a.push_d1_w()
    a.lsr_w(1, D1)
    a.jsr_abs(EXPAND)
    a.pop_d1_w()

    # ---- send, unless the caller is building a whole page ----
    a.label('send')
    a.tst_w(D4)
    a.bne('nodma')
    a.push_d1_w()
    a.lsr_w(1, D1)
    a.jsr_abs(DMA_CELL)
    a.pop_d1_w()

    a.label('nodma')
    a.tst_w(D3)
    a.bne('adv1')
    a.addq_w(2, D1)
    a.bra('wrap')
    a.label('adv1')
    a.addq_w(1, D1)
    a.label('wrap')
    a.andi_w(0x1F, D1)
    a.movem_pop(POP_MASK)
    a.moveq(0, D0)
    a.tst_w(D1)
    a.bne('done')
    a.moveq(1, D0)
    a.label('done')
    a.rts()

    # ---- expand8: a1 = 8 source bytes -> a2 = one 8x8 4bpp tile ----
    # Seeds each row with the OFF colour $E and bumps it to $F where a bit is
    # set, rather than holding both colours in registers: d4 is the mode and
    # d1/d2 belong to the caller, so registers are scarce.
    a.label('expand8')
    a.moveq(7, D5)
    a.label('byteloop')
    a.move_b_postinc(A1, D6)
    a.moveq(7, D0)
    a.moveq(0, D7)
    a.label('bitloop')
    a.lsl_l(4, D7)
    a.ori_b(0x0E, D7)
    a.lsl_b(1, D6)
    a.bcc('bitnext')
    a.addq_b(1, D7)
    a.label('bitnext')
    a.dbf(D0, 'bitloop')
    a.move_l_postinc(D7, A2)
    a.dbf(D5, 'byteloop')
    a.rts()
    return a


NOP = b'\x4e\x71'


def callsite1():
    """Renderer 1: draw, bump the hold-delay counter, then the row logic."""
    a = Asm(CALLSITE)
    a.jsr_abs(CODE)
    a.addq_b_absw(1, COUNTER)
    a.tst_w(D0)
    a.beq('cont')
    a.addq_w(1, D2)
    a.andi_w(1, D2)
    a.beq('page')
    a.bra('cont')
    a.labels['page'] = PAGE
    a.labels['cont'] = CONT
    body = a.build()
    pad = (CALLSITE_END - CALLSITE) - len(body)
    if pad < 0:
        raise ValueError('renderer 1 patch does not fit')
    return body + NOP * (pad // 2)


def callsite2():
    """Renderer 2: draw, then its original end-of-line logic.

    The $F5 test must stay ahead of the row increment - a $F5 at the end of a
    line branches away WITHOUT advancing the row.
    """
    a = Asm(CALLSITE2)
    a.jsr_abs(CODE)
    a.tst_w(D0)
    a.beq('cont')
    a.cmpi_b_ind(0xF5, A0)
    a.bne('rowinc')
    a.lea_disp(1, A0, A0)
    a.bra('f5')
    a.label('rowinc')
    a.addq_w(1, D2)
    a.andi_w(1, D2)
    a.beq('page')
    a.bra('cont')
    a.labels['cont'] = R2_CONT
    a.labels['f5'] = R2_F5
    a.labels['page'] = R2_PAGE
    body = a.build()
    pad = (CALLSITE2_END - CALLSITE2) - len(body)
    if pad < 0:
        raise ValueError(f'renderer 2 patch needs {len(body)} bytes, '
                         f'{CALLSITE2_END - CALLSITE2} available')
    return body + NOP * (pad // 2)


def narration_code():
    """Renderer 3: draw one glyph into the whole-line buffer at $FFFF0000.

    entry: d0.w = code, d1.w = half-column, d4.w = mode, a0 = script pointer
    exit : d0.w = 1 if the column wrapped to 0, else 0; d1 advanced;
           ($FFED5A) = cells occupied, which is what the flush uses as its
           DMA length.

    ($FFED5A) must count CELLS, not half-columns. The terminator flushes a
    partly filled line, so it is rounded UP - a half-filled final cell still
    has to be transferred or the last character loses its bottom half.

    The off colour here is 0, not the $E the staging renderers use: $06AD70
    builds its pixels from $F and $0, and the line buffer is zero-filled.
    """
    a = Asm(NCODE)
    a.movem_push(PUSH_MASK)
    a.push_a0()
    a.push_d0_w()

    # ---- width -> d3 (1 = half, 0 = full) ----
    a.moveq(0, D3)
    a.cmpi_w(0xE0, D0)
    a.bcc('align')
    a.move_w_dd(D0, D5)
    a.lsr_w(3, D5)
    a.lea_abs(TBL, A1)
    a.move_b_idx(A1, D5, D6)
    a.move_w_dd(D0, D5)
    a.andi_w(7, D5)
    a.eori_w(7, D5)
    a.btst_dd(D5, D6)
    a.beq('align')
    a.moveq(1, D3)

    # ---- a full-width glyph must start on an even half-column ----
    a.label('align')
    a.tst_w(D3)
    a.bne('fetch')
    a.btst_imm(0, D1)
    a.beq('fetch')
    a.addq_w(1, D1)
    a.andi_w(0x1F, D1)
    a.bne('fetch')
    a.addq_l_sp(2)
    a.pop_a0_l()
    a.subq_l_an(1, A0)               # rewind onto the code byte
    a.movem_pop(POP_MASK)
    a.moveq(16, D0)                  # the line is full: 16 cells to flush
    a.move_b_absw(D0, ED5A)
    a.moveq(1, D0)
    a.rts()

    a.label('fetch')
    a.pop_d0_w()
    a.addq_l_sp(4)
    a.jsr_abs(GLYPH_SEL)
    a.tst_w(D3)
    a.beq('full')

    # ---- half width: left half of the glyph into half-cell d1 ----
    a.lea_abs(NBUF, A2)
    a.move_w_dd(D1, D5)
    a.lsr_w(1, D5)
    a.lsl_w(7, D5)                   # cell * 128
    a.lea_idx(A2, D5, A2)
    a.move_w_dd(D1, D5)
    a.andi_w(1, D5)
    a.lsl_w(5, D5)                   # 0 = TL/BL, 32 = TR/BR
    a.lea_idx(A2, D5, A2)
    a.bsr('expandn')                 # source bytes 0-7  -> top tile
    a.lea_disp(8, A1, A1)
    a.lea_disp(32, A2, A2)
    a.bsr('expandn')                 # source bytes 16-23 -> bottom tile
    a.bra('adv')

    # ---- full width: stock expander, which wants a CELL column in d1 ----
    a.label('full')
    a.push_d1_w()
    a.lsr_w(1, D1)
    a.jsr_abs(SEND_FULL)
    a.pop_d1_w()

    a.label('adv')
    a.tst_w(D3)
    a.bne('adv1')
    a.addq_w(2, D1)
    a.bra('cells')
    a.label('adv1')
    a.addq_w(1, D1)
    a.label('cells')
    a.move_w_dd(D1, D5)              # cells = (half-columns + 1) >> 1,
    a.addq_w(1, D5)                  # taken BEFORE the wrap so a full line
    a.lsr_w(1, D5)                   # reads 16 rather than 0
    a.move_b_absw(D5, ED5A)
    a.andi_w(0x1F, D1)
    a.movem_pop(POP_MASK)
    a.moveq(0, D0)
    a.tst_w(D1)
    a.bne('done')
    a.moveq(1, D0)
    a.label('done')
    a.rts()

    # ---- expandn: a1 = 8 source bytes -> a2 = one 8x8 4bpp tile ----
    a.label('expandn')
    a.moveq(7, D5)
    a.label('nbyte')
    a.move_b_postinc(A1, D6)
    a.moveq(7, D0)
    a.moveq(0, D7)
    a.label('nbit')
    a.lsl_l(4, D7)
    a.lsl_b(1, D6)
    a.bcc('nnext')
    a.ori_b(0x0F, D7)
    a.label('nnext')
    a.dbf(D0, 'nbit')
    a.move_l_postinc(D7, A2)
    a.dbf(D5, 'nbyte')
    a.rts()
    return a


def callsite3():
    """Renderer 3: draw, then its original end-of-line logic.

    $06AB24 is left untouched - the control-code table branches to it.
    """
    a = Asm(CALLSITE3)
    a.jsr_abs(NCODE)
    a.tst_w(D0)
    a.bne('flush')
    a.tst_w(D4)
    a.bne('loop')
    a.bsr('perchar')
    a.bra('loop')
    a.labels['flush'] = R3_FLUSH
    a.labels['loop'] = R3_LOOP
    a.labels['perchar'] = R3_PERCHAR
    body = a.build()
    pad = (CALLSITE3_END - CALLSITE3) - len(body)
    if pad < 0:
        raise ValueError(f'renderer 3 patch needs {len(body)} bytes, '
                         f'{CALLSITE3_END - CALLSITE3} available')
    return body + NOP * (pad // 2)


def apply(rom: bytes):
    out = bytearray(rom)
    code = assemble().build()
    ncode = narration_code().build()
    s1, s2, s3 = callsite1(), callsite2(), callsite3()
    if CODE + len(code) > NCODE:
        raise ValueError('renderer 1/2 code runs into the renderer 3 routine')
    for off, blob in ((TBL, bytes(28)), (CODE, code), (NCODE, ncode),
                      (CALLSITE, s1), (CALLSITE2, s2), (CALLSITE3, s3)):
        out[off:off + len(blob)] = blob
    return bytes(out), {'code_bytes': len(code), 'code_at': CODE,
                        'table_at': TBL, 'callsite_bytes': len(s1),
                        'callsite2_bytes': len(s2),
                        'ncode_bytes': len(ncode), 'ncode_at': NCODE,
                        'callsite3_bytes': len(s3)}


def free_space_ok(rom: bytes) -> str:
    code = assemble().build()
    end = NCODE + len(narration_code().build())
    if set(rom[TBL:end]) - {0xFF}:
        return f'REFUSING: {TBL:06X}-{end - 1:06X} is not all $FF filler'
    return f'{TBL:06X}-{end - 1:06X} is $FF filler, {end - TBL} bytes'


def set_widths(rom: bytes, codes) -> bytes:
    out = bytearray(rom)
    for c in codes:
        if not 0 <= c <= 0xDF:
            raise ValueError(f'code ${c:02X} outside the single-byte range')
        out[TBL + (c >> 3)] |= 0x80 >> (c & 7)
    return bytes(out)


def read_widths(rom: bytes):
    return [c for c in range(0xE0)
            if rom[TBL + (c >> 3)] & (0x80 >> (c & 7))]
