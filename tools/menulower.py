"""PARKED - do not wire this in without reading the VRAM note below.

The idea was to give charset codes 65-86 (lowercase i-z, '.', "'", ',') a
second copy in "free" VRAM so the fixed-width path could draw them from there
and $6C1-$6D6 could join the tile pool, exactly as codes 1-64 are served from
the copy at $7C0.

It was wired to $7A1 and it corrupted the field map and blanked chrome labels,
because THERE IS NO FREE VRAM IN THAT BANK.  Measured out of a savestate:

    $700-$77F   Plane B nametable   (SaveRegion already says so)
    $780-$79F   sprite attribute table
    $7A0-$7BF   hscroll table
    $7C0-$7FF   the codes 1-64 font copy

The bytes at $7A1 read as blank in menu savestates only because the hscroll
table is mostly zeroes there; writing art into it is what put font glyphs on
the map.  "Blank in a savestate" is not evidence a tile is free - the same
mistake as $6FF, which tools/menupool.py already warns about.

A real second copy needs 22 tiles that no VDP table owns.  The only candidates
found so far are inside the $7C0 bank itself: codes 37-48 and 53-56 are mapped
by no charset entry, which would be $7E4-$7EF and $7F4-$7F7.  Reaching them
needs poolslot.bin widened from byte to word offsets, since $7E4-$680 exceeds
255.  That is a real change to VWFMenu_SlotTile and its six lookup sites.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decomp, nemcmp

# Font.bin decompresses to 87 tiles, i.e. codes 1-87, so code 88 has no stock
# art at all.  The chrome that must move is codes 65-86 ($6C1-$6D6).
LO, HI = 65, 86                 # charset codes, inclusive
SRC = "ps4disasm/general/art/nemesis/Font.bin"
OUT = "ps4disasm/general/art/nemesis/FontLower.bin"

art = decomp.decompress(open(SRC, "rb").read() + bytes(32), 0)
# Font.bin loads at tile $681 while codes start at $680, so code c is blob c-1.
tiles = art[(LO - 1) * 32:(HI - 1 + 1) * 32]
assert len(tiles) == (HI - LO + 1) * 32, "short read from Font.bin"

packed = nemcmp.compress(tiles)
round_trip = decomp.decompress(packed + bytes(32), 0)[:len(tiles)]
assert round_trip == tiles, "Nemesis round-trip mismatch"

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "wb").write(packed)
print("FontLower.bin: codes %d-%d, %d tiles, %d bytes (from %d raw)"
      % (LO, HI, HI - LO + 1, len(packed), len(tiles)))
