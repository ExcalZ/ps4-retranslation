"""Prerender menu name tables into 4bpp tile strips.

Composition is done here, once, instead of at runtime: the same algorithm
VWFMenu_DrawString runs, lifted out of the frame budget.  What that buys is
not pixels - the glyphs are identical - but the deletion of the allocator,
the sweep and the save/remap layer that shared, content-keyed pool tiles
made necessary.  A strip belongs to exactly one name, so a window can own
its tiles outright and hand them back when it closes.

Padding is deliberately NOT baked in.  A name shorter than its budget is
padded at draw time by pointing the spare nametable entries at the blank
tile at $680.  That keeps a1 advancing the full budget per row - which is
what every relative-positioned control-code handler in the engine depends
on, `move.w d2, -$80(a1)` and friends - while VRAM only pays for cells that
actually carry ink.

Emits into ps4disasm/vwf/:
    menustrips.bin    concatenated 4bpp tiles, in table order
    menustripidx.bin  per name: word tile offset, byte cell count, byte pad
    menustripmap.bin  table address -> strip index (see below)
    menunames.bin     the same names as menu-charset text, $FE-terminated,
                      for the vwf_menu_strips=0 build, which composes them
                      at runtime instead of copying the art
    menunameidx.bin   per name: word byte offset into menunames.bin
"""
import json, math, os, sys

INK, PAPER = 0xF, 0xE
OUT = "ps4disasm/vwf"

# (segment, label, stock cell budget, ROM symbol).  Budgets are the engine's,
# not ours - a strip may be shorter but must never be longer.
#
# The game finds a name by walking $FE terminators forward from the table
# base, `id - 1` times (loc_193C), so entry N of a table is entry N of its
# script segment: the mapping is positional and 1:1.  That is asserted
# against the built ROM below rather than assumed, because assuming an
# address here is exactly what went wrong before.
#
# InventoryNames2 is a second copy of the item names that differs only in
# which code it uses for the hyphen.  Same rendered text, so it aliases the
# same strips instead of duplicating 160 names' worth of tiles.
TABLES = [("00:001", "items",       10, "InventoryNames"),
          ("00:002", "techniques",   7, "TechniqueNames"),
          ("00:003", "skills",       8, "SkillNames"),
          ("00:004", "locations",   10, "PlaceNames"),
          ("00:001", "items alias", 10, "InventoryNames2")]

ROM = "ps4disasm/ps4built.bin"
LST = "ps4disasm/ps4.lst"


def symbols():
    """Every symbol address in the listing, so a table's extent is known."""
    import re
    out = {}
    for line in open(LST, encoding="utf-8", errors="replace"):
        m = re.match(r"\S*\s*\d+/\s*([0-9A-F]{6}) :\s+([A-Za-z_][A-Za-z0-9_]*):", line)
        if m:
            out.setdefault(m.group(2), int(m.group(1), 16))
    return out


def rom_entry_count(rom, start, limit):
    """Count $FE/$FF-terminated entries between `start` and the next symbol."""
    n, i = 0, start
    while i < limit:
        if rom[i] >= 0xFE:
            n += 1
        i += 1
    return n

face  = open(os.path.join(OUT, "menufont.bin"),  "rb").read()
width = open(os.path.join(OUT, "menuwidth.bin"), "rb").read()

# The space used to be overridden here, because menuwidth.bin gave it a full
# 8px cell: the runtime draws space-padded strings such as WinTiles_Meseta
# ("        MST"), and narrowing the advance was thought to slide them left.
# It does not - those are chrome, they take the composer's fixed label path,
# and that path never reads a width at all.  menuwidth.bin now carries the
# typographic 3px itself, so take it from there.
#
# Having two numbers was worse than having the wrong one.  This count is what
# trpatch8 previews in the JSON, so while they disagreed the width shown next
# to a name being edited was not the width the runtime composer would give it:
# "Cathode Ray Tube" previewed at 10 cells and composed at 11.
SPACE_ADV = width[0]

code = {' ': 0}
for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"): code[c] = 1 + i
for i, c in enumerate("0123456789"):                 code[c] = 27 + i
for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"): code[c] = 57 + i
code['-'] = 0x31; code['!'] = 0x32; code['?'] = 0x33; code[':'] = 0x34
code['.'] = 0x53; code["'"] = 0x54; code[','] = 0x55
code['ü'] = 0x57

# A strip is pixels, so a name is NOT limited to what the window charset can
# encode - that restriction only binds the text tables.  Characters the
# charset has no code for are synthesised here from a base letter plus an
# overlay.  Rows 0-2 sit above every lowercase glyph, which is where the
# diacritic goes.  Rueckkehr is the one name in the tables that needs this.
SYNTH = {}


def glyph_of(ch, where):
    """Return (8 rows of 1bpp, advance width) for one character."""
    if ch in SYNTH:
        base, overlay = SYNTH[ch]
        c = code[base]
        rows = [face[c * 8 + y] for y in range(8)]
        for y, bits in overlay.items():
            rows[y] |= bits
        return rows, width[c]
    c = code.get(ch)
    if c is None:
        raise KeyError("%r has no glyph (in %r)" % (ch, where))
    if ch == ' ':
        return [0] * 8, SPACE_ADV
    return [face[c * 8 + y] for y in range(8)], width[c]


def compose(text):
    """Return (cells, 1bpp rows) for `text`, laid out proportionally."""
    span = [0] * (8 * 16)               # 16 cells is far past any budget
    cursor = 0
    for ch in text:
        rows, adv = glyph_of(ch, text)
        byte, shift = cursor >> 3, cursor & 7
        for y in range(8):
            bits = rows[y] << 8 >> shift
            span[y * 16 + byte]     |= (bits >> 8) & 0xFF
            span[y * 16 + byte + 1] |=  bits       & 0xFF
        cursor += adv
    return max(1, math.ceil(cursor / 8)), span


def to_4bpp(span, cells):
    """Expand the 1bpp span into `cells` tiles, ink $F on paper $E."""
    out = bytearray()
    for t in range(cells):
        for y in range(8):
            b = span[y * 16 + t]
            for x in (0, 2, 4, 6):
                hi = INK if b & (0x80 >> x)       else PAPER
                lo = INK if b & (0x80 >> (x + 1)) else PAPER
                out.append((hi << 4) | lo)
    return out


def main():
    d = json.load(open("work/script_translated.json", encoding="utf-8"))
    ent = d["entries"] if isinstance(d, dict) and "entries" in d else d
    segs = {}
    for x in ent:
        segs.setdefault(x.get("segment") or x["id"].rsplit("#", 1)[0], []).append(x)

    rom = open(ROM, "rb").read()
    sym = symbols()
    ends = sorted(set(sym.values()))

    strips, index, bases, report = bytearray(), bytearray(), bytearray(), []
    table_index = {}
    over, mismatch, seen = [], [], {}
    names, nameidx, seen_text = bytearray(), bytearray(), {}
    for seg, label, budget, symbol in TABLES:
        rows = segs.get(seg, [])
        start = sym[symbol]
        limit = next(a for a in ends if a > start)
        found = rom_entry_count(rom, start, limit)
        if found != len(rows):
            mismatch.append((label, symbol, start, found, len(rows)))

        first, worst = len(index) // 4, 0
        bases += first.to_bytes(2, "big")
        for i, x in enumerate(rows):
            table_index[(symbol, i)] = len(index) // 4
            text = x.get("en") or ""
            if text in seen:
                off, cells = seen[text]           # the alias table reuses these
            else:
                cells, span = compose(text)
                off = len(strips) // 32
                strips += to_4bpp(span, cells)
                seen[text] = (off, cells)
            if cells > budget:
                over.append((label, text, cells, budget))
            worst = max(worst, cells)
            index += off.to_bytes(2, "big") + bytes([cells, 0])
            # The composed-name build draws from this text with the runtime
            # composer.  Same charset codes, same width table, so it lands on
            # the same cells the strip above was rendered from.
            if text not in seen_text:
                seen_text[text] = len(names)
                names += bytes(code[ch] for ch in text) + b"\xFE"
            nameidx += seen_text[text].to_bytes(2, "big")
        report.append((label, len(rows), first, worst, budget, symbol, start, found))

    if mismatch:
        for label, symbol, start, found, want in mismatch:
            sys.stderr.write("  COUNT MISMATCH  %-12s %s at $%06X holds %d entries,"
                             " the script has %d\n" % (label, symbol, start, found, want))
        raise SystemExit("the strip index would not line up with the game's tables")

    if over:
        for label, text, cells, budget in over:
            sys.stderr.write("  OVER BUDGET  %-11s %-14r %d cells > %d\n"
                             % (label, text, cells, budget))
        raise SystemExit("%d name(s) exceed their stock cell budget" % len(over))

    # Offset -> strip index, over the contiguous span the five tables occupy.
    # The draw routine gets a0 pointing at an entry, not an id, so this turns
    # that address into an index in constant time: one word per byte of the
    # span, $FFFF where no entry begins.
    lo = min(sym[t[3]] for t in TABLES)
    hi = max(sym[t[3]] for t in TABLES)
    hi = next(a for a in ends if a > hi)
    amap = bytearray([0xFF]) * ((hi - lo) * 2)
    for seg, label, budget, symbol in TABLES:
        a = sym[symbol]
        for i in range(len(segs.get(seg, []))):
            o = (a - lo) * 2
            n = table_index[(symbol, i)]
            amap[o] = (n >> 8) & 0xFF
            amap[o + 1] = n & 0xFF
            while rom[a] < 0xFE:
                a += 1
            a += 1                       # step past the terminator
    want = {}
    for seg, label, budget, symbol in TABLES:
        a = sym[symbol]
        for i in range(len(segs.get(seg, []))):
            want[(a - lo) * 2] = table_index[(symbol, i)]
            while rom[a] < 0xFE:
                a += 1
            a += 1
    got = {o: (amap[o] << 8) | amap[o + 1]
           for o in range(0, len(amap), 2)
           if ((amap[o] << 8) | amap[o + 1]) != 0xFFFF}
    if got != want:
        only_map = sorted(set(got) - set(want))[:5]
        only_tab = sorted(set(want) - set(got))[:5]
        wrong = [o for o in set(got) & set(want) if got[o] != want[o]][:5]
        sys.stderr.write("  MAP MISMATCH  %d marked, %d entries;"
                         " map-only %s table-only %s wrong-index %s\n"
                         % (len(got), len(want), only_map, only_tab, wrong))
        raise SystemExit("the offset map does not match the tables entry for entry")

    open(os.path.join(OUT, "menustripmap.bin"), "wb").write(amap)
    print("menustripmap.bin  %d bytes (span $%06X..$%06X)" % (len(amap), lo, hi))

    assert len(names) < 0x10000, "name text exceeds a word offset"
    open(os.path.join(OUT, "menunames.bin"),     "wb").write(names)
    open(os.path.join(OUT, "menunameidx.bin"),   "wb").write(nameidx)
    open(os.path.join(OUT, "menustrips.bin"),    "wb").write(strips)
    open(os.path.join(OUT, "menustripidx.bin"),  "wb").write(index)
    open(os.path.join(OUT, "menustripbase.bin"), "wb").write(bases)
    for label, n, first, worst, budget, symbol, start, found in report:
        print("  %-11s %3d names  index %3d..%3d  widest %d of %d  %s $%06X ok(%d)"
              % (label, n, first, first + n - 1, worst, budget, symbol, start, found))
    print("menustrips.bin   %d bytes (%d tiles)" % (len(strips), len(strips) // 32))
    print("menustripidx.bin %d bytes (%d entries)" % (len(index), len(index) // 4))
    print("menustripbase.bin %d bytes (%d tables)" % (len(bases), len(bases) // 2))
    print("menunames.bin    %d bytes, menunameidx.bin %d entries"
          % (len(names), len(nameidx) // 2))


if __name__ == "__main__":
    main()
