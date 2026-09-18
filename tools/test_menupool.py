"""Guard the menu VWF pool's capacity and its source-derived exclusions.

`tools/menupool.py` decides which frame tiles the composed pool may use.
Savestate evidence alone is not enough: a savestate only shows what happened
to be on screen in it, so a tile the code writes by raw index from a menu
nobody captured looks free.  $6FF was exactly that - the battle skill
separator, handed to the pool and then overwritten by composed glyphs.

So the generator also scans source, and this pins both the parse rule and the
result.  A new raw tile immediate must shrink the pool and fail the build, not
silently reclaim a tile the game still draws from.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import menupool as M

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ok = True


def check(label, good, detail=""):
    global ok
    ok &= good
    print("  %s %-52s %s" % ("ok  " if good else "FAIL", label, detail))


# ------------------------------------------------------------- the parse rule
# Two shapes name a tile: a bare `#$6xx`, and a nametable word `#$X6xx` whose
# high nibble is an attribute.  Nothing else does.  Reaching a tile by masking
# an arbitrary immediate with $7FF is the trap: palette values then masquerade
# as tiles, which is how three separate hand scans of this got it wrong.
for text, want in (("6FF", 0x6FF),     # bare
                   ("E6EF", 0x6EF),    # attributed word
                   ("16C0", 0x6C0),    # attributed word, low attribute
                   ("06FF", 0x6FF),    # leading zero
                   ("EEE", None),      # palette, not tile $6EE
                   ("EE0", None),      # palette, not tile $6E0
                   ("2700", None)):    # status register
    got = M.tile_of(text)
    check("#$%-5s -> %s" % (text, ("$%03X" % want) if want else "not a tile"),
          got == want, "" if got == want else "got %r" % got)

# The immediate must be the WHOLE hex run.  `move.l #$96FD9580, (a6)` is a VDP
# constant; matching its "96FD" prefix stole $6FD out of the pool.
check("a longer constant yields no tile from its prefix",
      not M.IMMEDIATE.search("\tmove.l\t#$96FD9580, (a6)"),
      "#$96FD9580")
check("a real immediate still matches",
      M.IMMEDIATE.search("\tmove.w\t#$6FF, -$6(a1)") is not None)

# ------------------------------------------------------------ the result
# All six frame+voicing composites are now taken via EXTRA.  $6E0 and $6FF stay
# out: $6E0 is reached by `addi.w #$6E0` and $6FF is the battle skill separator.
EXPECTED = [0x6E0, 0x6FF]
check("the exclusion set is exactly the two still-named tiles",
      M.EXCLUDED == EXPECTED,
      " ".join("$%03X" % t for t in M.EXCLUDED))
check("no reclaimed tile is named in source",
      not (set(M.SCATTERED) & set(M.NAMED)))
font_new = [t for t in M.FIELD_FONT_EXTRA
            if t not in M.CONTIG + M.SCATTERED + M.EXTRA + M.ALPHA_COPY]
check("capacity is %d contiguous + %d reclaimed + %d extra + %d alphabet + %d font" %
      (len(M.CONTIG), len(M.SCATTERED), len(M.EXTRA), len(M.ALPHA_COPY), len(font_new)),
      len(M.tiles) == len(M.CONTIG) + len(M.SCATTERED) + len(M.EXTRA)
      + len(M.ALPHA_COPY) + len(font_new),
      "%d slots" % len(M.tiles))
check("the complete duplicate uppercase alphabet is reclaimed",
      M.ALPHA_COPY == list(range(0x7C0, 0x7DA)),
      " ".join("$%03X" % t for t in M.ALPHA_COPY))
# The established 114 slots keep their tiles: 63 contiguous, 13 scattered, 12
# extra, then the alphabet - savestates and save records index by slot.
check("the contiguous run still stops at $6C0",
      M.CONTIG == list(range(0x682, 0x6C1)))
check("slot 0..113 keep the established order",
      M.tiles[:114] == M.CONTIG + M.SCATTERED + M.EXTRA + M.ALPHA_COPY)
check("the 32 dead font tiles are the field-only tail (slots 114..145)",
      M.tiles[114:] == font_new and len(font_new) == 32
      and set(font_new) == set(range(0x6C1, 0x6D3)) | {0x6D7}
      | set(range(0x6D8, 0x6E0)) - {0x6DB, 0x6DC, 0x6DF} | set(range(0x7F8, 0x800)),
      " ".join("$%03X" % t for t in M.tiles[114:]))

# The assembly constant must agree with what the generator emitted, or the ROM
# indexes a pool of one size while every budget check assumes another.
constants = open(os.path.join(ROOT, "ps4disasm", "ps4.constants.asm"),
                 encoding="utf-8", errors="replace").read()
declared = int(re.search(r"^VWFMENU_SLOTS\s*=\s*(\d+)", constants, re.M).group(1))
check("VWFMENU_SLOTS matches the generated pool",
      declared == len(M.tiles), "%d declared, %d generated" % (declared, len(M.tiles)))

slot = open(os.path.join(ROOT, "ps4disasm", "vwf", "poolslot.bin"), "rb").read()
check("poolslot.bin is that many word entries",
      len(slot) == len(M.tiles) * 2, "%d bytes" % len(slot))

# The contiguous run is deliberately exempt from the source rule: the same
# numeric range appears there as object IDs and coordinates rather than
# nametable cells.  Assert that exemption is still only about those, so a real
# tile reference landing inside the run cannot hide behind it.
inside = sorted(t for t in M.NAMED if M.CONTIG[0] <= t <= M.CONTIG[-1])
check("contiguous-range names are known false positives",
      all(re.search(r"\b(addi?\.w|move\.w)\b", M.NAMED[t][1]) for t in inside),
      "%d immediate(s) inside $%03X-$%03X" % (len(inside), M.CONTIG[0], M.CONTIG[-1]))

# EXTRA bypasses the NAMED filter, so its justification must stay in the tree:
# the voicing path is unreachable only while no name table carries $F0/$F1.
src_mp = open(os.path.join(ROOT, "tools", "menupool.py"),
              encoding="utf-8").read()
check("EXTRA is gated on the voicing path being unreachable",
      "0xF0 not in _d and 0xF1 not in _d" in src_mp)
# $6EF-$6F2 were read BACK off the plane and rewritten.  They are only safe
# while all three of those sites are compiled out; menupool.py asserts the same
# thing at generation time, and this pins it from the other side.
ps4 = open(os.path.join(ROOT, "ps4disasm", "ps4.asm"),
           encoding="utf-8", errors="replace").read()
for marker in ("$6F1 is a pool tile now", "$6F2 is a pool tile now",
               "clobber an ordinary item name"):
    check("voicing read-back neutralised: %s" % marker[:28], marker in ps4)

print("ALL PASS" if ok else "FAILURES ABOVE")
sys.exit(0 if ok else 1)
