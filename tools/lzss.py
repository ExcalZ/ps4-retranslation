"""LZSS decompressor - reimplementation of the routine at $041BA0.

This is the game's THIRD codec, separate from the 4bpp graphics Huffman/RLE at
$0416F6. It expands the story script from ROM into the RAM work buffer at
$FF3000, which is why sweeping every compressed blob with the graphics decoder
never found any script: the script is not stored in that format.

Found by watchpointing writes to $FF3000 and reading the registers at the
break: a0 = $001DC4E8 (ROM source), a1 = $FFFF3000 (RAM destination),
PC = $00041BC2 (the literal-copy instruction inside the loop).

Format
------
A 16-bit flag word, LSB first, one bit per operation:

    bit set    literal: copy one byte
    bit clear  match:   copy from earlier in the output

Matches come in two forms, selected by the next flag bit:

    clear   short: 2 more flag bits give length-1 (so 1..4), then one byte
                   gives an 8-bit negative offset
    set     long:  two bytes give a 13-bit negative offset and a 3-bit
                   length-1 (so 1..8). A length code of 0 means an extended
                   byte follows: 0 ends the stream, 1 is a no-op, anything
                   else is the literal length.

The flag word is refilled every 16 operations. Offsets are negative indices
into the output produced so far, so matches may overlap their own output.
"""


class _Bits:
    """Flag-word reader: 16 bits per word, low byte first in the stream."""

    def __init__(self, data, pos):
        self.d = data
        self.p = pos
        self.word = 0
        self.left = 0
        self._load()

    def _load(self):
        lo = self.d[self.p]; self.p += 1
        hi = self.d[self.p]; self.p += 1
        self.word = (hi << 8) | lo
        self.left = 16

    def bit(self):
        b = self.word & 1
        self.word >>= 1
        self.left -= 1
        if self.left == 0:
            self._load()
        return b

    def byte(self):
        v = self.d[self.p]; self.p += 1
        return v


def decompress(data, src, limit=0x10000, with_size=False):
    """Expand the LZSS stream at `src`. Returns the decompressed bytes."""
    bits = _Bits(data, src)
    out = bytearray()

    while len(out) < limit:
        if bits.bit():                                  # literal
            out.append(bits.byte())
            continue

        if not bits.bit():                              # short match
            n = (bits.bit() << 1) | bits.bit()
            length = n + 1
            off = bits.byte() | 0xFF00                  # d2 = $FFFFFF00 | byte
        else:                                           # long match
            b0 = bits.byte()
            b1 = bits.byte()
            off = (((0xFF00 | b1) << 5) & 0xFF00) | b0
            code = b1 & 7
            if code == 0:
                ext = bits.byte()
                if ext == 0:
                    break                               # end of stream
                if ext == 1:
                    continue                            # no-op
                length = ext
            else:
                length = code + 1

        delta = off - 0x10000 if off & 0x8000 else off  # sign-extend .w
        for _ in range(length + 1):
            i = len(out) + delta
            if i < 0:
                # A real stream never references before its own start - the
                # game decompresses into a fresh buffer, so there is nothing
                # there to copy. An underflow therefore means `src` is wrong.
                # This used to append 0 instead, and since $00 decodes to a
                # space, five mislocated streams quietly lost 1258 characters
                # out of the middles of sentences rather than failing.
                raise ValueError(
                    f'back-reference underflow at output byte {len(out)} '
                    f'(offset {delta}) - stream start {src:06X} is wrong')
            out.append(out[i])
    return (bytes(out), bits.p - src) if with_size else bytes(out)
