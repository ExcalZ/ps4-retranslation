"""Character table for PS4 script encoding.

The byte->glyph mapping is data, not code: edit ps4.tbl to refine it.
Format, one entry per line:  HH=text        (HH = hex byte)
                             HHHH=text      (two-byte code, for F0/F1 banks)
Lines starting with # are comments. '=' may map to multi-char strings.

Control codes are declared separately with a leading '*':
    *FE=END      message terminator
"""
import os

DAKUTEN, HANDAKUTEN = 0xF0, 0xF1
DEFAULT_TBL = os.path.join(os.path.dirname(__file__), 'ps4.tbl')

# $F0/$F1 are combining marks that occupy their own tile and precede the kana
# they modify. Compose them on decode so the script reads naturally, and split
# them again on encode so the bytes round-trip exactly.
# Explicit base sets. A range test cannot be used here: Unicode interleaves
# the voiced forms (HA BA PA HI BI PI ...), so "ha <= c <= ho" would wrongly
# admit BE as a base and decompose PE into a character the font has no tile
# for. Only these bases exist as plain glyphs in the ROM.
_DAKU_BASES = ("かきくけこさしすせそたちつてとはひふへほ"
               "カキクケコサシスセソタチツテトハヒフヘホ")
_HANDAKU_BASES = "はひふへほハヒフヘホ"
_SPECIAL = {('う', DAKUTEN): 'ゔ', ('ウ', DAKUTEN): 'ヴ'}

_FWD = dict(_SPECIAL)
for _b in _DAKU_BASES:
    _FWD[(_b, DAKUTEN)] = chr(ord(_b) + 1)
for _b in _HANDAKU_BASES:
    _FWD[(_b, HANDAKUTEN)] = chr(ord(_b) + 2)
_REV = {v: k for k, v in _FWD.items()}          # composed -> (base, mark)


def _compose(base, mark):
    return _FWD.get((base, mark))


def _decompose(ch):
    """voiced char -> (mark, base char), or None."""
    hit = _REV.get(ch)
    return (hit[1], hit[0]) if hit else None


class Table:
    def __init__(self, path=DEFAULT_TBL):
        self.dec = {}      # int code -> str
        self.enc = {}      # str -> int code
        self.ctrl = {}     # int code -> name
        if os.path.exists(path):
            self.load(path)

    def load(self, path):
        for ln in open(path, encoding='utf-8'):
            ln = ln.rstrip('\n')
            if not ln.strip() or ln.lstrip().startswith('#'):
                continue
            ctrl = False
            if ln.startswith('*'):
                ctrl = True
                ln = ln[1:]
            if '=' not in ln:
                continue
            hexpart, text = ln.split('=', 1)
            hexpart = hexpart.strip()
            try:
                code = int(hexpart, 16)
            except ValueError:
                continue
            if ctrl:
                self.ctrl[code] = text
            else:
                self.dec[code] = text
                # first mapping wins on the encode side (avoids ambiguity)
                self.enc.setdefault(text, code)

    def decode(self, data: bytes):
        """bytes -> list of (code, text) tokens."""
        out = []
        i = 0
        while i < len(data):
            b = data[i]
            if b in (DAKUTEN, HANDAKUTEN) and i + 1 < len(data):
                merged = _compose(self.dec.get(data[i + 1]), b)
                if merged is not None:
                    out.append(((b << 8) | data[i + 1], merged))
                    i += 2
                    continue
            code = b
            i += 1
            if code in self.ctrl:
                out.append((code, '{%s}' % self.ctrl[code]))
            elif code in self.dec:
                out.append((code, self.dec[code]))
            else:
                out.append((code, '{%0*X}' % (4 if code > 0xFF else 2, code)))
        return out

    def decode_str(self, data: bytes) -> str:
        return ''.join(t for _, t in self.decode(data))

    def encode(self, text: str) -> bytes:
        """text -> bytes. Understands {XX}/{XXXX} raw escapes and {NAME} controls."""
        rev_ctrl = {v: k for k, v in self.ctrl.items()}
        out = bytearray()
        i = 0
        while i < len(text):
            if text[i] == '{':
                j = text.index('}', i)
                tok = text[i + 1:j]
                if tok in rev_ctrl:
                    code = rev_ctrl[tok]
                else:
                    code = int(tok, 16)
                if code > 0xFF:
                    out += bytes([code >> 8, code & 0xFF])
                else:
                    out.append(code)
                i = j + 1
                continue
            # voiced kana: emit the combining mark, then the plain base
            split = _decompose(text[i])
            if split is not None and split[1] in self.enc:
                mark, base = split
                out.append(mark)
                out.append(self.enc[base])
                i += 1
                continue
            # longest-match on table text
            for L in (3, 2, 1):
                frag = text[i:i + L]
                if frag in self.enc:
                    code = self.enc[frag]
                    if code > 0xFF:
                        out += bytes([code >> 8, code & 0xFF])
                    else:
                        out.append(code)
                    i += L
                    break
            else:
                raise KeyError(f'no table entry for {text[i]!r} at offset {i}')
        return bytes(out)
