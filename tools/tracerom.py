"""A trace-only build: log every 8x8 text draw, change nothing else.

The renderer has two entry points and 66 callers between them, so designing an
allocation scheme for a full VWF conversion means knowing which destinations are
actually written, and which are live at the same time. Six attempts to infer
that from the disassembly and from leftover RAM were wrong. This measures it.

Both entry points are redirected to a stub that records (destination, text
pointer) into a ring buffer and then performs the instructions it displaced
before rejoining the stock renderer at $28056A. Nothing about the drawing
changes - the ROM plays exactly as it did.

    $28055A  movem.l d2/d3/d7/a0/a1,-(a7)   entry B, forces d0 = $E000
    $28055E  move.w  #$E000,d0
    $280562  bra     $280568
    $280564  movem.l d2/d3/d7/a0/a1,-(a7)   entry A, caller supplies d0
    $280568  moveq   #0,d2                  <- BRANCH TARGET, must not move
    $28056A  move.b  (a0)+,d2

**$280568 CANNOT BE OVERWRITTEN.** Three branches target it - the main loop-back
at $28058E, the dakuten path at $2805E0, and entry B's own `bra`. A six-byte
`jmp` planted at $280564 swallows it, so every character after the first
branched into the middle of a jump operand and executed garbage. That crashed
the game on entering battle, with an address error and the PC in the plane-B
buffer.

So entry A is left alone and its NINE call sites are redirected instead; only
entry B, whose span nothing branches into, is patched in place.

The VWF is NOT installed in this build. That frees the whole work-RAM block for
the log, which is why it can hold 256 draws rather than 32.
"""
import vwfpatch

TR_BUF = 0xFF5400          # 256 records x 8 bytes: dest.l, text.l
TR_N = 256
TR_PTR = 0xFF5C00          # write index, in bytes

STUB_A = 0x300C00
STUB_B = 0x300C60
RECORD = 0x300CC0

ENTRY_A = 0x280564
ENTRY_B = 0x28055A
REJOIN_B = 0x280568        # the `moveq #0,d2` entry B fell into
MOVEM = 0x31C0             # d2/d3/d7/a0/a1, predecrement mask


class Asm(vwfpatch.Asm):
    def move_l_an_postinc(self, src, dst):
        self._raw(0x20C8 | (dst << 9) | src)

    def move_l_an_ind(self, src, dst):
        # MOVE.L An,(Am): source mode 001 (address register direct). 0x2080
        # would encode mode 000 - move.l Dn,(Am) - and silently log d0.
        self._raw(0x2088 | (dst << 9) | src)


def record_routine(org=RECORD):
    """Store (a1, a0) in a hash table keyed by the destination.

    NOT a ring. The party status bar redraws all three names EVERY FRAME, so a
    256-entry ring fills with about 85 frames of nothing else and everything
    interesting scrolls out. A table keyed by destination collapses repeats onto
    their own slot, so what accumulates is the SET of draws the game performs.

    The key is `((dest >> 1) ^ (dest >> 9)) & $FF`. Destination rows differ in
    bits 8-11 and columns in bits 1-7, so folding the two apart separates both:
    `dest >> 1` alone collides item rows $069A with $089A, and $079A with $099A.

    A collision is visible rather than silent - the stored destination is kept,
    so a slot whose key does not rehash to itself was overwritten by another
    address.

    Preserves every register it touches.
    """
    a = Asm(org)
    D0, D1, A0, A1, A2 = 0, 1, 0, 1, 2
    a.movem_push(0xC020)                 # d0/d1/a2
    a.move_l_an_dn(A1, D0)
    a.lsr_l(1, D0)
    a.move_l_an_dn(A1, D1)
    a.lsr_l(8, D1)
    a.lsr_l(1, D1)                       # #9 is not an encodable count
    a.eor_w_dd(D1, D0)
    a.andi_w(0xFF, D0)
    a.lsl_w(3, D0)                       # 8 bytes per entry
    a.lea_abs(TR_BUF, A2)
    a.adda_w_dn(D0, A2)
    a.move_l_an_postinc(A1, A2)          # destination
    a.move_l_an_ind(A0, A2)              # text pointer
    a.movem_pop(0x0403)                  # d0/d1/a2
    a.rts()
    return a


def stub_a(org=STUB_A):
    """Record, then enter the untouched entry A."""
    a = Asm(org)
    a.jsr_abs(RECORD)
    a.jmp_abs(ENTRY_A)
    return a


def stub_b(org=STUB_B):
    """Record, replay what entry B's patch covered, rejoin at $280568."""
    a = Asm(org)
    a.jsr_abs(RECORD)
    a.movem_push(MOVEM)
    a.move_w_imm_d0(0xE000)
    a.jmp_abs(REJOIN_B)
    return a


# operands of `jsr ($280564).l`, i.e. every entry-A call site
ENTRY_A_SITES = (0x001856, 0x001BE2, 0x001FF4, 0x003CF4,
                 0x004DAA, 0x004DEE, 0x00504A, 0x005096, 0x007458)


def install(rom: bytes) -> bytes:
    out = bytearray(rom)
    for org, blob in ((RECORD, record_routine().build()),
                      (STUB_A, stub_a().build()),
                      (STUB_B, stub_b().build())):
        if any(b != 0xFF for b in out[org:org + len(blob)]):
            raise ValueError(f'{org:06X} is not $FF filler')
        out[org:org + len(blob)] = blob

    # entry B in place - nothing branches into $28055A-$28055F
    if int.from_bytes(out[ENTRY_B:ENTRY_B + 4], 'big') != 0x48E731C0:
        raise ValueError('entry B does not start with the expected movem')
    out[ENTRY_B:ENTRY_B + 2] = bytes([0x4E, 0xF9])
    out[ENTRY_B + 2:ENTRY_B + 6] = STUB_B.to_bytes(4, 'big')

    # entry A by its call sites, leaving $280564-$280569 - and the branch
    # target at $280568 - completely untouched
    for off in ENTRY_A_SITES:
        cur = int.from_bytes(out[off:off + 4], 'big')
        if cur != ENTRY_A:
            raise ValueError(f'{off:06X}: expected ${ENTRY_A:06X}, found ${cur:06X}')
        out[off:off + 4] = STUB_A.to_bytes(4, 'big')
    return bytes(out)


def key(dest):
    return (((dest >> 1) ^ (dest >> 9)) & 0xFF)


def read(ram: bytes, base=0xFF0000):
    """Decode the table. Returns (dest, text, collided)."""
    out = []
    for k in range(TR_N):
        o = TR_BUF - base + k * 8
        dest = int.from_bytes(ram[o:o + 4], 'big')
        text = int.from_bytes(ram[o + 4:o + 8], 'big')
        if dest or text:
            out.append((dest, text, key(dest) != k))
    return out
