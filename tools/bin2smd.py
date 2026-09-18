"""Convert a raw Mega Drive ROM (.bin) to Super Magic Drive format (.smd), or back.

SMD layout: 512-byte header, then the ROM split into 16 KiB blocks. Within each
block the first 8 KiB holds the odd-addressed bytes and the second 8 KiB holds
the even-addressed bytes.

usage: python tools/bin2smd.py in.bin [out.smd]
       python tools/bin2smd.py in.smd [out.bin]   (direction chosen by extension)
"""
import sys
from pathlib import Path

BLOCK = 16384
HALF = BLOCK // 2


def bin_to_smd(data: bytes) -> bytes:
    if len(data) % BLOCK:
        data += b"\xff" * (BLOCK - len(data) % BLOCK)
    blocks = len(data) // BLOCK
    hdr = bytearray(512)
    hdr[0] = blocks & 0xFF
    hdr[1] = 0x03
    hdr[8] = 0xAA
    hdr[9] = 0xBB
    hdr[10] = 0x06
    out = bytearray(hdr)
    for i in range(blocks):
        blk = data[i * BLOCK:(i + 1) * BLOCK]
        out += blk[1::2] + blk[0::2]
    return bytes(out)


def smd_to_bin(data: bytes) -> bytes:
    body = data[512:]
    out = bytearray()
    for i in range(len(body) // BLOCK):
        blk = body[i * BLOCK:(i + 1) * BLOCK]
        merged = bytearray(BLOCK)
        merged[1::2] = blk[:HALF]
        merged[0::2] = blk[HALF:]
        out += merged
    return bytes(out)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    src = Path(argv[1])
    data = src.read_bytes()
    if src.suffix.lower() == ".smd":
        dst = Path(argv[2]) if len(argv) > 2 else src.with_suffix(".bin")
        dst.write_bytes(smd_to_bin(data))
    else:
        dst = Path(argv[2]) if len(argv) > 2 else src.with_suffix(".smd")
        dst.write_bytes(bin_to_smd(data))
    print(f"{src} -> {dst} ({dst.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
