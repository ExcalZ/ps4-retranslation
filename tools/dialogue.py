"""Dialogue script extract / reinsert.

Separate from script_io.py, which handles the 8x8 bank. The dialogue stream
uses a different, mixed-width encoding driven by the renderer at $06AE1E:

    $00-$DF   single byte  -> index into the 16x16 kana table at $2A3452
    $E0-$EF   two bytes    -> (b0<<8 | b1) & $0FFF indexes the kanji table
                              at $1F62BA
    $F0-$FF   control code -> 16 handlers dispatched from $06AEA6

Kanji are emitted as {Kxxx} escapes rather than characters: identifying all
4096 glyphs would mean reading them off the font sheet one by one, and a
placeholder round-trips exactly while leaving the door open to fill them in
later. Unknown bytes become {XX} the same way.
"""
import json, os, re

KANA_TABLE = 0x2A3452
KANJI_TABLE = 0x1F62BA
GLYPH_BYTES = 32

KANJI_LO, KANJI_HI = 0xE0, 0xEF
CTRL_LO = 0xF0

# Control codes that consume operand bytes from the script stream. Read off the
# dispatcher at $06AE32: it does andi.w #$F,d5 / add d5,d5 / add d5,d5 /
# jmp (94,pc,d5.w), so the branch table is 16 BRA.w entries at $06AEA6.
#
#   $F2 -> $06AEE8  moveq #0,d0 / move.b (a0)+,d0, then sub-dispatches through
#                   a second table at $06A652        -> 1 operand byte
#   $F4 -> $06AEFE  moveq #0,d0 / move.b (a0)+,d0    -> 1 operand byte
#   $FA -> TextCtrlCode_CheckEventFlag in ps4.asm  -> 2 operand bytes:
#                   move.b (a0)+,d0 / jsr EventFlags_Test - operand 1 is an
#                   event flag id; if it is set, move.b (a0),d0 / jsr
#                   GetOffsetByID skips forward operand-2 messages ($FF
#                   terminators, counted from the current position - a
#                   RELATIVE hop, not an absolute id: $01 means "the next
#                   message"); if clear, both bytes are stepped over and the
#                   text keeps drawing.  (An earlier reading of this code as
#                   "ends the text, bytes read by the event interpreter" was
#                   wrong.)
#
# Without this, those operands decoded as ordinary kana: 1176 bytes of
# parameter data appeared as stray characters inside sentences. Applying
# exactly these three widths drops the count of bytes with no table entry from
# 45 to 0, which is the check that pins the widths down - $D9 and $DA occur in
# the script ONLY as the first operand byte of $FA.
CTRL_OPERANDS = {0xF2: 1, 0xF4: 1, 0xF5: 2, 0xF9: 1, 0xFA: 2}

# $F5 is the yes/no prompt, and it is NOT pure layout.  TextCtrlCode_YesNo
# ends with
#
#     move.b  (a0,d0.w), d0     ; d0 is 0 for yes, 1 for no
#     lea     $2(a0), a0
#     jsr     (GetOffsetByID).l
#
# so the two bytes after it are the branch targets - like $FA, RELATIVE hops:
# GetOffsetByID counts $FF terminators from the byte after the operands, so
# $00 continues inline and $01 jumps to the next message.  Modelling it
# as zero-operand decoded them as text, and far worse dropped them on the way
# back out - leaving the engine to read the first two characters of the
# following English as message ids.  Answering the Dorin information dealer
# jumped into the middle of the Tonoe cutscene.
#
# All 27 sites agree with the disassembly: every pair is $00-$04, and not one
# byte is above $40, which text would produce constantly.

# $F9 is a delay: move.b (a0)+,d7 / subq.b #1,d7 / jsr ($041638) / dbf d7.
#
# $F2 is variable. Its byte selects a sub-handler through the table at
# $06A652, and three of the thirteen read a further byte themselves:
#
#     #3  $06A6D0    #4  $06A6E6    #11 $06A858
#
# The others open with movem.l ...a0...,-(a7) and restore a0 on the way out,
# so anything they read leaves the script pointer where it was. Reading the
# handlers without checking that distinction over-counts: a saved/restored a0
# consumes nothing from the caller's point of view.
# Sub-handler $00 takes TWO further bytes, which the widths above missed. They
# decoded as a space plus one kana glued to the front of a line - visible as
# ' こ', ' さ', ' し' running in gojuon order through the Birth Valley cutscene.
# Read as a big-endian word instead, the 165 sites hold values $000A..$017F,
# 163 of them distinct and 97 of the 164 steps exactly +1: an id allocated in
# script order, not text. The rollover is visible in the decode too - once the
# low byte passes the kana bank the high byte ticks from $00 to $01 and the
# pair prints as 'あル', 'あレ', 'あロ'.
#
# This one is worse than a cosmetic mis-decode. The bytes round-trip fine while
# they sit in the `jp` string, so extraction looked correct; but a translator
# replacing that line drops them, and 330 bytes of event ids go with it.
F2_SUB_EXTRA = {0x00: 2, 0x03: 1, 0x04: 1, 0x0B: 1}


def ctrl_width(data, i):
    """Operand bytes belonging to the control code at data[i]."""
    b = data[i]
    w = CTRL_OPERANDS.get(b, 0)
    if b == 0xF2 and i + 1 < len(data):
        w += F2_SUB_EXTRA.get(data[i + 1], 0)
    return w
DEFAULT_TBL = os.path.join(os.path.dirname(__file__), 'ps4_dialogue.tbl')

# Confirmed dialogue. The earlier bounds (0x2AC800-0x2AE000) overlapped two
# regions already validated as 8x8 text - item names at 0x2ABEFF-0x2AC911 and
# item descriptions at 0x2ADF23-0x2AF268 - so 221 bytes of 8x8 text were being
# mis-parsed as dialogue. The corrected span sits cleanly between them.
#
# The two encodings separate sharply: the 8x8 regions contain ZERO bytes in
# $E0-$EF and ZERO $FF bytes, so they cannot masquerade as dialogue. Adjacent
# spans were tested and rejected: 0x2AB0C3-0x2ABEFF averages 44.6 chars per
# message, impossible for a 16x2 box (max 32), and 0x2AF268 onward holds no
# kanji at all.
REGIONS = [
    (0x2AC911, 0x2ADF23),   # first region
    (0x1E2A6E, 0x1E3200),   # second region - found from a LIVE script pointer
    # Third region: UI strings then the attract-mode prologue, dialogue-encoded
    # but sitting immediately before the 8x8 item bank at $2ABEFF, which is why
    # neither the 8x8 scan nor the LZSS sweep ever saw it. Found by searching
    # the ROM for narration vocabulary outside every known stream.
    #
    #   $2ABCE5-$2ABD4D  planet names, "found an item", "found meseta"
    #   $2ABD4D-$2ABEF5  the prologue shown during attract mode
    #
    # Like the opening narration it is FULL WIDTH: one line per entry, no line
    # breaks, and the longest original line is 14 characters.
    (0x2ABCE5, 0x2ABEFF),
]
# The second region was located empirically: a breakpoint on the glyph selector
# $06A9FA halted with a0 = $001E2A6E. Note a0 is sometimes a ROM address and
# sometimes RAM ($FFFF3B31 was seen earlier), so the game reads script from both
# - some straight out of ROM, some staged in a work buffer.
#
# This region uses control codes $F4 and $FD, which the first region never does.
# An earlier scan filtered on the control set observed in region 1 alone and so
# would have rejected this one; that filter was over-fitted to a single sample.


class DialogueTable:
    def __init__(self, path=DEFAULT_TBL):
        self.dec, self.enc, self.ctrl = {}, {}, {}
        self.kanji, self.kanji_rev = {}, {}
        if os.path.exists(path):
            self.load(path)

    def load(self, path):
        for ln in open(path, encoding='utf-8'):
            ln = ln.rstrip('\n')
            if not ln.strip() or ln.lstrip().startswith('#'):
                continue
            ctrl = ln.startswith('*')
            if ctrl:
                ln = ln[1:]
            if '=' not in ln:
                continue
            h, text = ln.split('=', 1)
            h = h.strip()
            if h.startswith('K') and len(h) == 4:      # kanji: K<3 hex digits>
                try:
                    ki = int(h[1:], 16)
                except ValueError:
                    continue
                self.kanji[ki] = text
                self.kanji_rev.setdefault(text, ki)
                continue
            try:
                code = int(h, 16)
            except ValueError:
                continue
            if ctrl:
                self.ctrl[code] = text
            else:
                self.dec[code] = text
                self.enc.setdefault(text, code)

    def decode(self, data: bytes) -> str:
        out, i = [], 0
        while i < len(data):
            b = data[i]
            if b >= CTRL_LO:
                w = min(ctrl_width(data, i), len(data) - i - 1)
                name = self.ctrl[b] if b in self.ctrl else '%02X' % b
                ops = data[i + 1:i + 1 + w]
                suffix = ':' + ops.hex().upper() if w else ''
                out.append('{%s%s}' % (name, suffix))
                i += 1 + w
            elif KANJI_LO <= b <= KANJI_HI:
                if i + 1 >= len(data):
                    out.append('{%02X}' % b); i += 1; continue
                idx = ((b << 8) | data[i + 1]) & 0x0FFF
                out.append(self.kanji.get(idx, '{K%03X}' % idx))
                i += 2
            else:
                out.append(self.dec[b] if b in self.dec else '{%02X}' % b)
                i += 1
        return ''.join(out)

    def encode(self, text: str) -> bytes:
        rev = {v: k for k, v in self.ctrl.items()}
        out, i = bytearray(), 0
        while i < len(text):
            if text[i] == '{':
                j = text.index('}', i)
                tok = text[i + 1:j]
                ops = b''
                if ':' in tok:                     # control with operands
                    tok, oh = tok.split(':', 1)
                    ops = bytes.fromhex(oh)
                if tok.startswith('K') and len(tok) == 4:
                    idx = int(tok[1:], 16)
                    # restore the original two-byte form
                    out += bytes([0xE0 | ((idx >> 8) & 0x0F), idx & 0xFF])
                elif tok in rev:
                    out.append(rev[tok])
                    out += ops
                else:
                    out.append(int(tok, 16))
                    out += ops
                i = j + 1
                continue
            ch = text[i]
            if ch in self.kanji_rev:                   # kanji -> two-byte form
                ki = self.kanji_rev[ch]
                out += bytes([0xE0 | ((ki >> 8) & 0x0F), ki & 0xFF])
                i += 1
                continue
            if ch not in self.enc:
                raise KeyError(f'no dialogue table entry for {ch!r}')
            out.append(self.enc[ch])
            i += 1
        return bytes(out)


# LZSS-compressed story script. Each entry is a stream start; the decompressor
# at $041BA0 expands it into the RAM buffer at $FF3000, and the renderer reads
# it from there. Found by sweeping $1C0000-$1E0000 and validating the output as
# dialogue - every one has zero invalid kanji indices.
#
# Start addresses matter exactly: an LZSS stream never references before its
# own start, so a wrong start makes back-references underflow the output.
# lzss.py now RAISES on that; it used to substitute a zero byte, and $00
# decodes to a space, so wrong starts silently ate characters instead of
# failing.
#
# That silent failure is also why the first sweep found only 8 streams: bad
# starts validated as plausible dialogue, so the scan accepted them and
# skipped past the real ones. Re-sweeping with the strict decompressor found
# 26, cross-checked against the addresses that game code actually loads.
#
# Streams are reached three ways, none of which is a single table:
#   move.l #<stream>,d0 ; jsr ($05402C).l   - literal in event code
#   jsr ($05402A).l followed by an inline longword
#   movea.l ($FFECF8).w,a0 ; move.l (a0),d0 - first field of an area descriptor
# and $058970 indexes a small table at $058A50 by the byte at $FFF400.
#
# Consecutive spans sit 0-15 bytes apart with no overlaps.
STREAMS = [
    0x1CC476, 0x1CD2E6, 0x1CE546, 0x1CF6D6, 0x1D02D6, 0x1D1256, 0x1D2426,
    0x1D38E6, 0x1D4446, 0x1D4FB6, 0x1D5A26, 0x1D6816, 0x1D76C6, 0x1D85A6,
    0x1D9436, 0x1DA026, 0x1DB036, 0x1DB6F6, 0x1DC4E6, 0x1DD086, 0x1DDD96,
    0x1DEC96, 0x1DFCB6, 0x1E05B6, 0x1E1316, 0x1E1F06,
]


def extract_streams(rom: bytes, tbl: DialogueTable, streams=STREAMS):
    """Decompress each LZSS script stream and split it into messages."""
    import lzss
    entries = []
    for src in streams:
        buf = lzss.decompress(rom, src, limit=0x20000)
        i, idx = 0, 0
        while i < len(buf):
            j = buf.find(b'\xff', i)
            if j < 0:
                break
            raw = buf[i:j]
            # Empty messages (consecutive $FF) MUST be kept. Skipping them
            # drops a terminator each, so a rebuilt stream comes out short and
            # every later message shifts - 12 empties plus a 1-byte tail made
            # the first rebuild 13 bytes light.
            entries.append({
                "id":       f"lz{src:06X}#{idx:04d}",
                "stream":   src,
                "offset":   i,          # offset within the decompressed buffer
                "raw_len":  (j + 1) - i,
                "hex":      raw.hex(),
                "jp":       tbl.decode(raw),
                "en":       "",
                "note":     "",
            })
            idx += 1
            i = j + 1
        if i < len(buf):                # bytes after the final terminator
            raw = buf[i:]
            entries.append({
                "id":       f"lz{src:06X}#tail",
                "stream":   src,
                "offset":   i,
                "raw_len":  len(raw),
                "hex":      raw.hex(),
                "jp":       tbl.decode(raw),
                "en":       "",
                "note":     "trailing bytes, no terminator",
                "tail":     True,
            })
    return entries


def extract(rom: bytes, tbl: DialogueTable, regions=REGIONS):
    """Split on the $FF terminator; each message keeps its own offset."""
    entries = []
    for ri, (lo, hi) in enumerate(regions):
        i, idx = lo, 0
        while i < hi:
            j = rom.find(b'\xff', i, hi)
            if j < 0:
                break
            raw = rom[i:j]
            if raw:
                entries.append({
                    "id":      f"dlg{ri:02d}#{idx:04d}",
                    "region":  ri,
                    "offset":  i,
                    "raw_len": (j + 1) - i,
                    "hex":     raw.hex(),
                    "jp":      tbl.decode(raw),
                    "en":      "",
                    "note":    "",
                })
                idx += 1
            i = j + 1
    return entries


def save(entries, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({"version": 1, "kind": "dialogue", "entries": entries},
                  f, ensure_ascii=False, indent=2)


def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)["entries"]


def stats(entries):
    kanji = sum(len(re.findall(r'\{K[0-9A-F]{3}\}', e['jp'])) for e in entries)
    raw = sum(len(re.findall(r'\{[0-9A-F]{2}\}', e['jp'])) for e in entries)
    total = sum(len(bytes.fromhex(e['hex'])) for e in entries)
    return {"messages": len(entries), "bytes": total,
            "kanji": kanji, "unmapped": raw}


def reinsert_streams(rom: bytes, entries, tbl: DialogueTable, strict=True,
                     en_encode=None):
    """Rebuild each LZSS stream from its entries, recompress, write in place.

    A rewritten stream must fit the original compressed span, since nothing
    repoints. The compressor currently lands ~1.2% under the originals, so
    there is a little headroom, but a longer translation can still overflow -
    over-long streams are reported and left untouched.
    """
    import lzss, lzss_enc
    out = bytearray(rom)
    report = {"written": 0, "kept": 0, "problems": [], "streams": []}
    groups = {}
    for e in entries:
        if "stream" in e:
            groups.setdefault(e["stream"], []).append(e)

    # The overlaps that used to appear here were an artifact of wrong stream
    # starts, not of two streams genuinely sharing bytes: with the corrected
    # starts the eight compressed spans sit 3-13 bytes apart. The check stays
    # as a guard, since writing a stream that overlaps another would corrupt
    # it, but it should now never fire.
    spans = {}
    for src in groups:
        _, n = lzss.decompress(rom, src, limit=0x20000, with_size=True)
        spans[src] = (src, src + n)
    overlapping = set()
    for a in spans:
        for b in spans:
            if a != b and spans[a][0] < spans[b][1] and spans[b][0] < spans[a][1]:
                overlapping.add(a); overlapping.add(b)

    for src, ents in sorted(groups.items()):
        if src in overlapping:
            report["problems"].append(
                f"stream {src:06X}: compressed span overlaps another stream, "
                f"skipped to avoid corrupting it")
            continue
        _, avail = lzss.decompress(rom, src, limit=0x20000, with_size=True)
        plain = bytearray()
        for e in sorted(ents, key=lambda x: x["offset"]):
            text = e.get("en", "").strip()
            enc = None
            if text:
                # English uses its own encoder: the Japanese table is the
                # canonical DECODER for `jp` and must not be repurposed, or
                # every untranslated line loses its meaning.
                try:
                    enc = (en_encode(text) if en_encode else tbl.encode(text))
                except KeyError as ex:
                    report["problems"].append(f'{e["id"]}: {ex}')
            if enc is None:
                enc = bytes.fromhex(e["hex"])
                report["kept"] += 1
            else:
                report["written"] += 1
            # the tail entry has no terminator of its own
            plain += enc if e.get("tail") else enc + b'\xff'
        packed = lzss_enc.compress(bytes(plain))
        fits = len(packed) <= avail
        report["streams"].append({"src": src, "avail": avail,
                                  "used": len(packed), "fits": fits})
        if not fits:
            msg = (f"stream {src:06X}: {len(packed)} bytes needed, "
                   f"{avail} available")
            if strict:
                raise ValueError(msg)
            report["problems"].append(msg)
            continue
        out[src:src + len(packed)] = packed
        # leave the tail of the old stream alone; the decoder stops at the
        # terminator, so trailing bytes are unreachable
    return bytes(out), report

def pack_streams(entries, tbl: DialogueTable, en_encode=None):
    """Rebuild and recompress every stream, ignoring the original span.

    Returns {stream address: compressed bytes} plus a report. Used with
    relocate.py, which places the results wherever they fit and remaps the
    decompressor - so a stream is free to outgrow the space it came from.
    """
    import lzss_enc
    groups, report = {}, {"written": 0, "kept": 0, "problems": []}
    for e in entries:
        if "stream" in e:
            groups.setdefault(e["stream"], []).append(e)
    packed = {}
    for src, ents in sorted(groups.items()):
        plain = bytearray()
        for e in sorted(ents, key=lambda x: x["offset"]):
            text = e.get("en", "").strip()
            enc = None
            if text:
                try:
                    enc = (en_encode(text) if en_encode else tbl.encode(text))
                except KeyError as ex:
                    report["problems"].append(f'{e["id"]}: {ex}')
            if enc is None:
                enc = bytes.fromhex(e["hex"]); report["kept"] += 1
            else:
                report["written"] += 1
            plain += enc if e.get("tail") else enc + bytes([0xFF])
        packed[src] = lzss_enc.compress(bytes(plain))
    return packed, report

def layout(data: bytes, half_width=frozenset()):
    """Simulate the renderer: returns (rows_used, longest_line, pages).

    Columns are counted in HALF cells (0..31). A full-width glyph takes two,
    a half-width one takes one, matching the patched renderer; with an empty
    half_width set this reduces to the stock 16-cell geometry.

    Row overflow is NOT treated as an error. 56 messages in the original
    script push the row past the two-row window with explicit $FC breaks, so
    the engine plainly tolerates it; guessing a limit here would be inventing
    a constraint the game does not have. What matters for a translation is
    staying within what the original message already used.
    """
    col = row = 0
    peak_row = 0
    longest = 0
    pages = 1
    i = 0
    while i < len(data):
        b = data[i]
        if b >= CTRL_LO:
            w = ctrl_width(data, i)
            if b == 0xFC:                       # explicit line break
                longest = max(longest, col)
                col = 0; row += 1
            elif b in (0xFD, 0xF5):             # page / scroll
                longest = max(longest, col)
                col = row = 0; pages += 1
            i += 1 + w
        else:
            if 0xE0 <= b <= 0xEF:
                col += 2; i += 2                # kanji are always full width
            else:
                col += 1 if b in half_width else 2
                i += 1
            if col >= 32:
                longest = max(longest, col)
                col = 0; row += 1
        peak_row = max(peak_row, row)
    longest = max(longest, col)
    return peak_row + 1, longest, pages

# A region that outgrows its span can be moved wholesale, because every way in
# is a longword pointer that region_pointers() can find and rewrite. $0E7600 is
# $FF filler past hwpatch's routines and relocate.py's remap arena.
RELOC_ARENA = {2: (0x0E7600, 0x0E8000)}


def region_pointers(rom: bytes, regions=REGIONS):
    """Find longword pointers whose target lies inside a region.

    Region text is NOT reached by counting terminators the way the streams are:
    the engine holds hardcoded addresses into the middle of the block, so any
    record that changes length silently moves every later entry point. Each hit
    is validated against a record boundary before it is trusted - a longword
    that lands mid-record is data that happens to look like a pointer, and
    rewriting it would corrupt the ROM.
    """
    import struct
    spans = [(lo, hi) for lo, hi in regions]
    hits = []
    for i in range(0, len(rom) - 3, 2):
        v = struct.unpack('>I', rom[i:i + 4])[0]
        for ri, (lo, hi) in enumerate(spans):
            if lo <= v < hi:
                hits.append((i, ri, v))
    return hits


def reinsert_regions(rom: bytes, entries, tbl: DialogueTable,
                     en_encode=None, regions=REGIONS):
    """Write region text back in place. Streams have pack_streams; regions had
    nothing, so anything translated in one was extracted and then silently
    dropped at build time.

    Regions are uncompressed ROM text and nothing repoints them, so each must
    still fit its original span - there is no relocation escape hatch here the
    way there is for the LZSS streams and the 8x8 bank.

    The rebuild walks the original span rather than concatenating the extracted
    records, because extract() skips empty records while the game still counts
    their terminators as indices. Concatenating would silently renumber every
    later entry in the region.
    """
    out = bytearray(rom)
    report = {"written": 0, "kept": 0, "problems": [], "pointers": [],
              "relocated": []}
    moves = {}
    for ri, (lo, hi) in enumerate(regions):
        ents = sorted((e for e in entries if e.get("region") == ri),
                      key=lambda x: x["offset"])
        if not ents:
            continue
        orig = rom[lo:hi]
        buf = bytearray()
        pos = lo
        wrote = 0
        relat = {}                                   # id -> offset within buf
        for e in ents:
            buf += orig[pos - lo:e["offset"] - lo]   # gaps = empty records
            text = (e.get("en") or "").strip()
            enc = None
            if text:
                try:
                    enc = (en_encode(text) if en_encode else tbl.encode(text))
                except Exception as ex:
                    report["problems"].append(f'{e["id"]}: {ex}')
            if enc is None:
                enc = bytes.fromhex(e["hex"])
            else:
                wrote += 1
            relat[e["id"]] = len(buf)
            buf += enc + bytes([0xFF])
            pos = e["offset"] + e["raw_len"]
        # Trailing $FF filler is reclaimable: the pad below rewrites the same
        # byte, so dropping it here turns dead padding into usable slack
        # without changing the output of an untranslated region.
        tail = orig[pos - lo:]
        if set(tail) - {0xFF}:
            buf += tail

        base = lo
        if len(buf) > hi - lo:
            alo, ahi = RELOC_ARENA.get(ri, (0, 0))
            if len(buf) > ahi - alo:
                report["problems"].append(
                    f"region {ri} left unmodified: needs {len(buf)}, "
                    f"span {hi - lo}, arena {ahi - alo}")
                continue
            if set(rom[alo:alo + len(buf)]) - {0xFF}:
                report["problems"].append(
                    f"region {ri} left unmodified: arena {alo:06X} is not free")
                continue
            base = alo
            # the old span keeps its Japanese: nothing points at it any more
            out[alo:alo + len(buf)] = buf
            report["relocated"].append(
                f'region {ri}: {len(buf)} bytes -> {alo:06X} '
                f'(span was {hi - lo})')
        else:
            buf += bytes([0xFF]) * ((hi - lo) - len(buf))
            out[lo:hi] = buf
        report["written"] += wrote
        report["kept"] += len(ents) - wrote
        newoff = {k: base + v for k, v in relat.items()}
        # only regions whose records actually shifted need pointer fixups
        if any(newoff[e["id"]] != e["offset"] for e in ents):
            moves[ri] = newoff
    # rewrite the hardcoded entry points now that records have shifted
    import struct
    for site, ri, target in region_pointers(rom, regions):
        if ri not in moves:
            continue
        for e in sorted((x for x in entries if x.get("region") == ri),
                        key=lambda x: x["offset"]):
            delta = target - e["offset"]
            if not 0 <= delta <= 1:
                continue
            # A +1 target skips a leading space the Japanese never displayed.
            # English puts a real letter in that byte, so aim at the record.
            if delta == 1 and bytes.fromhex(e["hex"])[:1] == bytes([0])                     and (e.get("en") or "").strip():
                delta = 0
            new_t = moves[ri][e["id"]] + delta
            if new_t != target:
                out[site:site + 4] = struct.pack('>I', new_t)
                report["pointers"].append(
                    f'{site:06X}: {target:06X} -> {new_t:06X} ({e["id"]})')
            break
        else:
            report["problems"].append(
                f'{site:06X}: pointer {target:06X} lands mid-record, left alone')
    return bytes(out), report
