"""Menu VWF: ROM font table, and the RAM/VRAM budget it composes into.

The face is `vwffont`. This module lays it out for the 68000 and records the
addresses the assembly depends on.

Font table
----------
256 entries of EIGHT bytes at `FONT_BASE`:

    +0      advance width in pixels (0 = not drawable, treated as a space)
    +1..+5  five 1bpp rows, MSB = leftmost pixel, matching rows 3-7 of the cell
    +6,+7   padding

Eight bytes, not six, so a code indexes with `lsl.l #3` instead of a multiply -
the routine runs per character, and a `mulu` is 38+ cycles against 8 for a
shift. The 1 KB wasted is meaningless in the fourth megabyte.

The table is flat over the whole byte range so the composer needs no mapping
logic at all: lowercase ($01-$1A), the small-caps uppercase the menus actually
store ($80-$99) and digits ($9A-$A3) all point at the same glyphs, because the
face IS small caps. Codes with no glyph get width 0 and blank rows.

Where things live
-----------------
FONT_BASE is in the fourth megabyte, which exists only in an expanded ROM (see
expand.py) and is clear of the SRAM overlay at $200001-$203FFF.

SCRATCH is work RAM for composition. $FF5341-$FF5FFF is quiet in all eight
captured savestates - five battle moments, the opening cutscene, and two
idle-boot states, across both the Japanese and the English builds - and the
disassembly declares no symbol inside it: the nearest are `Sound_Index`
($FF500A) below and `Chunk_Table` ($FF6000) above. Basing at $FF5800 leaves
about 1.2 KB of margin below in case the sound driver reaches further than
those states show, and 2 KB above.

This is evidence, not proof. RAM quiet across eight moments can still be live
in a ninth, and the honest test is a write-watchpoint on the region during a
long play session.
"""
import vwffont

FONT_BASE = 0x300000          # fourth megabyte
ENTRY = 8                     # bytes per glyph entry
TABLE_BYTES = 256 * ENTRY     # 2048

SCRATCH = 0xFF5800            # 1bpp composition buffer
SCRATCH_ROWS = 7          # rows 1-7 of the cell; row 0 is always paper
SCRATCH_STRIDE = 12           # bytes per row -> 96 px, 12 cells
SCRATCH_BYTES = SCRATCH_ROWS * SCRATCH_STRIDE          # 84

# One slot per POOL tile, NOT one shared staging buffer. $0420D6 only QUEUES a
# transfer; the copy happens in vblank. With a single buffer every queued DMA
# reads whatever the last draw left there, so a window of four names rendered
# the last name into all four rows. Each draw now owns the slice matching the
# tiles it allocated, so its source is still intact when the queue drains.
TILES = SCRATCH + 0x80        # 4bpp output, 32 bytes per POOL tile
TILES_MAX = 40                # SLOT_PERIOD * TILES_PER_ROW, see below
TILES_BYTES = TILES_MAX * 32                           # 1280

INK, PAPER = 0xF, 0xE         # matches the stock font tiles exactly


def _rows_to_bytes(ch):
    """The five 1bpp rows of `ch`, MSB leftmost."""
    rows = vwffont.G[ch]
    out = []
    for r in rows:
        b = 0
        for i, p in enumerate(r):
            if p == '#':
                b |= 0x80 >> i
        out.append(b)
    return out


def glyphs():
    """{code: (top_row, rows)} for every code the menu encoders can emit.

    Three sets share the byte range, so the renderer needs no case logic - the
    encoder picks the code and the glyph follows:

        $01-$1A   small caps      rows 3-7
        $1C-$35   true lowercase  x-height 4-7, ascenders from 2
        $80-$99   true capitals   rows 2-7

    $1C-$35 are the codes the ligature set used to occupy. The VWF made those
    unnecessary, which is exactly what freed the room for a third alphabet.
    """
    import vwffont, vwfcase
    m = {}
    for i, c in enumerate('abcdefghijklmnopqrstuvwxyz'):
        m[0x01 + i] = (vwffont.TOP, vwffont.G[c])          # small caps
        m[0x1C + i] = vwfcase.LOW[c]                       # true lowercase
        m[0x80 + i] = vwfcase.CAPS[c]                      # true capitals
    m[0x1B] = (vwffont.TOP, vwffont.G['ü'])
    m[0x36] = vwfcase.LOW['ü']
    for i, c in enumerate('0123456789'):
        m[0x9A + i] = (vwffont.TOP, vwffont.G[c])
        m[0xA4 + i] = (vwffont.TOP, vwffont.G[c])
    for code, c in ((0xAE, "'"), (0xAF, ':'), (0xB0, '-'), (0xB1, '.'),
                    (0xB2, ','), (0xB3, '('), (0xB4, '.'), (0xB5, '!')):
        m[code] = (vwffont.TOP, vwffont.G[c])
    return m


def table():
    """The 2048-byte font table: [width, rows 1..7] per code."""
    import vwffont
    buf = bytearray(TABLE_BYTES)
    for code, (top, rows) in glyphs().items():
        off = code * ENTRY
        buf[off] = max(len(r) for r in rows)
        for dy, r in enumerate(rows):
            y = top + dy
            if not 1 <= y <= 7:
                raise ValueError(f'code ${code:02X}: row {y} outside 1-7')
            b = 0
            for i, p in enumerate(r):
                if p == '#':
                    b |= 0x80 >> i
            buf[off + y] = b            # +1..+7 are cell rows 1..7
    buf[0x00 * ENTRY] = vwffont.SPACE
    return bytes(buf)


def advance(code):
    """Advance width of one code, from the built table."""
    return table()[code * ENTRY]


def cells_for(encoded: bytes, gap: int = 1) -> int:
    """Cells a run of ENCODED bytes occupies - encoding-aware, unlike
    vwffont.cells, which assumes everything is a small cap."""
    t = table()
    ws = [t[b * ENTRY] for b in encoded if t[b * ENTRY]]
    if not ws:
        return 1
    px = sum(ws) + gap * (len(ws) - 1)
    return max(1, -(-px // 8))


def install(rom: bytes, base: int = FONT_BASE) -> bytes:
    """Write the font table, refusing to overwrite anything but filler."""
    if len(rom) < base + TABLE_BYTES:
        raise ValueError(f'rom is {len(rom):#x}; {base:#x} needs an expanded '
                         f'image - run `ps4tool.py expand` first')
    span = rom[base:base + TABLE_BYTES]
    if any(b != 0xFF for b in span):
        raise ValueError(f'{base:06X} is not $FF filler; refusing to overwrite')
    out = bytearray(rom)
    out[base:base + TABLE_BYTES] = table()
    return bytes(out)


def read_glyph(rom: bytes, code: int, base: int = FONT_BASE):
    """(width, rows) back out of an installed table - the round-trip check."""
    off = base + code * ENTRY
    return rom[off], list(rom[off + 1:off + 6])


# ------------------------------------------------------------ the composer

CODE_BASE = 0x300800          # after the font table, still in the fourth MB


class Asm(__import__('hwpatch').Asm):
    """hwpatch's assembler plus the handful of encodings the composer needs."""

    def clr_l_postinc(self, an):     self._raw(0x4298 | an)
    def adda_w_dn(self, dn, an):     self._raw(0xD0C0 | (an << 9) | dn)
    def movea_l_an(self, src, dst):  self._raw(0x2048 | (dst << 9) | src)
    def lsr_w_dn(self, cnt, dn):     self._raw(0xE068 | (cnt << 9) | dn)
    def or_b_ind(self, dn, an):      self._raw(0x8110 | (dn << 9) | an)
    def or_b_disp(self, dn, d, an):  self._raw(0x8128 | (dn << 9) | an,
                                               d & 0xFFFF)
    def subq_w(self, n, dn):         self._raw(0x5140 | ((n & 7) << 9) | dn)
    def bcs(self, t):                self._rel(0x65, t)
    def cmpi_b_imm(self, v, dn):     self._raw(0x0C00 | dn, v & 0xFF)
    def bhi(self, t):                self._rel(0x62, t)
    def tst_w_short(self, addr):     self._raw(0x4A78, addr & 0xFFFF)
    def move_l_an_dn(self, an, dn):  self._raw(0x2008 | (dn << 9) | an)
    def lsr_l(self, n, dn):
        # Immediate shift counts are 1-8 (8 encoded as 0). `n & 7` silently
        # turns 9 into 1, which is how a hash ended up XORing a value with
        # itself and filing every draw under slot 0.
        if not 1 <= n <= 8:
            raise ValueError(f'lsr.l #{n} is not encodable; use two shifts')
        self._raw(0xE088 | ((n & 7) << 9) | dn)
    def subi_w(self, v, dn):         self._raw(0x0440 | dn, v & 0xFFFF)
    def addi_w(self, v, dn):         self._raw(0x0640 | dn, v & 0xFFFF)
    def move_w_ind(self, an, dn):    self._raw(0x3010 | (dn << 9) | an)
    def swap_dn(self, dn):           self._raw(0x4840 | dn)
    def eor_w_dd(self, src, dst):    self._raw(0xB140 | (src << 9) | dst)
    def move_w_imm_d0(self, v):      self._raw(0x303C, v & 0xFFFF)
    def move_w_to_ind(self, dn, an): self._raw(0x3080 | (an << 9) | dn)
    def move_w_idx(self, an, ix, dn):
        self._raw(0x3000 | (dn << 9) | 0x30 | an, (ix << 12))
    def push_an_l(self, an):         self._raw(0x2F08 | an)
    def pop_an_l(self, an):          self._raw(0x205F | (an << 9))
    def push_dn_w(self, dn):         self._raw(0x3F00 | dn)
    def pop_dn_w(self, dn):          self._raw(0x301F | (dn << 9))
    def move_w_postinc(self, dn, an):self._raw(0x30C0 | (an << 9) | dn)
    def move_w_abs(self, addr, dn):  self._raw(0x3039 | (dn << 9),
                                               (addr >> 16) & 0xFFFF, addr & 0xFFFF)
    def move_w_to_abs(self, dn, addr):
        # MOVE.W Dn,(xxx).l - the DESTINATION occupies bits 11-6 (reg 001,
        # mode 111); the source register is the low field, not bits 11-9.
        self._raw(0x33C0 | dn, (addr >> 16) & 0xFFFF, addr & 0xFFFF)
    def move_w_imm_abs(self, v, addr):
        self._raw(0x33FC, v & 0xFFFF, (addr >> 16) & 0xFFFF, addr & 0xFFFF)
    def move_b_ind(self, an, dn):    self._raw(0x1010 | (dn << 9) | an)
    def move_l_ind_postinc(self, s, d):
        self._raw(0x20D0 | (d << 9) | s)
    def move_l_imm_postinc(self, v, an):
        self._raw(0x20FC | (an << 9), (v >> 16) & 0xFFFF, v & 0xFFFF)


def compose_routine(org=CODE_BASE, font=FONT_BASE, stride=SCRATCH_STRIDE):
    """Render a terminated string into the 1bpp scratch buffer.

        in   a0  text pointer          (advanced past the terminator)
             a1  scratch buffer, SCRATCH_ROWS x stride bytes
        out  d0  pixel width of the run
        uses d1-d7, a2, a3

    One glyph row is a byte with the leftmost pixel in bit 7. Placing it at an
    arbitrary x means shifting it into a 16-bit window - `byte << 8` then
    `lsr` by (x & 7) - after which the high byte belongs to scratch[x >> 3]
    and the low byte to the cell after it. That is the whole trick; everything
    else is bookkeeping.
    """
    a = Asm(org)
    D0, D1, D2, D3, D4, D5, D6, D7 = range(8)
    A1, A2, A3 = 1, 2, 3

    # clear the scratch: SCRATCH_ROWS * stride, rounded up to longwords
    longs = (SCRATCH_ROWS * stride + 3) // 4
    a.movea_l_an(A1, A3)
    a.moveq(longs - 1, D1)
    a.label('clr')
    a.clr_l_postinc(A3)
    a.dbf(D1, 'clr')

    a.moveq(0, D3)                       # x = 0

    a.label('next')
    a.moveq(0, D2)
    a.move_b_postinc(0, D2)              # d2 = (a0)+
    a.cmpi_b_imm(0xFE, D2)
    a.bcc('done')                        # >= $FE terminates

    a.lsl_w(3, D2)                       # code * 8
    a.lea_abs(font, A2)
    a.adda_w_dn(D2, A2)                  # a2 = font entry
    a.moveq(0, D4)
    a.move_b_postinc(A2, D4)             # d4 = advance width
    a.beq('next')                        # width 0 -> undrawable, no advance

    a.move_w_dd(D3, D6)
    a.andi_w(7, D6)                      # d6 = x & 7
    a.move_w_dd(D3, D1)
    a.lsr_w(3, D1)                       # d1 = x >> 3
    a.movea_l_an(A1, A3)
    a.adda_w_dn(D1, A3)                  # a3 = scratch + x>>3

    a.moveq(SCRATCH_ROWS - 1, D7)
    a.label('row')
    a.moveq(0, D5)
    a.move_b_postinc(A2, D5)
    a.lsl_w(8, D5)                       # glyph row into bits 15-8
    a.lsr_w_dn(D6, D5)                   # slide to the sub-byte position
    a.move_w_dd(D5, D0)
    a.lsr_w(8, D0)
    a.or_b_ind(D0, A3)                   # high byte -> this cell
    a.or_b_disp(D5, 1, A3)               # low byte  -> the next one
    a.lea_disp(stride, A3, A3)
    a.dbf(D7, 'row')

    a.add_w_dd(D4, D3)                   # x += width
    a.addq_w(1, D3)                      # x += gap
    a.bra('next')

    a.label('done')
    a.tst_w(D3)
    a.beq('zero')
    a.subq_w(1, D3)                      # drop the trailing gap
    a.label('zero')
    a.move_w_dd(D3, D0)
    a.rts()
    return a


def install_code(rom: bytes, org: int = CODE_BASE) -> bytes:
    """Write the composer, refusing to overwrite anything but filler."""
    code = compose_routine(org).build()
    if len(rom) < org + len(code):
        raise ValueError('rom is not expanded; run `ps4tool.py expand` first')
    if any(b != 0xFF for b in rom[org:org + len(code)]):
        raise ValueError(f'{org:06X} is not $FF filler; refusing to overwrite')
    out = bytearray(rom)
    out[org:org + len(code)] = code
    return bytes(out)


# ------------------------------------------------- 1bpp -> 4bpp expansion

EXPAND_BASE = 0x301000        # 256 longwords: byte -> 8 nibbles
EXPAND_BYTES = 256 * 4
EXPAND_CODE = 0x300900

BLANK_ROW = 0xEEEEEEEE        # a row of paper


def expand_table():
    """byte -> longword, one nibble per bit, MSB leftmost."""
    buf = bytearray(EXPAND_BYTES)
    for b in range(256):
        v = 0
        for i in range(8):
            v = (v << 4) | (INK if (b >> (7 - i)) & 1 else PAPER)
        buf[b * 4:b * 4 + 4] = v.to_bytes(4, 'big')
    return bytes(buf)


def expand_routine(org=EXPAND_CODE, scratch=SCRATCH,
                   table_at=EXPAND_BASE, stride=SCRATCH_STRIDE):
    """Turn the 1bpp scratch into 4bpp tiles, one per cell.

        in   d0  cell count      a1  destination (d0 * 32 bytes)
        out  -   destination filled
        uses d0-d5, a1, a2, a3, a4

    Row 0 of every tile is paper; rows 1-7 carry glyph data. Small caps still
    occupy rows 3-7 and so share a baseline with unconverted text, while
    capitals reach row 2 and lowercase ascenders reach row 2 as well.

    Expansion is a 1 KB lookup rather than a bit loop. Eight nibbles from one
    table read is 12 cycles against roughly 100 for shifting them out one at a
    time, and the table costs nothing in a spare megabyte.
    """
    a = Asm(org)
    D0, D1, D2, D3, D4, D5 = range(6)
    A1, A2, A3, A4 = 1, 2, 3, 4

    a.tst_w(D0)
    a.beq('out')
    a.movea_l_an(A1, A3)                  # caller supplies the destination
    a.move_w_dd(D0, D1)
    a.subq_w(1, D1)                       # cell counter
    a.moveq(0, D4)                        # cell index

    a.label('cell')
    a.move_l_imm_postinc(BLANK_ROW, A3)   # row 0 is paper; 1-7 carry glyphs

    a.lea_abs(scratch, A2)
    a.adda_w_dn(D4, A2)                   # a2 = scratch + cell
    a.moveq(SCRATCH_ROWS - 1, D3)

    a.label('row')
    a.moveq(0, D5)
    a.move_b_ind(A2, D5)                  # one 1bpp row of this cell
    a.lsl_w(2, D5)
    a.lea_abs(table_at, A4)
    a.adda_w_dn(D5, A4)
    a.move_l_ind_postinc(A4, A3)          # eight nibbles out
    a.lea_disp(stride, A2, A2)            # down one scratch row
    a.dbf(D3, 'row')

    a.addq_w(1, D4)
    a.dbf(D1, 'cell')
    a.label('out')
    a.rts()
    return a


# --------------------------------------------------------- the renderer

DRAW_CODE = 0x300A00
RESET_CODE = 0x300B00
# Must sit clear of TILES: at SCRATCH+0x100 it landed INSIDE the 384-byte tile
# buffer and the expander overwrote the allocator with $EEEE on the first draw.
# `check_layout()` below asserts the separation so this cannot recur silently.
POOL_NEXT = SCRATCH + 0x500      # one word of allocator state

# The pool CANNOT be the low font bank yet. Those 128 tiles are still the live
# alphabet for every unconverted caller - in battle the party status bar is on
# screen beside the technique window, drawn by the stock renderer. The bank
# only frees up once ALL menu text is converted.
#
# So the first window borrows from the art region: $4BA-$4DB is the 34-tile run
# that survived all five battle savestates blank and unreferenced. 32 of them
# is the pool. This is the weakest link in the design and is deliberately
# isolated to two constants - once a second window converts, move the pool into
# the freed low bank and the dependency on that survey disappears.
POOL_START = 0x4BA
POOL_END = 0x4DC                 # exclusive - the full 34-tile run
TILES_PER_ROW = 8                # item names reach 8 cells

# Slots cycle with period FIVE, not four, and their tile bases come from a
# table rather than arithmetic.
#
# A power-of-two period is the obvious choice and it is wrong here. The battle
# item list draws FIVE entries per build - four visible plus one off-screen -
# so under `(a1 >> 8) & 3` entry 0 and entry 4 share a slice, and entry 4 is
# "the first item of the next page". That is why page 1 inherited page 2's
# names. Technique and skill menus paginate later in the game and will draw the
# same way.
#
# Period 5 makes any five consecutive rows distinct. It costs a table lookup
# instead of a shift, and it buys freedom from contiguity: the fifth slice
# lives in the structural VRAM gap at $794, which no table can ever use, so
# 5 x 8 = 40 tiles fit where only 34 were contiguous.
SLOT_PERIOD = 5
SLOT_BASES = (0x4BA, 0x4C2, 0x4CA, 0x4D2,   # the $4BA-$4DB run
              0x794)                        # the $F280-$F3FF structural gap
TRACE = 0xFF5E00                 # 32 records x 8 bytes: dest.l, tile.w, pad
TRACE_PTR = 0xFF5F00             # write index, in bytes
TRACE_N = 32

ROWTAB = 0x301400                # 256 bytes: (a1>>8)&$FF -> slot*2
SLOTTAB = 0x301600               # SLOT_PERIOD words: slot -> first tile
SLOT_MASK = 3                    # four rows, 256 bytes apart
SLOT_SHIFT = 3                   # log2(TILES_PER_ROW)
DMA_QUEUE = 0x0420D6             # d0 = source>>1, d1 = VRAM address, d2 = words
VEHICLE_FLAG = 0xF43C            # ($FFF43C).w - non-zero in vehicle battles
FRAME_FIXUP = 0x2805E6           # the stock renderer's own post-step


def reset_routine(org=RESET_CODE):
    """Rewind the tile pool. Called once per window build."""
    a = Asm(org)
    a.move_w_imm_abs(POOL_START, POOL_NEXT)
    a.rts()
    return a


def draw_routine(org=DRAW_CODE):
    """VWF replacement for $280564, for converted call sites only.

        in   a0  text      a1  nametable destination     d0  attribute
        out  -   cells written to (a1)+, tiles queued for DMA

    Tiles are derived from the destination: rows sit 256 bytes apart, so
    `(a1 >> 8) & 3` is a distinct slot per row and each row owns a fixed
    8-tile slice.

    A sequential allocator was tried instead and is WRONG here, for a reason
    worth writing down: **the nametable outlives the allocation.** A row that is
    not redrawn keeps its old nametable entries, and if the pool has since been
    rewound and refilled with different-width text, those entries index tiles
    that now hold something else at a different offset. That is exactly what the
    battle item menu's pages showed - row 1 displaying the first six cells of a
    name drawn for another page, its last two cells spilling into row 2.

    Deriving the slot removes that failure entirely: row R always owns the same
    tiles, so a stale entry shows row R's own most recent content, which is
    correct by construction. It also needs no reset, and therefore no hook.

    A name wider than its slice draws NOTHING rather than running into the next
    row's tiles.

    EVERY DRAW EMITS THE FULL SLICE - eight nametable cells and eight tiles -
    however short the name. That is not tidiness, it is correctness.

    Under the stock renderer a stale nametable entry is harmless: tiles are a
    fixed alphabet, so an entry written for old text still renders that old text
    correctly. With a VWF the tiles belong to a string, so a stale entry renders
    whatever now occupies them. The battle item menu does exactly this - the
    window buffer at $FF069A held seven entries for a slot while the plane copy
    still held five, so five cells indexed a seven-cell name and displayed
    `MONOMA`.

    Writing a fixed count makes the entry list length-invariant: a stale copy
    has the same eight entries as a fresh one, so it shows the slot's current
    contents rather than a truncation of them. The tail is blank because the
    composer clears the scratch before it starts.

    NOTHING LIVE MAY CROSS A CALL. The composer uses d1-d7 and a2/a3; the
    expander uses d0-d5 and a1-a4. The attribute rides the stack across both,
    the tile index sits in d6 and the cell count in d7, the DMA source rides the
    stack across the expander, and the nametable pointer stays in a5.
    """
    a = Asm(org)
    D0, D1, D2, D3, D5, D6, D7 = 0, 1, 2, 3, 5, 6, 7
    A0, A1, A5 = 0, 1, 5

    a.movem_push(0xFFFC)                 # d0-d7 / a0-a5
    a.push_dn_w(D0)                      # attribute, across both calls
    a.movea_l_an(A1, A5)                 # a5 = nametable destination
    a.lea_abs(SCRATCH, A1)
    a.jsr_abs(CODE_BASE)                 # compose -> d0 = pixel width
    a.addq_w(7, D0)
    a.lsr_w(3, D0)                       # cells = (px + 7) >> 3
    a.move_w_dd(D0, D7)
    a.beq('unwind')

    a.move_l_an_dn(A5, D6)               # slot from the destination row
    a.lsr_l(8, D6)
    a.andi_w(0xFF, D6)
    a.lea_abs(ROWTAB, A1)
    a.move_b_idx(A1, D6, D6)             # d6 = slot * 2
    a.cmpi_w(TILES_PER_ROW + 1, D7)
    a.bcc('unwind')                      # wider than its slice: draw nothing

    a.move_w_dd(D6, D0)                  # slice of the tile buffer: slot*2*128
    a.lsl_w(7, D0)
    a.lea_abs(TILES, A1)
    a.adda_w_dn(D0, A1)
    a.lea_abs(SLOTTAB, A0)               # a0 is free; the text is consumed
    a.move_w_idx(A0, D6, D6)             # d6 = this slot's first tile
    a.push_an_l(A1)                      # keep the DMA source
    # ALWAYS the full slice, never just the cells this name needs. The composer
    # cleared the scratch, so the tail expands to blanks. See the note below.
    a.moveq(TILES_PER_ROW, D7)
    a.move_w_dd(D7, D0)
    a.jsr_abs(EXPAND_CODE)               # expand into (a1)
    a.pop_an_l(A1)
    a.pop_dn_w(D5)                       # attribute back

    a.move_l_an_dn(A1, D0)
    a.lsr_l(1, D0)                       # DMA source, in words
    a.move_w_dd(D6, D1)
    a.lsl_w(5, D1)                       # VRAM address = tile * 32
    a.move_w_dd(D7, D2)
    a.lsl_w(4, D2)                       # length in words = cells * 16
    a.jsr_abs(DMA_QUEUE)

    # --- diagnostic ring buffer -------------------------------------------
    # Records every draw as (destination low word, first tile). Reading it out
    # of a savestate answers in one capture what four rounds of inferring this
    # menu's behaviour from leftover RAM did not: which addresses are drawn to,
    # in what order, and which of them share a slice.
    a.lea_abs(TRACE_PTR, A0)
    a.move_w_ind(A0, D0)
    a.andi_w((TRACE_N - 1) * 8, D0)
    a.lea_abs(TRACE, A1)
    a.adda_w_dn(D0, A1)
    a.move_l_an_dn(A5, D1)
    a.move_w_dd(D1, D2)
    a.swap_dn(D1)
    a.move_w_postinc(D1, A1)             # destination, HIGH word
    a.move_w_postinc(D2, A1)             # destination, low word
    a.move_w_postinc(D6, A1)             # first tile of the slice
    a.addq_w(8, D0)                      # 8-byte stride; the 8th byte is spare
    a.move_w_to_ind(D0, A0)
    # ----------------------------------------------------------------------

    a.move_w_dd(D7, D3)
    a.subq_w(1, D3)
    a.label('nt')
    a.move_w_dd(D6, D0)
    a.add_w_dd(D5, D0)                   # tile + attribute
    a.move_w_postinc(D0, A5)
    a.addq_w(1, D6)
    a.dbf(D3, 'nt')

    a.bra('done')

    a.label('unwind')
    a.addq_l_sp(2)                       # discard the stashed attribute


    a.label('done')
    a.movem_pop(0x3FFF)
    # Vehicle battles ($FFF43C) re-skin the window-frame tile above the name.
    a.tst_w_short(VEHICLE_FLAG)
    a.beq('ret')
    a.jsr_abs(FRAME_FIXUP)
    a.label('ret')
    a.rts()
    return a


# ------------------------------------------------------------- wiring

WINDOW_BUILD = 0x2804BE       # Battle_SetupWindow - precedes EVERY draw site
STOCK_RENDERER = 0x280564
TRAMPOLINE = 0x300B10

# Tables drawn by the VWF renderer. english8 reads this to decide which names
# must be encoded as plain letters rather than paired.
VWF_SEGMENTS = frozenset({'00:001',      # item names
                          '00:002',      # technique names
                          '00:003'})     # skill names

# (operand offset, what it draws). Operands are at call+2.
DRAW_SITES = (
    (0x001856, 'techniques'),
    (0x001BE2, 'skills'),
    # Item menus are NOT converted. They redraw the same destination with
    # different content while an older plane copy is still on screen, which
    # destination-derived slices cannot survive - see the trace analysis below.
    # They need double-buffered slices, and that needs the low font bank.
)

# The `jsr ($2804BE).l` that precedes each of the above, redirected to a stub
# that rewinds the pool first. This is the reset the first design got wrong: it
# hooked $041C70, which is not the window build, so the pool drifted across
# redraws until long names were refused.
RESET_SITES = (
    (0x0017D8, 'techniques'),
    (0x001B64, 'skills'),
    (0x001F38, 'items, field menu'),
    (0x003C56, 'items, field menu 2'),
    (0x004D3E, 'items, battle list'),
)


def trampoline_routine(org=TRAMPOLINE):
    """Rewind the pool, then carry on into the window build.

    `jmp` rather than `jsr`: Battle_SetupWindow's own `rts` returns to the
    original caller, the stack is untouched, and it sees exactly the registers
    it would have - the reset writes one word of RAM and clobbers nothing.
    """
    a = Asm(org)
    a.move_w_imm_abs(POOL_START, POOL_NEXT)
    a.jmp_abs(WINDOW_BUILD)
    return a


def wire(rom: bytes) -> bytes:
    """Redirect the converted draw sites, and their window builds."""
    out = bytearray(rom)
    # No pool reset, and so no trampoline: slots are derived, not allocated.
    for off, want, new, what in (
            [(o, STOCK_RENDERER, DRAW_CODE, w) for o, w in DRAW_SITES]):
        cur = int.from_bytes(out[off:off + 4], 'big')
        if cur != want:
            raise ValueError(f'{off:06X} ({what}): expected ${want:06X}, '
                             f'found ${cur:06X}')
        out[off:off + 4] = new.to_bytes(4, 'big')
    return bytes(out)


def check_layout():
    """Assert the RAM blocks do not overlap, and that the tile buffer can hold
    everything the pool can allocate. Cheap, and it has caught two bugs."""
    blocks = [('scratch', SCRATCH, SCRATCH_BYTES),
              ('tiles', TILES, TILES_BYTES),
              ]
    blocks.sort(key=lambda b: b[1])
    for (n1, a1, s1), (n2, a2, _) in zip(blocks, blocks[1:]):
        if a1 + s1 > a2:
            raise ValueError(f'{n1} (${a1:06X}+{s1}) overlaps {n2} (${a2:06X})')
    if len(SLOT_BASES) != SLOT_PERIOD:
        raise ValueError('SLOT_BASES must have one entry per slot')
    spans = sorted((b, b + TILES_PER_ROW) for b in SLOT_BASES)
    for (a1_, b1), (a2_, _) in zip(spans, spans[1:]):
        if b1 > a2_:
            raise ValueError(f'slices ${a1_:03X} and ${a2_:03X} overlap')
    top = blocks[-1][1] + blocks[-1][2]
    return {'lo': blocks[0][1], 'hi': top, 'bytes': top - blocks[0][1]}


def install_all(rom: bytes) -> bytes:
    """Every VWF asset. Writes into $FF filler only, never below $300000."""
    check_layout()
    out = bytes(rom)
    for base, blob in ((FONT_BASE, table()),
                       (EXPAND_BASE, expand_table()),
                       (ROWTAB, rowtab()),
                       (SLOTTAB, slottab()),
                       (CODE_BASE, compose_routine().build()),
                       (EXPAND_CODE, expand_routine().build()),
                       (DRAW_CODE, draw_routine().build()),
                       (RESET_CODE, reset_routine().build())):
        if len(out) < base + len(blob):
            raise ValueError('rom is not expanded; run `ps4tool.py expand`')
        if any(b != 0xFF for b in out[base:base + len(blob)]):
            raise ValueError(f'{base:06X} is not $FF filler; refusing')
        buf = bytearray(out)
        buf[base:base + len(blob)] = blob
        out = bytes(buf)
    return out


def rowtab():
    """(a1 >> 8) & $FF  ->  slot * 2, cycling with period SLOT_PERIOD."""
    return bytes(((h % SLOT_PERIOD) * 2) & 0xFF for h in range(256))


def slottab():
    """slot -> first tile of its slice."""
    out = bytearray()
    for b in SLOT_BASES:
        out += b.to_bytes(2, 'big')
    return bytes(out)
