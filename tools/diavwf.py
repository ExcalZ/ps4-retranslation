"""Generate VWF tables for the 8x16 dialogue font (Art_DiaFont).

Emits, into ps4disasm/vwf/:
  diafont.bin  80 glyphs x 16 bytes, left-normalised (ink starts at x=0)
  diawidth.bin 80 bytes, advance in pixels
  nibexp.bin   256 x 8 x 8 bytes: for byte b at nibble-shift k,
               two longs (hi, lo) that OR onto the 4bpp buffer.

The OR works because the dialogue box is pre-filled with paper $E and
ink is $F: $E | $1 == $F, so setting the low bit of a nibble turns
paper into ink. Idempotent, and needs no read-modify-write.
"""
import os, sys

SRC = "ps4disasm/general/art/uncompressed/DiaFont.bin"
OUT = "ps4disasm/vwf"
NGLYPH = 80
TRACK = 1     # pixels of side bearing added to every inked glyph
SPACE = 4     # advance for the blank glyph ($00)

art = open(SRC, "rb").read()
assert len(art) == NGLYPH * 16, len(art)

font = bytearray()
width = bytearray()
report = []
for g in range(NGLYPH):
    gl = art[g*16:(g+1)*16]
    lo, hi = 8, -1
    for b in gl:
        for x in range(8):
            if b >> (7-x) & 1:
                lo = min(lo, x); hi = max(hi, x)
    if hi < 0:                       # blank glyph
        font += bytes(16); width.append(SPACE); report.append((g, 0, 0)); continue
    font += bytes(((b << lo) & 0xFF) for b in gl)   # strip left bearing
    w = hi - lo + 1
    width.append(w + TRACK)
    report.append((g, lo, w + TRACK))

# nibble-expand table
nib = bytearray()
for b in range(256):
    mask = 0
    for p in range(8):
        if b >> (7-p) & 1:
            mask |= 1 << (4 * (7-p))
    for k in range(8):
        v = (mask << 32) >> (4*k)
        nib += ((v >> 32) & 0xFFFFFFFF).to_bytes(4,"big")
        nib += (v & 0xFFFFFFFF).to_bytes(4,"big")

os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT,"diafont.bin"),"wb").write(font)
open(os.path.join(OUT,"diawidth.bin"),"wb").write(width)
open(os.path.join(OUT,"nibexp.bin"),"wb").write(nib)

print("diafont.bin  %5d bytes" % len(font))
print("diawidth.bin %5d bytes" % len(width))
print("nibexp.bin   %5d bytes" % len(nib))
print()
print("widest advance: %d   narrowest inked: %d" % (max(width), min(w for w in width if w>SPACE)))
print("mean advance over A-Za-z: %.2f" % (
    sum(width[g] for g in list(range(1,27))+list(range(0x1B,0x35)))/52.0))
