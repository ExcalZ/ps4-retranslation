"""Nemesis compressor - the encode side of decomp.py.

decomp.py reimplements the decoder at $0416F6; this produces streams it accepts.
Needed because adding lowercase and ligature glyphs to the 8x8 system font at
$2A303A means rewriting a Nemesis blob, and the disassembly ships only a
Kosinski compressor.

Format, mirroring decomp.py:

    word    header      bit15 = XOR filter, low bits = TILE count
                        (the decoder computes rows as (hdr << 3) & 0xFFFF)
    bytes   code table  groups of (nibble value, then its codes), $FF terminated
    bytes   bitstream

A symbol is (run << 4) | nibble, where run is 0-7 and means run+1 copies of that
nibble. Runs may cross a row boundary: the decoder just pushes nibbles and
flushes every eighth one.

Two constraints shape the Huffman step:

  * codes are looked up by peeking 8 bits, so no code may exceed 8 bits
  * a peek of $FC-$FF means "inline literal", so the assigned codes must leave
    the top four slots of the 256-entry table free. Canonical assignment counts
    upward from zero, so it is enough that sum(2^(8-len)) <= 252.

Symbols that cannot be given a short enough code are dropped from the table and
emitted as inline literals instead, which cost 6 + 7 = 13 bits each.
"""
import heapq
from collections import Counter

ESCAPE_SLOTS = 4                    # $FC-$FF reserved for the literal escape
TABLE_SLOTS = 256 - ESCAPE_SLOTS


def _rows(data):
    return [int.from_bytes(data[i:i + 4], 'big') for i in range(0, len(data), 4)]


def _symbols(rows):
    """(run, nibble) pairs; runs may span rows, capped at 8 repeats."""
    nibs = []
    for r in rows:
        for s in range(28, -4, -4):
            nibs.append((r >> s) & 0xF)
    out, i = [], 0
    while i < len(nibs):
        n = nibs[i]
        j = i + 1
        while j < len(nibs) and nibs[j] == n and j - i < 8:
            j += 1
        out.append(((j - i - 1) << 4) | n)
        i = j
    return out


def _lengths(freq, keep):
    """Huffman code lengths for `keep`, or None if any exceeds 8 bits."""
    if len(keep) == 1:
        return {next(iter(keep)): 1}
    h = [(freq[s], i, {s: 0}) for i, s in enumerate(sorted(keep))]
    heapq.heapify(h)
    nxt = len(h)
    while len(h) > 1:
        f1, _, a = heapq.heappop(h)
        f2, _, b = heapq.heappop(h)
        merged = {k: v + 1 for k, v in a.items()}
        merged.update({k: v + 1 for k, v in b.items()})
        heapq.heappush(h, (f1 + f2, nxt, merged)); nxt += 1
    lens = h[0][2]
    return None if max(lens.values()) > 8 else lens


def _slots(lens):
    return sum(1 << (8 - L) for L in lens.values())


def _fit(freq):
    """Code lengths that stay within 8 bits and leave the escape its slots.

    Huffman always yields a COMPLETE code, so its Kraft sum is exactly 256
    slots and the naive test "does it leave 252 free" can never pass. Shorten
    the code space instead: repeatedly lengthen the rarest symbol by one bit,
    which halves the slots it occupies, until the escape's four fit. A symbol
    already at the 8-bit ceiling is dropped to an inline literal instead.
    """
    keep = set(freq)
    while keep:
        lens = _lengths(freq, keep)
        if lens is None:                       # some code exceeded 8 bits
            keep.remove(min(keep, key=lambda s: (freq[s], -s)))
            continue
        lens = dict(lens)
        while lens and _slots(lens) > TABLE_SLOTS:
            rare = min(lens, key=lambda s: (freq[s], -s))
            if lens[rare] < 8:
                lens[rare] += 1
            else:
                del lens[rare]
        if lens:
            return lens
        keep.remove(min(keep, key=lambda s: (freq[s], -s)))
    return {}


def _canonical(lens):
    """Canonical codes counting up from zero, shortest first."""
    codes, code, prev = {}, 0, None
    for sym in sorted(lens, key=lambda s: (lens[s], s)):
        L = lens[sym]
        if prev is not None:
            code = (code + 1) << (L - prev)
        prev = L
        codes[sym] = code
    return codes


def _emit_table(lens, codes):
    out = bytearray()
    for nib in range(16):
        syms = sorted(s for s in codes if (s & 0x0F) == nib)
        if not syms:
            continue
        out.append(0x80 | nib)
        for s in syms:
            out.append(((s & 0x70)) | lens[s])
            out.append(codes[s])
    out.append(0xFF)
    return out


class _Bits:
    def __init__(self):
        self.buf = bytearray(); self.cur = 0; self.n = 0

    def put(self, value, width):
        for k in range(width - 1, -1, -1):
            self.cur = (self.cur << 1) | ((value >> k) & 1)
            self.n += 1
            if self.n == 8:
                self.buf.append(self.cur); self.cur = 0; self.n = 0

    def done(self):
        if self.n:
            self.buf.append((self.cur << (8 - self.n)) & 0xFF)
        # The decoder refills up to two bytes ahead of the symbol it is
        # decoding, so leave slack rather than let it read the next asset.
        self.buf += b'\x00' * 4
        return bytes(self.buf)


def _encode(data, xor):
    rows = _rows(data)
    if xor:
        enc, prev = [], 0
        for r in rows:
            enc.append(r ^ prev); prev = r
        rows = enc
    syms = _symbols(rows)
    freq = Counter(syms)
    lens = _fit(freq)
    codes = _canonical(lens)

    bits = _Bits()
    for s in syms:
        if s in codes:
            bits.put(codes[s], lens[s])
        else:
            bits.put(0x3F, 6)                       # $FC-$FF escape prefix
            bits.put(((s & 0x70) | (s & 0x0F)), 7)  # [run:3][nibble:4]

    tiles = len(data) // 32
    hdr = tiles | (0x8000 if xor else 0)
    return bytes([hdr >> 8, hdr & 0xFF]) + _emit_table(lens, codes) + bits.done()


def compress(data):
    """Nemesis-encode `data` (a multiple of 32 bytes). Picks the smaller mode."""
    if len(data) % 32:
        raise ValueError(f'{len(data)} bytes is not a whole number of tiles')
    plain = _encode(data, False)
    xored = _encode(data, True)
    return xored if len(xored) < len(plain) else plain
