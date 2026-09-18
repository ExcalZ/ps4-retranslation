"""Code assignment for the English 8x8 low bank, and the packer that uses it.

The low bank is 128 tiles addressed as codes $00-$7F. What is available:

    $00        space                       keep
    $01-$65    kana                        101 free
    $66-$77    window frame, arrows,
               dakuten marks, dot, slash   KEEP - the UI still draws these
    $78-$7F    narrow H/P/T duplicates,
               the ori-chou ligature,
               re, n, small tsu, blank     8 free

So 109 codes are assignable. This map uses 82 and leaves 27 for the enemy and
battle-action tables later.

Why ligatures are NOT given ps4.tbl text entries
------------------------------------------------
table.py resolves text by greedy longest match, so the moment "an" exists as a
table entry every "an" in the bank encodes as that glyph - in item names, in
skill names, everywhere - not just in the technique names it was chosen for.
That is the wrong default: skills are abbreviated to <=8 cells precisely so they
need no pairing, and item names were never part of the ligature solve.

So ps4.tbl carries single letters only, which keeps plain text round-tripping,
and the ligature and party glyphs are reached by code. Packing policy is applied
per table at build time by pack() below, not by the table's match order.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))

# a-z land at $01+i, matching english.py's convention for the dialogue font so
# the two encoders do not disagree about where lowercase lives.
LOWER = {chr(ord('a') + i): 0x01 + i for i in range(26)}
UMLAUT = {'ü': 0x1B}

# Small-caps ligatures for the technique table, $1C upward.
TECH_LIGS = ('ab ag an ar as at ce ch ck eg eh er es ev fe gr hr ig im in '
             'is ke kk ne oc ra ro sa ta te').split()
LIG = {p: 0x1C + i for i, p in enumerate(TECH_LIGS)}

# creep glyphs for the party-name field, after the ligatures.
PARTY_KEYS = ('Fa Fo Fr Ha La Py Ra Ru Sh Si Th am dy en es hn il ja ke ra rr '
              'a l s y').split()
_base = max(LIG.values()) + 1
PARTY = {k: _base + i for i, k in enumerate(PARTY_KEYS)}

RESERVED_UI = set(range(0x66, 0x78))

# Punctuation.  '!' '?' and '-' are the ROM's own glyphs: they live in the high
# bank, which the font install never rewrites, and the JP staff already used ー
# as a hyphen themselves in "HEADーON" and "AXVー２５".
#
# A Japanese font has no ASCII period, comma or apostrophe -- it has 。 and 、,
# which read as circles in English prose -- so those three are drawn by
# lowerfont.punct() into low-bank codes.  The numbers match wincharset.asm, so
# the prerendered tables and the dynamic field text agree about where
# punctuation lives rather than each picking its own slots.
HIGH_PUNCT = {'!': 0xB1, '?': 0xB2, '-': 0xB0}
DRAWN = {'.': 0x53, "'": 0x54, ',': 0x55}
SPACE = 0x00


def assigned():
    """{code: (kind, key)} for every code this map claims."""
    out = {}
    for ch, c in LOWER.items():
        out[c] = ('letter', ch)
    for ch, c in UMLAUT.items():
        out[c] = ('letter', ch)
    for k, c in LIG.items():
        out[c] = ('lig', k)
    for k, c in PARTY.items():
        out[c] = ('party', k)
    for ch, c in DRAWN.items():
        out[c] = ('punct', ch)
    return out


def check():
    """Raise if the map overlaps the UI block, space, or itself."""
    a = assigned()
    n = len(LOWER) + len(UMLAUT) + len(LIG) + len(PARTY) + len(DRAWN)
    if len(a) != n:
        raise ValueError(f'{n - len(a)} code collision(s) in the slot map')
    bad = sorted(c for c in a if c in RESERVED_UI or c == SPACE or c > 0x7F)
    if bad:
        raise ValueError('codes land on reserved tiles: '
                         + ' '.join(f'${c:02X}' for c in bad))
    free = [c for c in range(0x01, 0x80)
            if c not in a and c not in RESERVED_UI]
    return {'used': len(a), 'free': len(free), 'spare_codes': free}


# --------------------------------------------------------------- packing

def _pairs_for(word, budget, ligs):
    """Indices into word[1:] to merge, using only as many pairs as needed."""
    need = max(0, len(word) - budget)
    rest = word[1:]
    ink = {'i': 1, 'l': 2, 't': 3, 'f': 3, 'r': 3, 's': 3, 'a': 3, 'e': 3,
           'o': 3, 'c': 3, 'h': 3, 'k': 3, 'v': 3, 'm': 5, 'w': 6}
    opts = sorted(((i, rest[i:i + 2]) for i in range(len(rest) - 1)
                   if rest[i:i + 2] in ligs),
                  key=lambda t: ink.get(t[1][0], 4) + ink.get(t[1][1], 4))
    chosen, used = [], set()
    for i, _ in opts:
        if len(chosen) >= need:
            break
        if i in used or i + 1 in used:
            continue
        chosen.append(i)
        used.update({i, i + 1})
    return sorted(chosen)


def pack(word, table):
    """Encode a name to bytes under the policy for `table`.

    'party'      creep, fully paired two glyphs per cell
    'technique'  small caps, paired only as far as the 5-cell budget forces
    'plain'      small caps, one glyph per cell (skills, items, locations)
    """
    if table == 'party':
        parts = [word[i:i + 2] for i in range(0, len(word) - 1, 2)]
        if len(word) % 2:
            parts.append(word[-1])
        missing = [p for p in parts if p not in PARTY]
        if missing:
            raise KeyError(f'{word}: no party glyph for {missing}')
        return bytes(PARTY[p] for p in parts)

    out = bytearray([_code(word[0])])
    rest = word[1:]
    merge = _pairs_for(word, 5, LIG) if table == 'technique' else []
    i = 0
    while i < len(rest):
        if i in merge:
            out.append(LIG[rest[i:i + 2]]); i += 2
        else:
            out.append(_code(rest[i])); i += 1
    return bytes(out)


def _code(ch):
    if ch == ' ':
        return SPACE
    if ch in LOWER:
        return LOWER[ch]
    if ch in UMLAUT:
        return UMLAUT[ch]
    if ch in DRAWN:
        return DRAWN[ch]
    if ch in HIGH_PUNCT:
        return HIGH_PUNCT[ch]
    if ch.isupper():
        return 0x80 + (ord(ch) - ord('A'))      # existing high-bank capitals
    if ch.isdigit():
        return 0x9A + (ord(ch) - ord('0'))
    raise KeyError(f'no code for {ch!r}')


def save(path=None):
    path = path or os.path.join(HERE, '..', 'work', 'slotmap.json')
    data = {'lower': LOWER, 'umlaut': UMLAUT, 'lig': LIG, 'party': PARTY}
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)
    return path


if __name__ == '__main__':
    info = check()
    print(f"codes used {info['used']}, free {info['free']}")
    print('spare: ' + ' '.join(f'${c:02X}' for c in info['spare_codes']))
    print('saved ' + save())
