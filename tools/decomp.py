"""PS4 graphics decompressor - reimplementation of the routine at $0416F6.

Scheme: canonical Huffman over (nibble, run-length) symbols, decoded through a
256-entry fast lookup table indexed by the top 8 bits of a 16-bit bit buffer.
Output nibbles accumulate 8 at a time into a longword which is written to the
destination, optionally XOR-filtered against the previous longword.

Stream layout:
    word    header      bit15 = XOR filter, (hdr << 3) & 0xFFFF = longword count
    bytes   code table  see build_table(), terminated by $FF
    bytes   bitstream

Table entry (one word): (code_length << 8) | ((run & 7) << 4) | nibble
Codes whose top 8 bits are >= $FC escape to a 7-bit literal: [run:3][nibble:4].
"""


def build_table(data, p):
    """Returns (table, p). table[i] = (code_length << 8) | symbol."""
    table = [0] * 256
    b = data[p]; p += 1
    while b != 0xFF:
        group = b                      # d7: supplies the low nibble (the value)
        while True:
            b2 = data[p]; p += 1
            if b2 >= 0x80:             # start of a new group, or $FF terminator
                b = b2
                break
            codelen = b2 & 0x0F
            symbol = (b2 & 0x70) | (group & 0x0F)
            entry = (codelen << 8) | symbol
            nbits = 8 - codelen
            idx = data[p]; p += 1
            if nbits == 0:
                table[idx & 0xFF] = entry
            else:
                base = (idx << nbits) & 0xFF
                for k in range(1 << nbits):
                    table[(base + k) & 0xFF] = entry
    return table, p


def decompress(data, off, limit=None):
    """Decode the blob at `off`. If `limit` is set, stop after that many
    output bytes (used to cheaply pre-screen candidates during a scan)."""
    p = off
    hdr = (data[p] << 8) | data[p + 1]; p += 2
    xor_filter = bool(hdr & 0x8000)
    remaining = (hdr << 3) & 0xFFFF          # longwords to emit
    if remaining == 0:
        return b""

    table, p = build_table(data, p)

    bits = ((data[p] << 8) | data[p + 1]) & 0xFFFF; p += 2
    navail = 16
    acc = 0            # d4: nibble accumulator
    nleft = 8          # d3: nibbles until a longword is complete
    prev = 0           # d2: XOR filter state
    out = bytearray()

    def refill(bits, navail, p):
        if navail < 9:
            navail += 8
            # The refill is eager, like the game's routine: after the final
            # code it fetches one byte that is never used.  In ROM that byte
            # exists; for a blob that ends exactly at the stream's end it does
            # not, so read past the end as zero rather than raising.
            bits = ((bits << 8) | (data[p] if p < len(data) else 0)) & 0xFFFF
            p += 1
        return bits, navail, p

    while True:
        peek = (bits >> (navail - 8)) & 0xFF
        if peek >= 0xFC:
            navail -= 6
            bits, navail, p = refill(bits, navail, p)
            navail -= 7
            v = (bits >> navail) & 0xFFFF
            run = (v & 0x70) >> 4
            nib = v & 0x0F
            bits, navail, p = refill(bits, navail, p)
        else:
            entry = table[peek]
            navail -= (entry >> 8)
            bits, navail, p = refill(bits, navail, p)
            sym = entry & 0xFF
            run = (sym & 0xF0) >> 4
            nib = sym & 0x0F

        for _ in range(run + 1):
            acc = ((acc << 4) | nib) & 0xFFFFFFFF
            nleft -= 1
            if nleft == 0:
                if xor_filter:
                    prev ^= acc
                    out += prev.to_bytes(4, 'big')
                else:
                    out += acc.to_bytes(4, 'big')
                remaining -= 1
                if remaining == 0:
                    return bytes(out)
                if limit is not None and len(out) >= limit:
                    return bytes(out)
                acc = 0
                nleft = 8
