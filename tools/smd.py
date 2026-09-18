"""SMD (Super Magic Drive) <-> raw BIN conversion for Mega Drive ROMs.

SMD layout: 512-byte header, then a series of 16 KiB blocks. Within each block
the first 8 KiB holds the odd-offset bytes of the deinterleaved data and the
second 8 KiB holds the even-offset bytes.
"""
import struct

HEADER_SIZE = 512
BLOCK = 0x4000
HALF = BLOCK // 2


def is_smd(data: bytes) -> bool:
    if len(data) < HEADER_SIZE + BLOCK:
        return False
    # Canonical SMD signature bytes in the 512-byte header.
    return data[8] == 0xAA and data[9] == 0xBB and data[10] == 0x06


def smd_to_bin(data: bytes) -> bytes:
    body = data[HEADER_SIZE:]
    out = bytearray(len(body))
    for base in range(0, len(body), BLOCK):
        blk = body[base:base + BLOCK]
        if len(blk) < BLOCK:
            break
        odd = blk[:HALF]
        even = blk[HALF:]
        chunk = bytearray(BLOCK)
        chunk[0::2] = even
        chunk[1::2] = odd
        out[base:base + BLOCK] = chunk
    return bytes(out)


def bin_to_smd(data: bytes, header: bytes | None = None) -> bytes:
    if header is None:
        header = make_header(len(data))
    out = bytearray(header)
    for base in range(0, len(data), BLOCK):
        chunk = data[base:base + BLOCK]
        if len(chunk) < BLOCK:
            chunk = chunk + b"\x00" * (BLOCK - len(chunk))
        out += bytes(chunk[1::2])   # odd bytes first
        out += bytes(chunk[0::2])   # then even bytes
    return bytes(out)


def make_header(size: int) -> bytes:
    h = bytearray(HEADER_SIZE)
    blocks = size // BLOCK
    h[0] = blocks & 0xFF
    h[1] = (blocks >> 8) & 0xFF
    h[2] = 0x00           # 0 = last file / standalone
    h[8] = 0xAA
    h[9] = 0xBB
    h[10] = 0x06          # 6 = Mega Drive
    return bytes(h)
