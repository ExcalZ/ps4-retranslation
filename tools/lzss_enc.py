"""LZSS compressor - produces streams the game's decompressor at $041BA0 reads.

Mirrors lzss.py exactly. Correctness first: the goal is that
lzss.decompress(compress(x)) == x, and that the output is no larger than the
original stream so it can be written back in place.

Encoding recap (see lzss.py for the disassembly it came from):

    flag bit set    literal byte
    flag bit clear  match, with a second flag bit choosing the form:
        clear  short: two more flag bits give (length-1), then one byte is
               an 8-bit negative offset      -> 2..5 bytes, window 256
        set    long:  two bytes give a 13-bit negative offset and a 3-bit
               (length-1)                    -> 3..9 bytes, window 8192
               a length code of 0 means an extended byte follows:
               0 ends the stream, 1 is a no-op, else it is the length

Flag words are 16 bits, low byte first, and are re-read every 16 bits at the
point the decoder needs one - so the encoder must interleave them identically.
"""

SHORT_WIN = 256
LONG_WIN = 8192
SHORT_MAX = 5          # copies = (2-bit value) + 2
LONG_MAX = 9           # copies = (3-bit code) + 2, code 1..7
EXT_MAX = 256          # copies = ext + 1, ext 2..255


class _Out:
    """Byte sink that interleaves flag words the way the decoder expects."""

    def __init__(self):
        self.buf = bytearray()
        self._reserve()

    def _reserve(self):
        self.slot = len(self.buf)
        self.buf += b'\x00\x00'
        self.word = 0
        self.n = 0

    def bit(self, b):
        if b:
            self.word |= (1 << self.n)
        self.n += 1
        if self.n == 16:
            self._flush()
            self._reserve()

    def _flush(self):
        self.buf[self.slot] = self.word & 0xFF          # low byte first
        self.buf[self.slot + 1] = (self.word >> 8) & 0xFF

    def byte(self, v):
        self.buf.append(v & 0xFF)

    def done(self):
        self._flush()
        return bytes(self.buf)


def _find(src, pos, win, longest):
    """Longest match starting at pos within `win` bytes back. Returns (len, dist)."""
    best_len, best_dist = 0, 0
    start = max(0, pos - win)
    limit = min(longest, len(src) - pos)
    if limit < 2:
        return 0, 0
    for cand in range(pos - 1, start - 1, -1):
        if src[cand] != src[pos]:
            continue
        n = 0
        while n < limit and src[cand + n] == src[pos + n]:
            n += 1
        if n > best_len:
            best_len, best_dist = n, pos - cand
            if n == limit:
                break
    return best_len, best_dist


def _cost(ln, sn):
    """Rough bit cost of encoding a match of this length here."""
    if sn >= 2 and sn >= ln:
        return 4 + 8, sn          # 4 flag bits + 1 byte
    if ln >= 3:
        return 2 + (24 if ln > LONG_MAX else 16), ln
    return 1 + 8, 1               # literal


def compress_greedy(src: bytes) -> bytes:
    out = _Out()
    pos = 0
    while pos < len(src):
        # long window first: it reaches further and encodes more length
        ln, dist = _find(src, pos, LONG_WIN, EXT_MAX)
        sn, sdist = _find(src, pos, SHORT_WIN, SHORT_MAX)

        # Lazy matching: if starting one byte later pays better per byte,
        # emit a literal now and take the longer match next round. Costs one
        # literal but often buys a materially longer match.
        if max(ln, sn) >= 2 and pos + 1 < len(src):
            ln2, _ = _find(src, pos + 1, LONG_WIN, EXT_MAX)
            sn2, _ = _find(src, pos + 1, SHORT_WIN, SHORT_MAX)
            c_now, n_now = _cost(ln, sn)
            c_next, n_next = _cost(ln2, sn2)
            if n_next > n_now and (c_now / n_now) > ((9 + c_next) / (1 + n_next)):
                out.bit(1)
                out.byte(src[pos])
                pos += 1
                continue

        # a short match is cheaper (4 flag bits + 1 byte vs 2 bits + 2 bytes)
        if sn >= 2 and sn >= ln:
            out.bit(0)                       # match
            out.bit(0)                       # short form
            v = sn - 2                       # copies = v + 2
            out.bit((v >> 1) & 1)
            out.bit(v & 1)
            out.byte((-sdist) & 0xFF)
            pos += sn
            continue

        if ln >= 3:
            off = (0x10000 - dist) & 0xFFFF
            hi = (off >> 8) & 0xFF
            if 0xE0 <= hi <= 0xFF:
                b0 = off & 0xFF
                top = (hi - 0xE0) & 0x1F
                out.bit(0)                   # match
                out.bit(1)                   # long form
                if ln <= LONG_MAX:
                    code = ln - 2            # copies = code + 2, code 1..7
                    out.byte(b0)
                    out.byte((top << 3) | code)
                else:
                    out.byte(b0)
                    out.byte(top << 3)       # code 0 -> extended length
                    out.byte(ln - 1)         # copies = ext + 1
                pos += ln
                continue

        out.bit(1)                           # literal
        out.byte(src[pos])
        pos += 1

    # terminator: long-form match, length code 0, extended byte 0
    out.bit(0)
    out.bit(1)
    out.byte(0)
    out.byte(0)
    out.byte(0)
    return out.done()

# ---------------------------------------------------------------- optimal
# Greedy-with-lazy leaves bytes on the table: taking the longest match here can
# force a worse split later. This is a shortest-path parse instead - cost[i] is
# the cheapest way to encode the tail from i, computed backwards, so the parse
# is optimal for this cost model.
#
# Bit costs, straight from the format:
#     literal              1 flag bit  + 1 byte  =  9
#     short  (len 2-5)     4 flag bits + 1 byte  = 12   window 256
#     long   (len 3-9)     2 flag bits + 2 bytes = 18   window 8192
#     long extended (3-256) 2 flag bits + 3 bytes = 26   window 8192
COST_LIT, COST_SHORT, COST_LONG, COST_EXT = 9, 12, 18, 26


def _matches(src):
    """For each position: (short_len, short_dist, long_len, long_dist)."""
    n = len(src)
    out = [(0, 0, 0, 0)] * n
    index = {}
    for i in range(n):
        if i + 1 >= n:
            break
        key = src[i:i + 2]
        sl = sd = ll = ld = 0
        for cand in reversed(index.get(key, ())):
            dist = i - cand
            if dist > LONG_WIN:
                break
            limit = min(EXT_MAX, n - i)
            k = 0
            while k < limit and src[cand + k] == src[i + k]:
                k += 1
            if k > ll:
                ll, ld = k, dist
            if dist <= SHORT_WIN:
                ks = min(k, SHORT_MAX)
                if ks > sl:
                    sl, sd = ks, dist
            if ll >= limit:
                break
        out[i] = (sl, sd, ll, ld)
        index.setdefault(key, []).append(i)
        # cap the chain: distant candidates cannot beat a long match already
        # found, and unbounded chains make this quadratic on repetitive data
        if len(index[key]) > 64:
            del index[key][0]
    return out


def compress_optimal(src: bytes) -> bytes:
    n = len(src)
    if n == 0:
        return compress(src)
    m = _matches(src)
    INF = float('inf')
    cost = [INF] * (n + 1)
    step = [None] * (n + 1)
    cost[n] = 0
    for i in range(n - 1, -1, -1):
        best, bstep = COST_LIT + cost[i + 1], ('lit', 1, 0)
        sl, sd, ll, ld = m[i]
        for L in range(2, min(sl, SHORT_MAX) + 1):
            c = COST_SHORT + cost[i + L]
            if c < best:
                best, bstep = c, ('short', L, sd)
        top = min(ll, LONG_MAX)
        for L in range(3, top + 1):
            c = COST_LONG + cost[i + L]
            if c < best:
                best, bstep = c, ('long', L, ld)
        for L in range(LONG_MAX + 1, ll + 1):
            c = COST_EXT + cost[i + L]
            if c < best:
                best, bstep = c, ('ext', L, ld)
        cost[i], step[i] = best, bstep

    out = _Out()
    i = 0
    while i < n:
        kind, L, dist = step[i]
        if kind == 'lit':
            out.bit(1)
            out.byte(src[i])
        elif kind == 'short':
            out.bit(0); out.bit(0)
            v = L - 2
            out.bit((v >> 1) & 1); out.bit(v & 1)
            out.byte((-dist) & 0xFF)
        else:
            off = (0x10000 - dist) & 0xFFFF
            out.bit(0); out.bit(1)
            b0 = off & 0xFF
            top = ((off >> 8) - 0xE0) & 0x1F
            if kind == 'long':
                out.byte(b0)
                out.byte((top << 3) | (L - 2))
            else:
                out.byte(b0)
                out.byte(top << 3)
                out.byte(L - 1)
        i += L
    out.bit(0); out.bit(1)
    out.byte(0); out.byte(0); out.byte(0)
    return out.done()

def compress(src: bytes) -> bytes:
    """Whichever parse is smaller. Both are verified by round-trip in tests."""
    a = compress_greedy(src)
    b = compress_optimal(src)
    return b if len(b) <= len(a) else a
