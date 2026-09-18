"""Kosinski decompression, and a validator for any compressor we add later.

Written to recover the original dialogue tree sources: the trees ship as
Kosinski-compressed .bin, the shipped koscmp.exe will not load on this machine
(0xC000007B), and the .asm sources are the only readable form.

Format: a 16-bit little-endian descriptor field, bits consumed LSB first,
refilled when exhausted.
    1        literal byte
    0 1      full match - 13-bit signed offset, count in the low 3 bits of the
             high byte, or an extra count byte (0 ends the stream)
    0 0 b b  inline match - 8-bit offset, 2-bit count
"""
import struct


def _reader(data, at):
    """Bit reader matching KosDecomp at ps4.asm:84672.

    The descriptor is refilled the moment its 16th bit is consumed - the engine
    does `dbf d4` between stashing the bit in d6 and acting on it - so the
    refill lands BEFORE the operation's own data bytes. Refilling lazily on the
    next bit request instead makes an operation read its offset byte out of the
    descriptor field, which is exactly where a lazy reader first diverges.
    """
    pos = at
    desc = struct.unpack_from('<H', data, pos)[0]
    pos += 2
    nbits = 16

    def bit():
        nonlocal desc, nbits, pos
        b = desc & 1
        desc >>= 1
        nbits -= 1
        if nbits == 0:
            desc = struct.unpack_from('<H', data, pos)[0]
            pos += 2
            nbits = 16
        return b

    def byte():
        nonlocal pos
        v = data[pos]; pos += 1
        return v

    def where():
        return pos
    return bit, byte, where


def decompress(data: bytes, at: int = 0) -> bytes:
    out = bytearray()
    bit, byte, where = _reader(data, at)
    while True:
        if bit():
            out.append(byte())
            continue
        if bit():
            lo = byte(); hi = byte()
            off = (((hi & 0xF8) << 5) | lo) - 0x2000    # 13-bit, always negative
            cnt = hi & 0x07
            if cnt == 0:
                cnt = byte()
                if cnt == 0:
                    break                                # end of stream
                if cnt == 1:
                    continue
                cnt += 1
            else:
                cnt += 2
        else:
            cnt = ((bit() << 1) | bit()) + 2
            off = byte() - 0x100
        for _ in range(cnt):
            out.append(out[len(out) + off])
    return bytes(out)
