"""Build the menu VWF pool's slot<->tile maps.

The pool no longer has to be one contiguous run.  A nametable entry is
just an 11-bit tile index, so the pool can also use tiles that sit inside
the frame range but are never referenced - by any savestate, or as an
immediate anywhere in the source.  That buys capacity without relocating
a single frame tile, which would have meant touching 86 immediate sites
plus references computed at runtime.

Emits into ps4disasm/vwf/:
    poolslot.bin  slot -> tile offset from $680   (VWFMENU_SLOTS bytes)
    pooltile.bin  tile offset from $680 -> slot   (128 bytes, $FF = not pool)
"""
import io
import os
import re

BASE = 0x680
# How far VWFMenu_TileSlot reaches, as an offset from $680.  Must match
# VWFMENU_TILESPAN in ps4.constants.asm and cover every tile the pool names.
TILESPAN = 384
# The contiguous run stops at $6C0: $6C1 onward was the fixed lowercase
# font.  It is dead now (see FIELD_FONT_EXTRA) but is appended AFTER the
# established slots rather than folded in here, so slots 0..113 keep the
# tiles every savestate and save-record layout already has.
CONTIG = list(range(0x682, 0x6C1))
# Candidates: unreferenced across the savestate sweep.  That evidence alone is
# NOT sufficient - a savestate can only show what happened to be on screen in
# it, so a tile the code writes by raw index from a menu nobody captured looks
# free.  $6FF was exactly that: the battle skill separator, handed to the pool
# and then overwritten by composed glyphs.
CANDIDATES = [0x6DB, 0x6DC, 0x6DF, 0x6E0, 0x6E1, 0x6E2, 0x6E4, 0x6E5,
              0x6EB, 0x6EC, 0x6ED, 0x6EE, 0x6EF, 0x6F0, 0x6F2, 0x6F6,
              0x6FB, 0x6FC, 0x6FD, 0x6FF]

# Tiles identified by glyph and confirmed dead by four independent checks:
# absent from either plane in every savestate, unmapped by wincharset, and -
# where code does name them - named only by the Japanese voicing path.  These
# bypass the NAMED filter below, so the justification is asserted, not assumed:
# that path is reached only through control codes $F0/$F1, and JP_DEAD checks
# those appear in no name table.
EXTRA = [0x681,                       # 'A'; codes 1-64 are served from $7C0
         0x6D6,                       # nakaguro, charset $56
         0x6EB, 0x6EC,                # frame+dakuten composites, write-only
         0x7EE, 0x7EF,                # standalone dakuten / handakuten
         0x7F4, 0x7F5,                # kuten / touten
         # The remaining four frame+voicing composites.  Held back until the
         # code stopped READING them off the plane; those sites are compiled
         # out under vwf_menu_strips, which the markers below verify.
         0x6EF, 0x6F0, 0x6F1, 0x6F2]

# Composed field chrome no longer reads these duplicate uppercase glyphs.
# Append them after the established 88 slots.  Battle remains capped at those
# first 88 because its sprite art can also occupy this VRAM bank; only the
# field menus may allocate the appended A-Z tiles.
ALPHA_COPY = list(range(0x7C0, 0x7DA))

# The fixed lowercase font - a-r at $6C1-$6D2, s-z at $7F8-$7FF - is dead
# in the field build: the composer now handles any run containing a letter,
# and the surviving fixed paths draw only uppercase, digits and punctuation.
# $6D7 is u-diaeresis; the eight Japanese remnants at $6D8-$6DF
# (the last of the katakana/hiragana leftovers) are likewise unreachable.
# Three of those Japanese tiles are already in SCATTERED, so the union below
# adds exactly 32 field-only slots (114..145): 26 lowercase + u-diaeresis +
# 5 Japanese.  Punctuation $6D3-$6D5, digits and UI glyphs remain out.
# Slots 114..145 are reachable only in the field (VWFMENU_BATTLE_SLOTS=88).
FIELD_FONT_EXTRA = (list(range(0x6C1, 0x6D3)) + [0x6D7] +
                    list(range(0x6D8, 0x6E0)) +
                    list(range(0x7F8, 0x800)))

# $7DA-$7E3 and $7E4-$7ED are TWO complete runs of digits 0-9: the normal set
# and the small/bold set used for HP and TP.  $7EC and $7ED - the 8 and 9 of the
# second run - were taken once because no savestate happened to show an 8 or a 9
# in a small-numeral field, and Rudy's HP rendered as garbage the moment it did.
# A contiguous glyph run is all-or-nothing: siblings being referenced is proof
# the whole run is live, whatever a sample shows.  $7F6/$7F7 are excluded on the
# same principle - $7F7 renders as the text-continue arrow.
_DIGIT_RUNS = set(range(0x7DA, 0x7EE))
assert not (set(EXTRA) & _DIGIT_RUNS), "EXTRA takes a tile from a digit run"
assert not (set(EXTRA) & {0x7F6, 0x7F7}), "EXTRA takes a UI glyph"


ASM = os.path.join("ps4disasm", "ps4.asm")
IMMEDIATE = re.compile(r"#\$0*([0-9A-Fa-f]{3,4})(?![0-9A-Fa-f])")


def tile_of(hexdigits):
    """The tile an immediate names, or None if it does not name one.

    Two shapes only: a bare `#$6xx`, or a nametable word `#$X6xx` whose high
    nibble is an attribute.  Leading zeroes are allowed.  Do NOT reach a tile
    by masking an arbitrary immediate with $7FF - palette values such as
    `#$EEE` and `#$EE0` then masquerade as tiles $6EE and $6E0, which is how
    three separate hand scans of this got the wrong answer.
    """
    h = hexdigits.upper()
    if len(h) == 3 and h[0] == "6":
        return int(h, 16)
    if len(h) == 4 and h[1] == "6":
        return int(h[1:], 16)
    return None


def source_named_tiles(path):
    """{tile: (line number, source text)} for every tile a code immediate names.

    Instruction operands only: comments are stripped and `dc.*` data is
    skipped, so a tile number appearing in a table or an annotation does not
    count.
    """
    found = {}
    with io.open(path, encoding="utf-8", errors="replace") as f:
        for n, line in enumerate(f, 1):
            code = line.split(";", 1)[0]
            if re.search(r"dc\.[bwl]", code):
                continue
            for m in IMMEDIATE.finditer(code):
                t = tile_of(m.group(1))
                if t is not None and BASE <= t <= 0x6FF and t not in found:
                    found[t] = (n, code.strip())
    return found


# Only the candidates are tested against the source.  Inside the contiguous
# run the same numeric range is object-structure fields and palette values -
# `move.w #$6A0, (Palette_Table_Buffer+$56).w`, `addi.w #$6C0, $1E(a4)` - and
# treating those as tile references would delete most of the pool.  A frame
# tile named by an immediate is a real dependency; a $6xx constant stored into
# an object field is not.
NAMED = source_named_tiles(ASM)
EXCLUDED = sorted(t for t in CANDIDATES if t in NAMED and t not in EXTRA)
SCATTERED = [t for t in CANDIDATES if t not in NAMED]

# The voicing path fires on control codes $F0/$F1 only.  If either ever
# appears in a name table, $6EB/$6EC/$7EE/$7EF become live again and EXTRA is
# no longer safe - fail the generation rather than the playtest.
# $6EF-$6F2 are only safe while nothing compares a plane cell against them.
_ps4 = open(ASM, encoding="utf-8", errors="replace").read()
for _marker in ("$6F1 is a pool tile now",
                "$6F2 is a pool tile now",
                "clobber an ordinary item name"):
    assert _marker in _ps4, (
        "a voicing comparison is still live; $6EF-$6F2 are unsafe: " + _marker)
for _f in ("fielditemnames.bin", "fieldtechnames.bin", "fieldskillnames.bin",
           "dialogueitemnames.bin"):
    _p = os.path.join("ps4disasm", "vwf", _f)
    if os.path.exists(_p):
        _d = open(_p, "rb").read()
        assert 0xF0 not in _d and 0xF1 not in _d,             "%s carries a voicing control code; EXTRA is unsafe" % _f

# EXTRA goes last so the first len(CONTIG)+len(SCATTERED) slots keep the tiles
# they already had, which keeps this change to an addition.
tiles = CONTIG + SCATTERED + EXTRA + ALPHA_COPY
tiles += [t for t in FIELD_FONT_EXTRA if t not in tiles]
assert len(set(tiles)) == len(tiles), "duplicate tile in the pool"
assert all(BASE < t < BASE + TILESPAN for t in tiles), "tile beyond TileSlot's reach"

# Word offsets: the pool may now name tiles in the $7C0 bank, and
# $7EC-$680 = 364 does not fit in a byte.  VWFMenu_SlotTile reads these
# with move.w on a doubled index; see VWFMENU_TILESPAN for the reverse
# table's reach, which must cover the highest tile the pool can name.
slot_to_tile = bytearray()
for t in tiles:
    slot_to_tile += (t - BASE).to_bytes(2, 'big')
assert all(t - BASE < TILESPAN for t in tiles), 'tile beyond TILESPAN'
tile_to_slot = bytearray([0xFF] * TILESPAN)
for s, t in enumerate(tiles):
    tile_to_slot[t - BASE] = s

OUT = "ps4disasm/vwf"
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "poolslot.bin"), "wb").write(slot_to_tile)
open(os.path.join(OUT, "pooltile.bin"), "wb").write(tile_to_slot)

# The RECLAIMED tiles must be disjoint from source-named ones.  The contiguous
# run is deliberately exempt: the same numeric range appears there as object
# IDs and coordinates, not nametable cells - `move.w #$690, (a1)` writes an
# object's type field at offset 0 right after Battle_LoadObject, and
# `addi.w #$6C0, $1E(a4)` adds to a position field.  Treating those as tile
# references would delete most of the pool for no reason.  A frame-range tile
# named by an immediate is a real dependency; a $6xx constant stored into an
# object field is not.
assert not (set(SCATTERED) & set(NAMED)), "a reclaimed tile is named in source"

print("pool slots: %d  (%d contiguous + %d reclaimed from the frame range)"
      % (len(tiles), len(CONTIG), len(SCATTERED)))
print("  contiguous $%03X-$%03X" % (CONTIG[0], CONTIG[-1]))
print("  reclaimed  %s" % " ".join("$%03X" % t for t in SCATTERED))
print("  extra      %s" % " ".join("$%03X" % t for t in EXTRA))
print("  excluded   %s   (named by a code immediate)"
      % " ".join("$%03X" % t for t in EXCLUDED))
for t in EXCLUDED:
    n, text = NAMED[t]
    print("     $%03X  ps4.asm:%-7d %s" % (t, n, text[:52]))
print("poolslot.bin %d bytes (2/slot)   pooltile.bin %d bytes"
      % (len(slot_to_tile), len(tile_to_slot)))
