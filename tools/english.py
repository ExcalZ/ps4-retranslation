"""English text encoding: slot assignment, font installation, encoder.

The Japanese table (ps4_dialogue.tbl) stays the canonical DECODER - it is what
gives the `jp` field its meaning, and rewriting it would corrupt every
untranslated line. English is a separate ENCODER that maps Latin characters
onto single-byte codes, reusing slots whose Japanese glyph an English script
does not need.

Lowercase has no home in the stock font, so a-z take the first 26 hiragana
slots. Punctuation reuses the Japanese punctuation slots, since the shapes
differ (。 is not a full stop, 、 is not a comma).

Every code here is single-byte, so English costs 1 byte per character against
Japanese's 1.16 - but needs far more characters, which is why stream budgets
are the binding constraint rather than the encoding.
"""
import latinfont

# character -> single-byte code
SLOTS = {' ': 0x00}
for i, c in enumerate('abcdefghijklmnopqrstuvwxyz'):
    SLOTS[c] = 0x01 + i                     # hiragana block, unused in English
SLOTS[';'] = 0x1B
for i, c in enumerate('0123456789'):
    SLOTS[c] = 0x51 + i                     # the font's own digits
SLOTS.update({
    '!': 0xAB,      # ！
    '?': 0xAC,      # ？
    '"': 0xAD,      # 「
    "'": 0xAE,      # ・
    ':': 0xAF,      # ：
    '-': 0xB0,      # ー
    '.': 0xB1,      # 。
    ',': 0xB2,      # 、
    '(': 0xB3,      # （
    ')': 0xD1,      # ）
})
for i, c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    SLOTS[c] = 0xB6 + i                     # the font's own capitals

# codes that must be drawn 8 pixels wide
HALF_WIDTH = sorted(set(SLOTS.values()))


def install_font(rom: bytes):
    """Draw the Latin glyphs into the single-byte font. Returns (rom, count)."""
    import font
    out = bytearray(rom)
    base, n = font.FONTS['kana']
    written = 0
    missing = []
    for ch, code in sorted(SLOTS.items(), key=lambda kv: kv[1]):
        bm = latinfont.bitmap(ch)
        if bm is None:
            missing.append(ch)
            continue
        off = base + code * font.GLYPH_BYTES
        out[off:off + font.GLYPH_BYTES] = font._bitmap_to_glyph(bm)
        written += 1
    if missing:
        raise KeyError('no glyph for ' + repr(missing))
    return bytes(out), written


def encode(text: str, ctrl_rev, ctrl_operands) -> bytes:
    """Encode an English string, passing {tokens} through unchanged.

    ctrl_rev maps a control NAME to its code; ctrl_operands gives operand
    widths so {ctl.F4:01} round-trips with its parameter bytes intact.
    """
    out = bytearray()
    i = 0
    while i < len(text):
        if text[i] == '{':
            j = text.index('}', i)
            tok = text[i + 1:j]
            ops = b''
            if ':' in tok:
                tok, oh = tok.split(':', 1)
                ops = bytes.fromhex(oh)
            if tok.startswith('K') and len(tok) == 4:
                idx = int(tok[1:], 16)
                out += bytes([0xE0 | ((idx >> 8) & 0x0F), idx & 0xFF])
            elif tok in ctrl_rev:
                out.append(ctrl_rev[tok])
                out += ops
            else:
                out.append(int(tok, 16))
                out += ops
            i = j + 1
            continue
        ch = text[i]
        if ch not in SLOTS:
            raise KeyError(f'no English slot for {ch!r} '
                           f'(available: {"".join(sorted(SLOTS))!r})')
        out.append(SLOTS[ch])
        i += 1
    return bytes(out)
