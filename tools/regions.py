"""Text regions in the ROM and the hardcoded anchors that address them.

Every region here was found by scanning for maximal runs containing no $FF
whose $FE terminators fall at text-like intervals, then confirmed by finding
32-bit pointers to it from executable address ranges.

Anchors matter because the game addresses text two different ways:

  * terminator-scanned - a base plus an index, counted in $FE terminators
    (the routine at $05CCB6). Messages between anchors may be resized.
  * directly pointed   - each entry has its own hardcoded pointer. Some
    regions use a fixed 16-byte stride, others are irregular.

Treating every code-referenced address as a fixed anchor covers both: a
fixed-stride region simply yields fixed-size segments, which enforces the
record width for free.
"""
import struct

# (start, end) of each confirmed text region in the deinterleaved ROM.
# 0x18D360 is excluded: it matches the text profile but has no code
# references, so its boundaries and purpose are unverified.
# (start, end, terminator). The terminator is per region: the two item regions
# end messages with $FE, but the name tables use $FF. That is not a guess - the
# copy loop at $0444C4 reads the small table until $FF and writes $FE only into
# its RAM copy:
#
#     0444C4  lea ($2AA1F0).l,a0     ; ROM table
#     0444CA  lea ($FFF500).w,a1     ; RAM, 11 slots of $80 bytes
#     0444D6  move.b (a0)+,d0
#     0444D8  cmpi.b #$FF,d0         ; <- ROM terminator
#     0444E2  move.b #$FE,(a3)       ; <- RAM terminator, written by the copy
#
# Counted over the data: the big table holds 285 $FF and zero $FE, the item
# name region 308 $FE and zero $FF. Appending new regions rather than inserting
# them keeps region indices - and therefore entry ids - stable.
REGIONS = [
    (0x2ABEFF, 0x2AC911, 0xFE),   # item / equipment names   308 messages
    (0x2ADF23, 0x2AF268, 0xFE),   # item descriptions        211 messages
    # Starts at $280CB0, not $280CB5. A byte search for ライラ lands on $280CB5
    # because ルディ occupies the five bytes before it; taking that hit as the
    # base silently drops the first entry. $FF filler runs up to $280CAF.
    (0x280CB0, 0x2815D4, 0xFF),   # party/class/enemy/skill names  286 entries
    (0x2AA1F0, 0x2AA271, 0xFF),   # party names again, copied to $FFF500
]

# Rejected after audit - these were previously listed as confirmed text on the
# strength of having hardcoded pointers into them. That test was too weak: a
# pointer proves a region is *addressed*, not that it holds text. Three
# independent checks say otherwise.
#
#   region          68k opcodes/KB   popcount<=1   dakuten marks
#   047E83-048D3A            15.0           44%               0
#   04A637-04AFE0            98.5           45%               0
#   071BE0-071E50            62.4           23%               9
#   1FF141-1FF3BB             0.0           40%               5 (20% invalid)
#   2AB0C4-2AB3EA             5.1           53%               3
#   2AB988-2ABC9B             9.1           23%              49
#   -- kept --
#   2ABEFF-2AC911             0.0            2%             312
#   2ADF23-2AF268             0.4           17%             408
#
# The clinching signal is dakuten density. 047E83 and 04A637 contain 6 KB with
# not one voiced kana between them, which cannot happen in Japanese prose;
# their bytes merely land inside the table's range. Disassembly confirms it -
# they decode as `lea $71D4E,a0` / `jsr $57750` and similar.
#
# Note that byte-level round-trip is NOT a usable discriminator: unmapped
# bytes survive as {XX} escapes, so code regions round-trip perfectly too.
REJECTED = [
    (0x047E83, 0x048D3A), (0x04A637, 0x04AFE0), (0x071BE0, 0x071E50),
    (0x1FF141, 0x1FF3BB), (0x2AB0C4, 0x2AB3EA), (0x2AB988, 0x2ABC9B),
]

# Address ranges that hold executable code, used to reject coincidental
# pointer-shaped bytes inside graphics blobs.
CODE = [(0x200, 0x70000), (0x280000, 0x2A0000)]


def _in_code(o):
    return any(a <= o < b for a, b in CODE)


# Opcodes whose next longword is a 32-bit absolute address or immediate.
# An anchor is only real if some reference is actually an operand of one of
# these. Two weaker tests were tried first and both admit false anchors:
#
#   * any byte offset - the original test. 68000 operands are always even
#     aligned, so odd hits cannot be pointers. This invented 7 anchors in
#     region 1 alone.
#   * any EVEN offset - still wrong. $2AC210 and $2AC58B both appear at even
#     offsets inside code, preceded by $0000002A: the four-byte window
#     straddles two unrelated longwords. Compare $2AC4E6, where all twelve
#     hits are preceded by a genuine `lea ($2AC4E6).l,aN`.
#
# A false anchor is not harmless. Segments are the spans between anchors, so
# an invented one imposes a size limit the game does not enforce and makes a
# translation look over budget when it is not.
OPERAND_OPS = set()
for _n in range(8):
    OPERAND_OPS.add(0x41F9 | (_n << 9))     # lea (xxx).l,An
    OPERAND_OPS.add(0x203C | (_n << 9))     # move.l #imm,Dn
    OPERAND_OPS.add(0x207C | (_n << 9))     # movea.l #imm,An
OPERAND_OPS |= {0x4EB9, 0x4EF9}             # jsr / jmp (xxx).l


def references(rom, addr):
    """Every in-code site whose operand is exactly `addr`."""
    out = []
    pat = addr.to_bytes(4, 'big')
    start = 0
    while True:
        o = rom.find(pat, start)
        if o < 0:
            break
        start = o + 2
        if o % 2 or not _in_code(o) or o < 2:
            continue
        # A text region can sit inside a CODE range - the big name table does -
        # so a run of text bytes could look like an operand and get rewritten.
        # Text never holds genuine pointers, so exclude the regions themselves.
        if any(lo <= o < hi for lo, hi, _ in REGIONS):
            continue
        if int.from_bytes(rom[o - 2:o], 'big') in OPERAND_OPS:
            out.append(o)
    return out


def build(rom):
    """[(region_index, start, end, [anchors])] for every region.

    One pass over the executable ranges collects candidates for all regions at
    once; each is then confirmed by finding a real operand reference.
    """
    found = {i: {lo} for i, (lo, _, _) in enumerate(REGIONS)}
    unpack = struct.Struct('>I').unpack_from
    for a, b in CODE:
        b = min(b, len(rom) - 4)
        for o in range(a, b, 2):                     # operands are even
            if int.from_bytes(rom[o - 2:o], 'big') not in OPERAND_OPS:
                continue
            v = unpack(rom, o)[0]
            for i, (lo, hi, _) in enumerate(REGIONS):
                if lo <= v < hi:
                    # A region may sit inside a CODE range - the big name table
                    # does - so a pointer-shaped window within the region's own
                    # bytes could invent an anchor. Only accept references from
                    # outside the region itself.
                    if lo <= o < hi:
                        break
                    found[i].add(v)
                    break
    return [(i, lo, hi, term, sorted(found[i]))
            for i, (lo, hi, term) in enumerate(REGIONS)]


def segments_for(anchors, hi):
    """Spans between consecutive anchors; the last runs to the region end."""
    pts = sorted(set(anchors)) + [hi]
    return [(pts[k], pts[k + 1]) for k in range(len(pts) - 1)]
