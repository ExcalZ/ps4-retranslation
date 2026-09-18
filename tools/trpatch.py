"""Apply and validate English translations against the dialogue JSON.

Translation happens in batches, so the risk is not one bad line - it is a bad
line landing in a 2131-entry file and not being noticed until a build breaks
hundreds of messages later. Every batch therefore goes through `apply`, which
refuses to write anything if any line in it fails validation.

Three classes of check, in order of how badly they bite:

  charset   english.SLOTS is the whole alphabet the patched font can draw.
            A curly quote or an em dash raises at build time, deep inside
            pack_streams, naming an id and nothing else. Catching it here
            points at the offending character instead.

  tokens    {ctl.*} carry engine operands - portrait ids, delays, and for
            $FA the two bytes the EVENT interpreter reads after the text
            ends. Losing or reordering one desynchronises the event, which
            shows up as a hang or a wrong portrait, not as garbled text.
            {BR}/{ctl.FD} are pure layout and may be re-broken.  {ctl.F5}
            is NOT: it carries the two yes/no branch targets
            freely, since English wraps at different places than Japanese.

  budget    TWO budgets, and the compressed one is not the binding one.

            compressed: what relocation has to place in the arena. Roomy.

            UNCOMPRESSED: each stream is decompressed into a RAM buffer at
            $FF6000 before rendering (lea ($FFFF6000).l,a1 at $051B2A and
            $051C28). Overflow it and the game corrupts RAM and hangs - which
            is exactly what happened to the Piata stream at 8692 bytes. The
            largest stream the original ever loads is 6582 bytes, so that is
            the only ceiling justified by evidence; STREAM_MAX below is set
            slightly under it for margin.
"""
import json, re, sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import english, dialogue

TOK = re.compile(r'\{([^}]*)\}')

# LEGACY BOUND - it does not constrain the current source build.
#
# It belongs to the COMPRESSED path, where a Kosinski tree is decompressed into
# RAM before it can be read.  Pinned by three observations rather than by the
# disassembly, which is ambiguous about what $FF6020-$FF6CE0 are:
#
#   6582 bytes (the original's own maximum)  ends $FF799A   works
#   7534 bytes (tightened Piata)             ends $FF7D6E   works
#   8691 bytes (first Piata attempt)         ends $FF81F3   HANGS
#
# $FF8000 is the most heavily used RAM address above the buffer - 72 loads -
# and is where the working and hanging cases divide.
#
# The source build sets dialogue_uncompressed = 1, and under that option
# DialogueTreesToRAM stores a ROM pointer instead of calling KosDecomp, and
# GetDialogueByID walks that ROM pointer instead of Dialogue_Trees.  Nothing is
# copied to RAM, so nothing can overrun into Plane_A_Buffer.  Confirmed in two
# savestates: Current_Dialogue_Tree held $00208FE2 and $001E1872, both ROM, and
# Saved_Dialogue_Addr is the dword ROM form rather than the word RAM form.
#
# Kept so the compressed path stays checkable, and because a per-stream total
# is still a useful sanity number.  It is NOT a budget for the current build:
# the binding limits there are ROM space (873 KiB free) and the per-page layout
# rules below.
STREAM_MAX = 8192
LAYOUT_TOKENS = {'BR', 'ctl.FD'}


def engine_tokens(text):
    """Tokens that must survive translation, in order.

    Excluded: layout tokens, which a translator may re-break freely, and
    {Kxxx} kanji escapes. A kanji escape is a GLYPH - ordinary text that
    happens to have no entry in the table yet - so replacing it with English
    is exactly what translating does. Counting them as engine data rejected
    every line of the attract-mode prologue.
    """
    out = []
    for body in TOK.findall(text):
        name = body.split(':', 1)[0]
        if name in LAYOUT_TOKENS:
            continue
        if re.fullmatch(r'K[0-9A-Fa-f]{3}', name):
            continue
        out.append(body)
    return out


MAX_ROWS = 2

# The opening narration does NOT go through the dialogue renderer, so the
# half-width patch never reaches it: every character occupies a full 16px cell
# and the line truncates at 16. Caught in-game - "Monsters on the prowl. And"
# rendered as "Monsters on the" and the rest was simply lost.
#
# These entries carry no control codes at all, one line each, and the longest
# original is exactly 16 characters. The empty entry in the middle is the page
# separator. Other full-width text screens probably exist elsewhere in the
# script and will need adding here as they are found.
FULLWIDTH = {0x1D4FB6: range(58, 66)}
# Region 2 ($2ABCE5) is the attract-mode prologue and behaves the same way:
# one line per entry, no breaks, longest original 14 characters.
FULLWIDTH_REGIONS = {2}
# Narration renders with the EN ROM's variable-width dialogue font, taken from
# the disassembly (vwf/diafont.bin + vwf/diawidth.bin). Those advances already
# include the inter-character gap, so a line's width is the plain sum - exact,
# not estimated, which is why the cap is the true 256px with no safety margin.
# The font also has no ';' and no brackets: text can pass the byte budget and
# still have no glyph, so unsupported characters are an error in their own right.
FULLWIDTH_PX = 256
_VWF_FONT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         'ps4disasm', 'vwf', 'diawidth.bin')
_VWF = None


def _vwf():
    global _VWF
    if _VWF is None:
        idx = {' ': 0}
        for i, c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
            idx[c] = 1 + i
        for i, c in enumerate('abcdefghijklmnopqrstuvwxyz'):
            idx[c] = 27 + i
        for c, i in zip(".',·:!?", range(53, 60)):
            idx[c] = i
        idx['-'] = 60
        idx['"'] = 61
        idx['%'] = 63
        for i, c in enumerate('0123456789'):
            idx[c] = 64 + i
        try:
            w = open(_VWF_FONT, 'rb').read()
        except OSError:
            w = b''
        _VWF = (idx, w)
    return _VWF


def line_px(text):
    """Rendered width of one narration line, in pixels."""
    idx, w = _vwf()
    if not w:
        return len(text) * 6.370
    return sum(w[idx[c]] for c in text if c in idx)


def vwf_missing(text):
    """Characters the EN narration font has no glyph for."""
    idx, _ = _vwf()
    return sorted({c for c in text if c not in idx})


def _fullwidth_limit(entry):
    if entry.get('region') in FULLWIDTH_REGIONS:
        return FULLWIDTH_PX
    r = FULLWIDTH.get(entry.get('stream'))
    if r is None:
        return None
    suf = entry['id'].rsplit('#', 1)[1]
    return FULLWIDTH_PX if suf.isdigit() and int(suf) in r else None


def _rows_per_page(en):
    """Rendered rows on each page, splitting on $FD/$F5."""
    out = []
    # F7 closes the current text window before the following staged line.  It
    # remains an engine token (and therefore must be preserved), but for layout
    # it is just as decisive a page boundary as FD/F5.
    # Allow operands: $F5 carries its two branch targets, so the token is
    # {ctl.F5:0001} and a bare-token pattern silently stops splitting there
    # - every yes/no message then measures as one long page.
    for page in re.split(r'\{(?:ctl\.FD|ctl\.F5|ctl\.F7)(?::[^}]*)?\}', en):
        rows, px = 1, 0
        for seg in re.split(r'(\{BR\}|\n)', page):
            if seg in ('{BR}', '\n'):
                rows += 1; px = 0; continue
            for ch in TOK.sub('', seg):
                px += line_px(ch)
                if px >= FULLWIDTH_PX:
                    rows += 1; px -= FULLWIDTH_PX
        out.append(rows)
    return out


def _dialogue_line_widths(en):
    """Pixel width of each translator-authored row (before engine auto-wrap)."""
    rows = []
    for part in re.split(r'(\{(?:BR|ctl\.FC|ctl\.FD|ctl\.F5|ctl\.F7)(?::[^}]*)?\}|\n)', en):
        if not part or part.startswith('{'):
            continue
        rows.append(line_px(TOK.sub('', part)))
    return rows


# A page ends at a button prompt, a Yes/No prompt, a scene step or a form feed.
PAGE_BREAKS = {'ctl.FD', 'ctl.F5', 'ctl.F7', 'ctl.FC'}


def midpage_speaker_changes(text):
    """Count {ctl.F4} portrait changes that land after text on the same page.

    Changing speaker without a button prompt first overwrites the outgoing
    line before the player can read it.  The original does it anyway in seven
    messages - a reaction shot, where the text is meant to run on - so this is
    counted rather than forbidden, and only a count HIGHER than the JP's is a
    problem.  {ctl.FD} placement is ours (it is a layout token), so introducing
    one of these is a translation bug and not something the data prevents.
    """
    n, pos, seen_text = 0, 0, False
    for m in TOK.finditer(text or ''):
        name = m.group(1).split(':')[0]
        if (text[pos:m.start()] or '').strip():
            seen_text = True
        if name == 'ctl.F4' and seen_text:
            n += 1
            seen_text = False
        elif name in PAGE_BREAKS:
            seen_text = False
        pos = m.end()
    return n


def check_line(entry, en):
    """Return a list of problems with `en` as a translation of entry['jp']."""
    problems = []
    # The window is two rows. A third is not reliably drawn: the row counter
    # masks to 0-1 and the page handler does not always flush in time, which
    # silently ate a line of Laila's opening speech. Originals keep 3910 of
    # their 4561 pages within two rows.
    cap = _fullwidth_limit(entry)
    if cap is not None:
        plains = [TOK.sub('', row) for row in en.splitlines()]
        wide = max((line_px(row) for row in plains), default=0)
        if wide > cap:
            problems.append(f'narration row {wide:.0f}px, holds {cap}px')
        miss = vwf_missing(''.join(plains))
        if miss:
            problems.append('no narration glyph for ' + ' '.join(repr(c) for c in miss))
        if '{BR}' in en:
            problems.append('full-width narration takes one line, no {BR}')
    else:
        wide_rows = [w for w in _dialogue_line_widths(en) if w > FULLWIDTH_PX]
        if wide_rows:
            problems.append(f'dialogue row {max(wide_rows):.0f}px, limit '
                            f'{FULLWIDTH_PX}px (32 cells)')
        over = [i for i, r in enumerate(_rows_per_page(en)) if r > MAX_ROWS]
        if over:
            problems.append(f'page(s) {over} exceed {MAX_ROWS} rows')
    bad = sorted({c for c in TOK.sub('', en) if c not in english.SLOTS and c not in '\r\n'})
    if bad:
        problems.append('illegal chars ' + ' '.join(repr(c) for c in bad))
    want, got = engine_tokens(entry['jp']), engine_tokens(en)
    if want != got:
        problems.append(f'engine tokens changed: {want} -> {got}')
    jp_mid = midpage_speaker_changes(entry['jp'])
    en_mid = midpage_speaker_changes(en)
    if en_mid > jp_mid:
        problems.append(f'{en_mid - jp_mid} speaker change(s) land mid-page '
                        f'that the JP breaks first - add {{ctl.FD}} before '
                        f'the {{ctl.F4}}')
    if '{' in en and en.count('{') != en.count('}'):
        problems.append('unbalanced braces')
    return problems


def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def save(doc, path):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def apply_patch(script_path, patch_path):
    doc = load(script_path)
    entries = doc['entries']
    by_id = {e['id']: e for e in entries}
    patch = load(patch_path)
    if isinstance(patch, dict) and 'entries' in patch:
        patch = patch['entries']

    problems, unknown = [], []
    for eid, en in patch.items():
        e = by_id.get(eid)
        if e is None:
            unknown.append(eid); continue
        for p in check_line(e, en):
            problems.append(f'{eid}: {p}')
    if unknown:
        problems += [f'{i}: no such id' for i in unknown]
    if problems:
        print(f'REFUSING to apply - {len(problems)} problem(s):')
        for p in problems[:40]:
            print('  ' + p)
        return 1

    for eid, en in patch.items():
        by_id[eid]['en'] = en
    save(doc, script_path)
    done = sum(1 for e in entries if (e.get('en') or '').strip())
    print(f'applied {len(patch)} line(s) -> {script_path}')
    print(f'translated now {done}/{len(entries)} ({100*done/len(entries):.1f}%)')
    return 0


def check_all(script_path, budget=False):
    doc = load(script_path)
    entries = doc['entries']
    problems = []
    for e in entries:
        en = (e.get('en') or '').strip()
        if en:
            for p in check_line(e, en):
                problems.append(f'{e["id"]}: {p}')
    done = sum(1 for e in entries if (e.get('en') or '').strip())
    print(f'{done}/{len(entries)} translated ({100*done/len(entries):.1f}%), '
          f'{len(problems)} problem(s)')
    for p in problems[:60]:
        print('  ' + p)
    if budget:
        dt = dialogue.DialogueTable()
        ctrl_rev = {v: k for k, v in dt.ctrl.items()}
        enc = lambda t: english.encode(t, ctrl_rev, dialogue.CTRL_OPERANDS)
        packed, rep = dialogue.pack_streams(entries, dt, en_encode=enc)
        total = sum(len(v) for v in packed.values())
        print(f'compressed script: {total} bytes '
              f'(arena 136021, {136021-total} free)')
        # The binding limit: what each stream expands to in the RAM buffer.
        from collections import defaultdict
        g = defaultdict(int)
        for e in entries:
            if 'stream' not in e:
                continue
            t = (e.get('en') or '').strip()
            try:
                n = len(enc(t)) if t else len(bytes.fromhex(e['hex']))
            except Exception:
                n = len(bytes.fromhex(e['hex']))
            # the tail entry of a stream carries no terminator
            g[e['stream']] += n + (0 if e.get('tail') else 1)
        bad = sorted(((s, n) for s, n in g.items() if n > STREAM_MAX),
                     key=lambda t: -t[1])
        print(f'per-stream totals: max {max(g.values())} '
              f'(legacy compressed-path RAM ceiling {STREAM_MAX}; '
              f'not a limit while dialogue_uncompressed = 1)')
        for s, n in bad:
            print(f'  OVER  stream ${s:06X}: {n} bytes, '
                  f'{n - STREAM_MAX} too many')
        for m in rep['problems'][:20]:
            print('  ' + m)
    return 1 if problems else 0


if __name__ == '__main__':
    if len(sys.argv) >= 4 and sys.argv[1] == 'apply':
        sys.exit(apply_patch(sys.argv[2], sys.argv[3]))
    elif len(sys.argv) >= 3 and sys.argv[1] == 'check':
        sys.exit(check_all(sys.argv[2], budget='--budget' in sys.argv))
    print(__doc__)
    print('usage: trpatch.py apply <dialogue.json> <patch.json>')
    print('       trpatch.py check <dialogue.json> [--budget]')
