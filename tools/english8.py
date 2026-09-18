"""English encoder for the 8x8 system-font bank.

Deliberately NOT a change to ps4.tbl. That table is the canonical DECODER for
the Japanese: codes $01-$65 are kana, and it is what gives every `jp` field its
meaning. Overwriting them with Latin letters would break the decode of all 827
entries and the byte-exact round-trip along with it. english.py takes the same
approach for the 16x16 dialogue font - Japanese table decodes, separate table
encodes - and this is the 8x8 counterpart.

The other reason to keep the letters out of ps4.tbl is packing policy. table.py
resolves text by greedy longest match, so a "an" entry would merge that pair in
every string in the bank: item names, location names, skill names. Skills are
abbreviated to <=8 cells precisely so they need no pairing. Policy therefore
belongs here, chosen per table, not in the table's match order.

    party      creep glyphs, fully paired, two per cell   (4 cells)
    technique  small caps, paired only as far as 5 forces (5 cells)
    plain      small caps, one glyph per cell             (items, skills,
                                                           locations, classes)
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slotmap

# Party names occupy the head of each name table; class and vehicle names
# follow in the same segment, and those are plain.
PARTY_SEGMENTS = {'03:000'}
PARTY_INDEXED = {'02:000': range(0, 11)}
TECHNIQUE_SEGMENTS = {'00:002'}

# Tables drawn by the VWF renderer. Their names must be encoded as PLAIN
# letters: the ligature and creep codes exist only to squeeze glyphs into a
# fixed-pitch cell, and the VWF font has no glyph for them, so a paired name
# renders with the pairs silently missing - "Gifeuer" came out as "Giu".
#
# Set from vwfpatch.VWF_SEGMENTS at build time so the encoder and the renderer
# cannot disagree about which tables are converted. Empty by default, because
# plain encoding overflows the stock renderer's cell budgets.
VWF_SEGMENTS = set()


def policy_for(entry):
    seg = entry.get('segment')
    if seg in VWF_SEGMENTS:
        return 'plain'          # the VWF needs no pairing, and cannot draw it
    if seg in TECHNIQUE_SEGMENTS:
        return 'technique'
    if seg in PARTY_SEGMENTS:
        return 'party'
    rng = PARTY_INDEXED.get(seg)
    if rng is not None:
        idx = int(entry['id'].rsplit('#', 1)[1])
        if idx in rng:
            return 'party'
    return 'plain'


TOKEN = re.compile(r'\{([0-9A-Fa-f]{2})\}')


def encode(text, entry):
    """Encode `text` under the policy for the table `entry` belongs to.

    A {XX} token is a raw control byte and passes through untouched -- $FC ends
    a line, and item descriptions are the one table that needs it, being the
    only prose in the 8x8 bank.  Splitting on the token instead of handing it
    to the packer also stops the ligature solver pairing letters across a line
    break, where the two halves are nowhere near each other on screen.
    """
    policy = policy_for(entry)
    out, pos = bytearray(), 0
    for m in TOKEN.finditer(text):
        if m.start() > pos:
            out += slotmap.pack(text[pos:m.start()], policy)
        out.append(int(m.group(1), 16))
        pos = m.end()
    if pos < len(text):
        out += slotmap.pack(text[pos:], policy)
    return bytes(out)


def install_font(rom):
    """Write the regenerated low bank over $2A2B7E. Returns (rom, report)."""
    import decomp, nemcmp, lowerfont, creepfont
    LOW_OFF = 0x2A2B7E
    SPAN = 0x2A303A - LOW_OFF
    data = bytearray(decomp.decompress(rom, LOW_OFF))
    INK, BG = 0xF, 0xE

    def put(code, grid):
        off = code * 32
        for y in range(8):
            for x in range(0, 8, 2):
                hi = INK if grid[y][x] else BG
                lo = INK if grid[y][x + 1] else BG
                data[off + y * 4 + x // 2] = (hi << 4) | lo

    for ch, code in slotmap.LOWER.items():
        put(code, lowerfont.glyph(ch, smallcap=True))
    for ch, code in slotmap.UMLAUT.items():
        put(code, lowerfont.glyph(ch, smallcap=True))
    for pair, code in slotmap.LIG.items():
        put(code, lowerfont.ligature(pair, smallcap=True))
    for key, code in slotmap.PARTY.items():
        put(code, creepfont.bitmap(key))
    for ch, code in slotmap.DRAWN.items():
        put(code, lowerfont.punct(ch))

    blob = nemcmp.compress(bytes(data))
    if len(blob) > SPAN:
        raise ValueError(f'low bank needs {len(blob)} bytes, span is {SPAN}')
    if decomp.decompress(blob, 0) != bytes(data):
        raise ValueError('low bank failed its Nemesis round-trip')
    out = bytearray(rom)
    out[LOW_OFF:LOW_OFF + len(blob)] = blob
    # Leave whatever followed inside the old span alone; the decompressor stops
    # on the tile count in the header, so trailing bytes are never read.
    return bytes(out), {'glyphs': len(slotmap.assigned()),
                        'bytes': len(blob), 'span': SPAN,
                        'free': SPAN - len(blob)}
