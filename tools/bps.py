"""BPS patch encoder and decoder (byuu's beat format), no external tools.

The retranslation stores its dialogue uncompressed, which shifts every byte
past ~$1C0000 relative to the stock ROM, and then extends the image to 4 MB.
A same-offset diff (IPS-style) therefore rewrites more than half the ROM; a
delta encoder that can say "copy N bytes from source offset X" turns the same
change into a patch a fraction of that size.  Flips does this, but is not
installed here and pulling in a binary for one step of the release is worse
than the ~200 lines the format actually needs.

Format (https://github.com/blakesmith/rombp/blob/master/docs/bps_spec.md):

    "BPS1"  source-size  target-size  metadata-size  metadata
    actions...
    source-crc32  target-crc32  patch-crc32          (little-endian u32)

Numbers are 7-bit varints, low group first; the top bit marks the LAST byte,
and every non-final group is stored minus one so no value has two encodings.
Each action is a varint holding (length - 1) << 2 | command:

    0 SourceRead   copy `length` bytes from source at the current output offset
    1 TargetRead   `length` literal bytes follow
    2 SourceCopy   signed varint delta to a running source pointer, then copy
    3 TargetCopy   same, against the output written so far (RLE when delta
                   lands within `length` of the write head)

`apply` is the verification path for `create`: a patch is not written unless
decoding it reproduces the target byte for byte, so a bug in the encoder
fails here rather than on a player's machine.

    python tools/bps.py create SOURCE TARGET PATCH [--meta TEXT]
    python tools/bps.py apply  PATCH SOURCE OUTPUT
    python tools/bps.py info   PATCH
"""
import sys
import zlib

MAGIC = b"BPS1"
SOURCE_READ, TARGET_READ, SOURCE_COPY, TARGET_COPY = range(4)

# Match finder tuning.  KEY bytes are hashed at every STEP-th source position
# and every target position is probed, so any repeat of at least
# KEY + STEP - 1 bytes is found at some alignment and then extended both
# ways.  Shorter repeats fall through to literals, which is fine: a copy costs
# two to five bytes of action overhead and does not pay for itself below that.
KEY = 8
STEP = 4
MIN_COPY = 8        # SourceCopy / TargetCopy pay an offset varint
MIN_READ = 4        # SourceRead does not
CHUNK = 256         # compare in slices before falling back to bytes


# --- varints ----------------------------------------------------------

def encode_num(value: int) -> bytes:
    out = bytearray()
    while True:
        x = value & 0x7F
        value >>= 7
        if value == 0:
            out.append(0x80 | x)
            return bytes(out)
        out.append(x)
        value -= 1


def decode_num(buf: bytes, pos: int):
    value, shift = 0, 1
    while True:
        x = buf[pos]
        pos += 1
        value += (x & 0x7F) * shift
        if x & 0x80:
            return value, pos
        shift <<= 7
        value += shift


def encode_signed(value: int) -> bytes:
    return encode_num((abs(value) << 1) | (1 if value < 0 else 0))


def decode_signed(buf: bytes, pos: int):
    raw, pos = decode_num(buf, pos)
    return (-(raw >> 1) if raw & 1 else raw >> 1), pos


# --- encoder ----------------------------------------------------------

def _extend(a: bytes, i: int, b: bytes, j: int, limit: int) -> int:
    """Length of the common run a[i:], b[j:], at most `limit`."""
    n = 0
    while n + CHUNK <= limit and a[i + n:i + n + CHUNK] == b[j + n:j + n + CHUNK]:
        n += CHUNK
    while n < limit and a[i + n] == b[j + n]:
        n += 1
    return n


def _extend_back(a: bytes, i: int, b: bytes, j: int, limit: int) -> int:
    n = 0
    while n < limit and a[i - n - 1] == b[j - n - 1]:
        n += 1
    return n


def _index(data: bytes, start: int, stop: int, table: dict):
    for i in range(start, stop, STEP):
        if i + KEY <= len(data):
            table[data[i:i + KEY]] = i


def create(source: bytes, target: bytes, metadata: bytes = b"") -> bytes:
    src, tgt = bytes(source), bytes(target)
    ns, nt = len(src), len(tgt)
    out = bytearray(MAGIC)
    out += encode_num(ns) + encode_num(nt) + encode_num(len(metadata)) + metadata

    src_idx: dict = {}
    _index(src, 0, ns, src_idx)
    tgt_idx: dict = {}
    indexed_to = 0                  # target positions below this are in tgt_idx

    src_rel = 0                     # the running pointers the decoder keeps
    tgt_rel = 0
    lit_start = 0                   # start of the pending TargetRead run
    p = 0

    def flush_literal(upto: int):
        nonlocal lit_start
        if upto > lit_start:
            n = upto - lit_start
            out.extend(encode_num(((n - 1) << 2) | TARGET_READ))
            out.extend(tgt[lit_start:upto])
        lit_start = upto

    while p < nt:
        slack = p - lit_start       # literal bytes a match may take back
        best_len, best_cmd, best_off, best_back = 0, None, 0, 0

        # 1. Same offset in the source: cheapest action, no offset to store.
        if p < ns and src[p] == tgt[p]:
            n = _extend(src, p, tgt, p, min(ns, nt) - p)
            if n >= MIN_READ:
                best_len, best_cmd, best_off = n, SOURCE_READ, p

        # 2. Anywhere in the source.
        if p + KEY <= nt:
            key = tgt[p:p + KEY]
            s = src_idx.get(key)
            if s is not None:
                n = _extend(src, s, tgt, p, min(ns - s, nt - p))
                b = _extend_back(src, s, tgt, p, min(s, slack))
                if n + b > best_len + best_back and n + b >= MIN_COPY:
                    best_len, best_cmd, best_off, best_back = n, SOURCE_COPY, s, b
            # 3. Earlier in the target (also covers runs, via overlap).
            t = tgt_idx.get(key)
            if t is not None:
                n = _extend(tgt, t, tgt, p, nt - p)
                b = _extend_back(tgt, t, tgt, p, min(t, slack))
                if n + b > best_len + best_back and n + b >= MIN_COPY:
                    best_len, best_cmd, best_off, best_back = n, TARGET_COPY, t, b
            elif p > 0 and tgt[p] == tgt[p - 1]:
                # A byte run not yet indexed (e.g. the $FF pad): copy from
                # one behind the write head.
                n = _extend(tgt, p - 1, tgt, p, nt - p)
                if n > best_len and n >= MIN_COPY:
                    best_len, best_cmd, best_off, best_back = n, TARGET_COPY, p - 1, 0

        if best_cmd is None:
            p += 1
            continue

        start = p - best_back
        length = best_len + best_back
        flush_literal(start)
        if best_cmd == SOURCE_READ:
            out.extend(encode_num(((length - 1) << 2) | SOURCE_READ))
        elif best_cmd == SOURCE_COPY:
            off = best_off - best_back
            out.extend(encode_num(((length - 1) << 2) | SOURCE_COPY))
            out.extend(encode_signed(off - src_rel))
            src_rel = off + length
        else:
            off = best_off - best_back
            out.extend(encode_num(((length - 1) << 2) | TARGET_COPY))
            out.extend(encode_signed(off - tgt_rel))
            tgt_rel = off + length
        p = start + length
        lit_start = p
        if p > indexed_to:
            _index(tgt, indexed_to - indexed_to % STEP, p, tgt_idx)
            indexed_to = p
    flush_literal(nt)

    out += zlib.crc32(src).to_bytes(4, "little")
    out += zlib.crc32(tgt).to_bytes(4, "little")
    out += zlib.crc32(out).to_bytes(4, "little")
    return bytes(out)


# --- decoder ----------------------------------------------------------

def info(patch: bytes) -> dict:
    if patch[:4] != MAGIC:
        raise ValueError("not a BPS patch")
    pos = 4
    ns, pos = decode_num(patch, pos)
    nt, pos = decode_num(patch, pos)
    nm, pos = decode_num(patch, pos)
    meta = patch[pos:pos + nm]
    pos += nm
    return {
        "source_size": ns, "target_size": nt, "metadata": meta,
        "actions_start": pos,
        "source_crc": int.from_bytes(patch[-12:-8], "little"),
        "target_crc": int.from_bytes(patch[-8:-4], "little"),
        "patch_crc": int.from_bytes(patch[-4:], "little"),
    }


def apply(patch: bytes, source: bytes) -> bytes:
    hdr = info(patch)
    if zlib.crc32(patch[:-4]) != hdr["patch_crc"]:
        raise ValueError("patch is corrupt (CRC32 mismatch)")
    if len(source) != hdr["source_size"] or zlib.crc32(source) != hdr["source_crc"]:
        raise ValueError("source ROM does not match the patch (size %d, CRC32 %08X expected)"
                         % (hdr["source_size"], hdr["source_crc"]))
    nt = hdr["target_size"]
    tgt = bytearray(nt)
    pos, end = hdr["actions_start"], len(patch) - 12
    out = src_rel = tgt_rel = 0
    while pos < end:
        data, pos = decode_num(patch, pos)
        cmd, length = data & 3, (data >> 2) + 1
        if cmd == SOURCE_READ:
            tgt[out:out + length] = source[out:out + length]
            out += length
        elif cmd == TARGET_READ:
            tgt[out:out + length] = patch[pos:pos + length]
            pos += length
            out += length
        elif cmd == SOURCE_COPY:
            delta, pos = decode_signed(patch, pos)
            src_rel += delta
            tgt[out:out + length] = source[src_rel:src_rel + length]
            src_rel += length
            out += length
        else:
            delta, pos = decode_signed(patch, pos)
            tgt_rel += delta
            if tgt_rel + length <= out:
                tgt[out:out + length] = tgt[tgt_rel:tgt_rel + length]
                out += length
                tgt_rel += length
            else:
                # Overlapping copy: byte by byte, as the spec defines it.
                for _ in range(length):
                    tgt[out] = tgt[tgt_rel]
                    out += 1
                    tgt_rel += 1
    if out != nt:
        raise ValueError("patch produced %d bytes, header says %d" % (out, nt))
    if zlib.crc32(tgt) != hdr["target_crc"]:
        raise ValueError("output CRC32 mismatch")
    return bytes(tgt)


# --- cli --------------------------------------------------------------

def main(argv):
    if len(argv) >= 4 and argv[0] == "create":
        source = open(argv[1], "rb").read()
        target = open(argv[2], "rb").read()
        meta = b""
        if "--meta" in argv:
            meta = argv[argv.index("--meta") + 1].encode("utf-8")
        patch = create(source, target, meta)
        if apply(patch, source) != target:
            sys.exit("encoder self-check failed: patch does not reproduce the target")
        open(argv[3], "wb").write(patch)
        print("%s: %d bytes (source %d -> target %d), verified"
              % (argv[3], len(patch), len(source), len(target)))
    elif len(argv) == 4 and argv[0] == "apply":
        patch = open(argv[1], "rb").read()
        source = open(argv[2], "rb").read()
        out = apply(patch, source)
        open(argv[3], "wb").write(out)
        print("%s: %d bytes, CRC32 %08X" % (argv[3], len(out), zlib.crc32(out)))
    elif len(argv) == 2 and argv[0] == "info":
        h = info(open(argv[1], "rb").read())
        for k in ("source_size", "target_size"):
            print("%-12s %d" % (k, h[k]))
        for k in ("source_crc", "target_crc", "patch_crc"):
            print("%-12s %08X" % (k, h[k]))
        print("metadata     %r" % h["metadata"])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
