"""Write our translations into the disassembly's dialogue tree sources.

Engine data comes from the US build; only the words and the line wrapping come
from us. That split matters: our tokens carry JP operands (event ids, portrait
ids) that are only guaranteed correct for the JP ROM, whereas the US tree's own
control bytes are by definition correct for the ROM being built. So each
non-layout token in our text consumes the next engine code from the US message
in order - the pairing the fingerprint match already established - while $FC/$FD
placement and the text itself are ours, because English wraps differently.

A message is only rewritten when our engine-token sequence lines up with the
US one. Anything else is reported and skipped rather than guessed at.

  python tools/treeport.py            report only
  python tools/treeport.py --write    rewrite the tree sources
"""
import io, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dialogue
import kosinski

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, 'ps4disasm', 'script')
LAYOUT = {0xFC: '{BR}', 0xFD: '{ctl.FD}'}
LAYOUT_TOK = {v: k for k, v in LAYOUT.items()}
# characters with no bare-string spelling in the AS charset
LITERAL = {'"': 0x3D, '\u00b7': 0x38}
TOKEN = re.compile(r'\{([^}]*)\}')

# The US dialogue trees have one control that is outside the renderer protocol
# decoded by dialogue.ctrl_width(): $F6 returns to the event interpreter, which
# consumes the following event id word.  It is still engine data and must move
# with the control when a message is rewritten.
TREE_EXTRA_OPERANDS = {0xF6: 2}

# Party Talk runs with Game_Mode_Routine == 4, and TextCtrlCode_Portrait reads
# a SECOND operand byte in that mode only:
#
#     move.b  (a0)+, d0               ; portrait id
#     cmpi.w  #4, (Game_Mode_Routine).w
#     bne.s   loc_6A19E
#     move.b  (a0)+, ($FFFFEC9D).w    ; mode 4 only
#
# So $F4 is three bytes wide in the Party Talk stream and two everywhere else --
# a width that depends on the mode the message is dispatched in, not on
# anything in the bytes. Read at the usual width, that second byte decodes as a
# leading kana ( , い, あ) on the following line, a translator deletes it as
# noise, and at run time the engine eats the first letter of the English
# instead: "Both the principal..." printed as "oth the principal...".
#
# lz1DB6F6 is the Party Talk stream, and the evidence is clean: the byte after
# $F4 xx is below $10 in 173 of 173 cases there, where every other stream is a
# mix of real text.  The stream spans TWO trees - 31 (84 of 84) and 32 (89 of
# 89; 84 + 89 = 173) - and the rule was first applied to 31 alone, so the
# second half of Party Talk went out at the two-byte width and the engine ate
# the first letter again ("hray was Lutz all along", tree 32 $1C).
PARTY_TALK_TREES = (31, 32)
PARTY_TALK_STREAM = 'lz1DB6F6'


def f4_width(tree_or_stream):
    """Operand bytes $F4 carries, which is 2 in Party Talk and 1 elsewhere."""
    return 2 if tree_or_stream in PARTY_TALK_TREES or tree_or_stream == PARTY_TALK_STREAM else 1

# Tried and rejected: restoring rows into US messages the localisers left
# empty, taking operands from the JP. The operands themselves are sound -- $F4
# and $F9 were verified identical across every message both builds kept (1819
# and 39 respectively, with three disagreements that are all US content edits).
# But test_treeport_controls asserts that a tree's assembled controls equal the
# canonical US controls, and writing a control where the US had none breaks
# that invariant. It is the same guard that caught the $00F2 panel lock, and
# there is no evidence the engine ever dispatches to those empty messages, so
# the guard wins. See work/STATUS.md.


# Hand-verified placements, for the cases no rule should be asked to infer.
#
# A heuristic that could reach these would have to be loose enough to misplace
# other rows, and a row written into the wrong message is worse than a message
# left in English.  So they are listed, each with the reason it is here.
#
#   (tree, message index): 'row id'   write that row's text into that message
#   (tree, message index): None       blank the message
#
OVERRIDES = {
    # Rocky the dog relocates if you fail to catch him, so the US carries the
    # scene once per town.  `lz1D2426` has 82 rows and tree 12 wants a copy at
    # index 94, which nothing indexes; the Japanese is one line serving every
    # location, so the same translation belongs here.
    (12, 0x5E): 'lz1D2426#0043',
    #
    # ...and the chase half that precedes it, Monsen's copy.  `twins()` cannot
    # find this one because it only compares the SAME index: the row targets
    # index 76 in tree 13, while Monsen's copy sits at $5D (93) at the very end
    # of tree 12, appended past eight empty slots the way quest text is.  Same
    # fingerprint, same 64 text bytes.
    (12, 0x5D): 'lz1D2426#0076',

    # The US split the two-row ending narration across four messages because
    # English needs the room -- `lz1E1316#0018` and `#0019` fill $12 and $13,
    # leaving these two holding a duplicate of our own closing line.  Blank
    # them or the player reads "and now the curtain rises on a new age" twice.
    (42, 0x14): None,
    (42, 0x15): None,

    # Tree 36 is lz1DDD96's variant and cannot be proved so: it resolves ONE
    # row, on a single {ctl.F4}, and tree 33 matches the same row just as
    # weakly.  That ambiguity is what the group bars exist to reject, so the
    # evidence here is content, checked by hand -- and the indices line up,
    # row #0000 to message $0 and #0011 to $B.
    #
    # $B is Zio's speech before the fight, translated long ago and never once
    # reaching the ROM.
    (36, 0x0B): 'lz1DDD96#0011',
    #
    # $0 -- Zio's death and Frena connecting herself to Nurvus -- is the one
    # message written with OUR controls instead of the US build's, which is
    # what the trailing 'jp' asks for.
    #
    # The whole divergence is three controls.  The Japanese holds three silent
    # beats and cries once:
    #
    #     JP   F9:13 F9:13 F9:13          F2:03B9 F9:27
    #     US   F2:03B9 F9:09 F2:03B9 F9:09 F2:03B9 F9:27
    #
    # The US turned one death cry into three for drama -- confirmed on video
    # both ways, and the other 38 controls of this message, operands included,
    # are byte-identical between the two.  So nothing that dispatches, selects
    # a portrait or ends a scene is in dispute; only a sound effect and its
    # delays.  That also disposes of the usual objection to writing our own
    # controls, that JP operands may be wrong for this ROM: here every other
    # operand already matches the US exactly.
    #
    # This is the only sanctioned deviation from canonical US controls, and
    # test_treeport_controls consults this table so the guard still covers
    # every other message.
    (36, 0x00): ('lz1DDD96#0000', 'jp'),

    # Tree 30 $4E, the bookshelf in the redecorated house (`lz1DB036#0078`):
    # the JP opens with {ctl.F4:01} like the lines either side of it ($4D and
    # $4F both carry F4:01 in the US too), but the US build dropped the
    # portrait from this one message.  Ported under the US controls the row
    # reads with no speaker; write the Japanese controls instead - the single
    # deviation is the portrait the neighbours already show.
    (30, 0x4E): ('lz1DB036#0078', 'jp'),
}


def canonical_engine(n):
    """Engine controls for a tree, read from its untouched US .bin.

    The .asm files are build outputs as well as inputs: once treeport rewrites
    a translated message, reading operands back from that mutable text can
    perpetuate an earlier parser mistake.  The compressed .bin beside each
    source is the immutable US tree and therefore the authority for event ids,
    portrait ids, and panel ids.
    """
    p = os.path.join(SCRIPT, f'dialogue {n}.bin')
    plain = kosinski.decompress(open(p, 'rb').read())
    out, engine, idx, i, message_start = {}, [], 0, 0, 0
    while i < len(plain):
        code = plain[i]
        if code < 0xF0:
            i += 1
            continue
        if code == 0xFF:
            out[idx] = engine
            engine, idx, i = [], idx + 1, i + 1
            message_start = i
            continue
        width = TREE_EXTRA_OPERANDS.get(code, dialogue.ctrl_width(plain, i))
        if code == 0xF4:
            width = f4_width(n)
        ops = tuple(plain[i + 1:i + 1 + width])
        if len(ops) != width:
            raise ValueError(
                f'tree {n} message ${idx:X}: truncated ${code:02X} control')
        if code not in LAYOUT:
            engine.append((code, ops))
        i += 1 + width
    if message_start < len(plain):
        out[idx] = engine
    return out


def jp_engine_full(hexstr, stream=None):
    """[(code, operands)] for a JP row -- jp_engine_codes, keeping operands.

    Only for the OVERRIDES entries that write our controls rather than the US
    build's; everything else takes its engine data from the untouched tree.
    """
    b, out, i = bytes.fromhex(hexstr), [], 0
    while i < len(b):
        code = b[i]
        if code < 0xF0:
            i += 1
            continue
        if code == 0xFF:
            break
        width = dialogue.ctrl_width(b, i)
        if code == 0xF4:
            width = f4_width(stream)
        if code not in LAYOUT:
            out.append((code, tuple(b[i + 1:i + 1 + width])))
        i += 1 + width
    return out


def jp_engine_codes(hexstr, stream=None):
    """Engine control codes of one JP source message, operands skipped.

    The mirror of canonical_engine for our side of the pairing: walk the
    original JP bytes by control width so that an operand which happens to
    fall in $F0-$FE is not miscounted as a control.
    """
    b, out, i = bytes.fromhex(hexstr), [], 0
    while i < len(b):
        code = b[i]
        if code < 0xF0:
            i += 1
            continue
        if code == 0xFF:
            break
        width = dialogue.ctrl_width(b, i)
        if code == 0xF4:
            width = f4_width(stream)
        if code not in LAYOUT:
            out.append(code)
        i += 1 + width
    return tuple(out)


def parse_tree(n):
    """[(index, header_line_no, start_line, end_line, engine_codes)] per message."""
    p = os.path.join(SCRIPT, f'dialogue {n}.asm')
    lines = io.open(p, encoding='utf-8', errors='replace').read().splitlines()
    msgs, cur, start = [], None, None
    for i, ln in enumerate(lines):
        m = re.match(r'^;\s*\$?([0-9A-Fa-f]+)\s*$', ln.strip())
        if m:
            if cur is not None:
                msgs.append([cur, start, i])
            cur = int(m.group(1), 16); start = i + 1
    if cur is not None:
        msgs.append([cur, start, len(lines)])
    original = canonical_engine(n)
    out = []
    for idx, a, b in msgs:
        if idx not in original:
            raise ValueError(f'tree {n}: source message ${idx:X} absent from .bin')
        out.append((idx, a, b, original[idx]))
    return lines, out


def match_us_order(en, engine):
    """Reorder our tokens to the US control order, or None if that is not safe.

    `emit` writes the US code and operands for each of our tokens in sequence,
    so our order must be theirs.  The US sometimes transposed two ADJACENT
    controls -- `lz1CD2E6#0102` has `{ctl.F4:03}{ctl.F2:00000F}` where tree 3
    has `F2:00000F` then `F4:03` -- and with no text between them that is a
    difference without a distinction.

    Only that case is accepted: a swap of two neighbouring tokens that have
    nothing but each other between them, so no line of dialogue can end up
    under the wrong portrait.  Anything else returns None.
    """
    toks = [m for m in TOKEN.finditer(en)
            if '{' + m.group(1) + '}' not in LAYOUT_TOK]
    if len(toks) != len(engine):
        return None
    want = [c for c, _ in engine]

    def code_of(m):
        return int(m.group(1).split('.')[1].split(':')[0], 16)

    order = list(range(len(toks)))
    for i in range(len(order) - 1):
        if code_of(toks[order[i]]) == want[i]:
            continue
        j = i + 1
        if (code_of(toks[order[j]]) != want[i]
                or code_of(toks[order[i]]) != want[j]):
            return None
        a, b = toks[order[i]], toks[order[j]]
        if en[a.end():b.start()].strip():
            return None          # text between them: the swap would move it
        order[i], order[j] = order[j], order[i]
    if [code_of(toks[k]) for k in order] != want:
        return None

    out, pos = [], 0
    for slot, k in enumerate(order):
        m = toks[slot]
        out.append(en[pos:m.start()])
        out.append(toks[k].group(0))
        pos = m.end()
    out.append(en[pos:])
    return ''.join(out)


def drop_extra_control(en, engine):
    """(text, dropped token) when the US removed exactly one control, else None.

    `lz1CF6D6#0003` carries a `{ctl.F9:13}` delay the US build does not, and
    dropping it makes the two sequences identical.  Accepted only when the
    result matches exactly and the surplus token sits directly against another
    token, so removing it cannot join two runs of text that were separated.

    Several positions can align when the tail of a message is an alternating
    run of `$F4`s, as `lz1DDD96#0008` is, so a candidate that fails a guard is
    skipped rather than ending the search.  Every position that is returned has
    passed both guards, so widening the search cannot widen what is accepted.

    The dropped control is returned so the caller can name it: this loses
    something the JP has, and a silent loss is how a portrait change goes
    missing without anyone noticing.
    """
    toks = [m for m in TOKEN.finditer(en)
            if '{' + m.group(1) + '}' not in LAYOUT_TOK]
    if len(toks) != len(engine) + 1:
        return None
    want = [c for c, _ in engine]

    def code_of(m):
        return int(m.group(1).split('.')[1].split(':')[0], 16)

    def prose(s):
        """What is left once layout tokens are taken out: actual words."""
        return TOKEN.sub('', s).strip()

    for k, m in enumerate(toks):
        kept = [code_of(t) for j, t in enumerate(toks) if j != k]
        if kept != want:
            continue
        before = en[toks[k - 1].end():m.start()] if k else en[:m.start()]
        after = (en[m.end():toks[k + 1].start()]
                 if k + 1 < len(toks) else en[m.end():])
        # A portrait change may only be dropped when no line of dialogue can
        # end up under the wrong portrait: either it re-sets the portrait that
        # is already showing (`lz1CF6D6#0038` has {ctl.F4:04} twice with
        # {ctl.F7} between, so the second is a no-op and the US removed it), or
        # it governs no words at all. The second case is how a line the US cut
        # is carried: `lz1DDD96#0008` keeps the JP's {ctl.F4:01} where the US
        # dropped Rudy's departure line, with nothing written under it.
        if code_of(m) == 0xF4:
            prev = next((toks[j].group(1) for j in range(k - 1, -1, -1)
                         if code_of(toks[j]) == 0xF4), None)
            if prev != m.group(1) and prose(after):
                continue
        if prose(before) and prose(after):
            continue             # words on both sides: removing it merges them
        return en[:m.start()] + en[m.end():], m.group(0)
    return None


def drop_extra_delays(en, engine):
    """(text, dropped tokens) when the US removed only $F9 delays, else None.

    The companion to drop_extra_control for the case where there is more than
    one surplus. $F9 is a pause and nothing else -- it names no speaker, holds
    no event id and dispatches nowhere -- so dropping one costs pacing and
    cannot cost meaning. The localisers stripped them wholesale: `lz1E1F06#0005`
    (Forren shutting Daughter down) carries seven the US build does not.

    No "words on both sides" guard here, unlike a dropped control: a delay sits
    mid-phrase on purpose, and closing "Ru{F9}...dy" back up to "Ru...dy" is
    exactly the right result.

    The tokens are aligned against the US sequence rather than counted, so the
    result is the US order by construction.
    """
    toks = [m for m in TOKEN.finditer(en)
            if '{' + m.group(1) + '}' not in LAYOUT_TOK]
    want = [c for c, _ in engine]

    def code_of(m):
        return int(m.group(1).split('.')[1].split(':')[0], 16)

    dropped, i = [], 0
    for m in toks:
        if i < len(want) and code_of(m) == want[i]:
            i += 1
        elif code_of(m) == 0xF9:
            dropped.append(m)
        else:
            return None
    if i != len(want) or not dropped:
        return None
    out, pos = [], 0
    for m in dropped:
        out.append(en[pos:m.start()])
        pos = m.end()
    out.append(en[pos:])
    return ''.join(out), [m.group(0) for m in dropped]


def drop_surplus(en, engine):
    """(text, dropped tokens) when the US removed $F9 delays and $F2 events.

    The last of the three drop rules, tried only after the other two fail.
    `lz1D38E6#0008` -- the crash landing and meeting Raja -- carries four
    tokens the US build does not: the `{ctl.F2:08}{ctl.F9:59}{ctl.F2:09}` sound
    gag after Raja's pun, and one `{ctl.F9:1D}`. Two surpluses of two different
    codes, so neither drop_extra_control (exactly one) nor drop_extra_delays
    ($F9 only) can place it, and the scene would be skipped entirely.

    $F2 hands an event id back to the interpreter, so it is not as free as a
    delay, and it is only dropped under drop_extra_control's adjacency guard:
    no prose on both sides, meaning the token sits against another token and
    removing it cannot join two separated runs of text. $F4 is never dropped
    here at all -- losing a portrait change loses who is speaking.

    Dropping is safe in the direction that matters: these are codes the US tree
    does not have, and the US tree is the engine data for the ROM being built.
    Adding one is what breaks test_treeport_controls; taking one away leaves
    the assembled controls exactly as the US build has them.
    """
    toks = [m for m in TOKEN.finditer(en)
            if '{' + m.group(1) + '}' not in LAYOUT_TOK]
    want = [c for c, _ in engine]

    def code_of(m):
        return int(m.group(1).split('.')[1].split(':')[0], 16)

    def prose(s):
        return TOKEN.sub('', s).strip()

    dropped, i = [], 0
    for k, m in enumerate(toks):
        if i < len(want) and code_of(m) == want[i]:
            i += 1
            continue
        if code_of(m) == 0xF9:
            dropped.append(m)
            continue
        if code_of(m) != 0xF2:
            return None
        before = en[toks[k - 1].end():m.start()] if k else en[:m.start()]
        after = (en[m.end():toks[k + 1].start()]
                 if k + 1 < len(toks) else en[m.end():])
        if prose(before) and prose(after):
            return None
        dropped.append(m)
    if i != len(want) or not dropped:
        return None
    out, pos = [], 0
    for m in dropped:
        out.append(en[pos:m.start()])
        pos = m.end()
    out.append(en[pos:])
    return ''.join(out), [m.group(0) for m in dropped]


def drop_portraits_for_blank(en, engine):
    """(text, dropped) when the US message has NO controls and ours are all $F4.

    A handful of rows carry a portrait the US message simply does not have:
    `lz1DB036#0072` is one `{ctl.F4:01}` against a US message with zero engine
    codes, and tree 7 has seven of them. emit cannot place a control the US
    tree lacks, so these were skipped and the US wording stayed on screen.

    Dropping every one of them is exactly what the US does: with no portrait
    control the line displays under whatever portrait is already showing. We
    lose the JP's choice of speaker portrait and gain the translated words,
    which is the right trade when the alternative is shipping English from
    1995.

    Restricted hard, because the same shape covers things that must NOT be
    flattened: `lz1CE546#0045`, the Alys death scene, is 42 `$F4` plus ten
    `$F7` scene breaks and six `$F2` events against a blank US message. $F7
    ends a scene and $F2 fires one; losing those would not cost a portrait, it
    would cost the cutscene. So this fires only when the US side is empty AND
    every token of ours is a portrait.
    """
    if engine:
        return None
    toks = [m for m in TOKEN.finditer(en)
            if '{' + m.group(1) + '}' not in LAYOUT_TOK]
    # Cap it at two. Recovering a one-line NPC that carries a single portrait
    # is a clear win; flattening a scene is not. `lz1E05B6#0000` is 19 portrait
    # changes against a blank US message and `lz1DEC96#0043` is nine -- a US
    # message with no controls facing a 19-speaker JP scene almost certainly
    # means the US split that scene across several messages, so writing the
    # whole thing into one is a different operation with a different risk, and
    # it would land every speaker's lines under one portrait.
    if not toks or len(toks) > 2:
        return None
    for m in toks:
        if int(m.group(1).split('.')[1].split(':')[0], 16) != 0xF4:
            return None
    out, pos = [], 0
    for m in toks:
        out.append(en[pos:m.start()])
        pos = m.end()
    out.append(en[pos:])
    return ''.join(out), [m.group(0) for m in toks]


def emit(en, engine):
    """Our text + wrapping over the US build's engine bytes."""
    body, ei = [], 0
    pos = 0
    for m in TOKEN.finditer(en):
        txt = en[pos:m.start()]
        if txt:
            body.extend(text_lines(txt))
        tok = '{' + m.group(1) + '}'
        if tok in LAYOUT_TOK:
            body.append(f'\tdc.b\t${LAYOUT_TOK[tok]:02X}')
        else:
            if ei >= len(engine):
                return None
            code, ops = engine[ei]; ei += 1
            body.append(f'\tdc.b\t${code:02X}')
            if ops:
                body.append('\tdc.b\t' + ', '.join(f'${o:02X}' for o in ops))
        pos = m.end()
    if en[pos:]:
        body.extend(text_lines(en[pos:]))
    if ei != len(engine):
        return None
    body.append('\tdc.b\t$FF')
    return body


def text_lines(txt):
    """dc.b strings, splitting out characters with no bare spelling."""
    out, buf = [], ''
    for ch in txt:
        if ch in LITERAL:
            if buf:
                out.append('\tdc.b\t"' + buf + '"'); buf = ''
            out.append(f'\tdc.b\t${LITERAL[ch]:02X}')
        else:
            buf += ch
    if buf:
        out.append('\tdc.b\t"' + buf + '"')
    return out


def tree_group(stream_rows, base, cache, gain=3):
    """Which trees hold this stream's messages, discovered by coverage.

    The US resolved the JP's in-message {ctl.FA} branches into PARALLEL TREES,
    and tree_map records only one tree per stream.  The rest cannot be guessed
    from the numbering -- $1CD2E6 is named as tree 4 and its variant is tree 3,
    *below* the base -- so the group is measured.

    Scoring by "what fraction of rows does this tree match" does not work: the
    variants hold DIFFERENT subsets of the branches, so a variant always looks
    poor against the base.  What identifies one is that it resolves rows the
    group so far cannot.  Rows with no engine codes are ignored throughout,
    since empty matches empty everywhere and carries no signal.
    """
    def engine(n):
        if n not in cache:
            cache[n] = canonical_engine(n)
        return cache[n]

    def matches(n, idx, fp):
        got = engine(n).get(idx)
        return got is not None and fp == tuple(c for c, _ in got)

    live = [(idx, fp) for idx, fp in stream_rows if fp]
    group = [base]
    unresolved = [r for r in live if not matches(base, *r)]
    while unresolved:
        best, gained, strongest = None, 0, 0
        for n in range(1, 44):
            # A variant sits beside its base: every group found this way is
            # adjacent except one 21 trees away, which was chance agreement on
            # rows carrying a single {ctl.F4}.  Requiring adjacency drops that
            # and nothing else.
            if n in group or abs(n - base) > 2:
                continue
            try:
                k = sum(1 for r in unresolved if matches(n, *r))
            except Exception:
                continue
            if k > gained:
                got = [r for r in unresolved if matches(n, *r)]
                best, gained = n, k
                strongest = max((len(fp) for _, fp in got), default=0)
        # Count is the wrong measure on its own.  The gain bar is here to
        # reject chance agreement on rows carrying a single {ctl.F4}, but a row
        # whose fingerprint is nine or fifty-eight codes cannot agree by
        # chance: tree 6 resolves exactly TWO rows of lz1CE546 -- $0044 at nine
        # codes and $0045, the Alys death scene, at fifty-eight -- and sat
        # outside the group for want of a third, taking ten messages of Tonoe
        # with it.  Distinctiveness counts as well as quantity.
        if best is None or (gained < gain and strongest < 4):
            break
        group.append(best)
        unresolved = [r for r in unresolved if not matches(best, *r)]
    return group


def canonical_textlen(n):
    """{message index: count of text bytes} for a tree, from its untouched .bin.

    The companion signal to canonical_engine.  A row whose fingerprint is EMPTY
    matches every tree equally, so routing on codes alone always fell through to
    group[0] -- and when the base tree's slot is blank and the variant holds the
    words, the translation was aimed at the empty one and skipped.  That is why
    the Mile well-and-fields NPC kept her US line while `lz1CD2E6#0002` sat
    finished in the JSON.  Whether a message HAS words is the tiebreak.
    """
    p = os.path.join(SCRIPT, f'dialogue {n}.bin')
    plain = kosinski.decompress(open(p, 'rb').read())
    out, count, idx, i = {}, 0, 0, 0
    while i < len(plain):
        code = plain[i]
        if code < 0xF0:
            count += 1
            i += 1
            continue
        if code == 0xFF:
            out[idx] = count
            count, idx, i = 0, idx + 1, i + 1
            continue
        width = TREE_EXTRA_OPERANDS.get(code, dialogue.ctrl_width(plain, i))
        if code == 0xF4:
            width = f4_width(n)
        i += 1 + width
    return out


def canonical_text(n):
    """{message index: its US text} for a tree, from the untouched .bin.

    Used to identify TWINS: the US sometimes carries the same message in two
    trees of a group, byte for byte.  A row can only be assigned once, so the
    copy that did not win kept its US wording -- seven of Tonoe's lines in tree
    6 sat that way behind their identical originals in tree 5.
    """
    p = os.path.join(SCRIPT, f'dialogue {n}.bin')
    plain = kosinski.decompress(open(p, 'rb').read())
    out, cur, idx, i = {}, bytearray(), 0, 0
    while i < len(plain):
        code = plain[i]
        if code < 0xF0:
            cur.append(code)
            i += 1
            continue
        if code == 0xFF:
            out[idx] = bytes(cur)
            cur, idx, i = bytearray(), idx + 1, i + 1
            continue
        width = TREE_EXTRA_OPERANDS.get(code, dialogue.ctrl_width(plain, i))
        if code == 0xF4:
            width = f4_width(n)
        i += 1 + width
    return out


def twins(group, tree, idx, ours, cache):
    """Other trees in the group holding the IDENTICAL message at this index.

    Identical means the same engine codes and the same text bytes -- not
    "similar", because a row written into the wrong message is worse than a
    message left in English.  Under that bar the copy cannot be a different
    line that happens to share an index.
    """
    def engine(n):
        if n not in cache:
            cache[n] = canonical_engine(n)
        return cache[n]

    def text(n):
        key = ('body', n)
        if key not in cache:
            cache[key] = canonical_text(n)
        return cache[key]

    mine = text(tree).get(idx)
    if not mine:
        return []
    out = []
    for n in group:
        if n == tree:
            continue
        got = engine(n).get(idx)
        if got is None or ours != tuple(c for c, _ in got):
            continue
        if text(n).get(idx) == mine:
            out.append(n)
    return out


def target_tree(group, idx, ours, cache):
    """The tree in this stream's group that actually holds this message."""
    def engine(n):
        if n not in cache:
            cache[n] = canonical_engine(n)
        return cache[n]

    def has_text(n):
        key = ('text', n)
        if key not in cache:
            cache[key] = canonical_textlen(n)
        return cache[key].get(idx, 0) > 0

    # Prefer a tree that both matches and has words at this index.  Ordering
    # the two passes this way leaves an exact match on a populated message
    # winning over an exact match on a blank one, which is the whole fix.
    for want_text in (True, False):
        for n in group:
            got = engine(n).get(idx)
            if got is not None and ours == tuple(c for c, _ in got)                     and has_text(n) == want_text:
                return n
    # Failing an exact match, a tree holding the same controls in a different
    # ORDER is still this message: the US transposed the occasional adjacent
    # pair.  Route there and let match_us_order decide whether the reordering
    # is safe -- it refuses unless the swap moves no text.
    for want_text in (True, False):
        for n in group:
            got = engine(n).get(idx)
            if got is not None and sorted(ours) == sorted(c for c, _ in got)                     and has_text(n) == want_text:
                return n
    # Last resort: a tree with words beats the base with none.
    for n in group:
        if has_text(n):
            return n
    return group[0]


def relocated(group, ours, claimed, cache):
    """(tree, index) for a message the US MOVED, or None.

    Indices otherwise line up one for one, but the US shifted the occasional
    message: `lz1CC476#0086` sits at $56 in our source and the US left $56 blank
    and put that message at $6E, the end of the tree.  Confirmed from the US
    text Mark quoted -- "I think there's more to it than that." / "Things are
    starting to get interesting!"

    Only an unambiguous relocation is accepted: the fingerprint must be
    distinctive (two or more codes), and exactly one message in the group may
    carry it without another row already owning it at that row's own index.
    """
    if len(ours) < 2:
        return None

    def engine(n):
        if n not in cache:
            cache[n] = canonical_engine(n)
        return cache[n]

    found = []
    for n in group:
        for idx, codes in engine(n).items():
            if (n, idx) in claimed:
                continue
            if ours == tuple(c for c, _ in codes):
                found.append((n, idx))
    return found[0] if len(found) == 1 else None


def main():
    write = '--write' in sys.argv
    only = [int(a) for a in sys.argv[1:] if a.isdigit()]
    tm = json.load(io.open(os.path.join(ROOT, 'work', 'tree_map.json'),
                           encoding='utf-8'))['map']
    mapped = {int(k, 16): v for k, v in tm.items()}
    ents = dialogue.load(os.path.join(ROOT, 'work', 'dialogue_full.json'))

    cache = {}
    bystream = {}
    for e in ents:
        st, suf = e.get('stream'), e['id'].split('#')[1]
        if st is None or not suf.isdigit() or st not in mapped:
            continue
        bystream.setdefault(st, []).append(
            (int(suf), jp_engine_codes(e['hex'])))
    groups = {st: tree_group(rws, mapped[st], cache)
              for st, rws in bystream.items()}
    bytree = {}
    unverified = []
    # Pass 1: every row that matches somewhere in its group at its own index.
    # Those slots are then spoken for, which is what makes a relocation
    # unambiguous in pass 2.
    todo, claimed = [], set()
    for e in ents:
        st, suf = e.get('stream'), e['id'].split('#')[1]
        if st is None or not suf.isdigit() or st not in mapped:
            continue
        # A source row can be intentionally empty.  `blank: true` distinguishes
        # that translation decision from an untranslated row, allowing us to
        # erase a stray US-localization line without inventing visible text.
        if not (e.get('en') or '').strip() and not e.get('blank'):
            continue
        idx, ours = int(suf), jp_engine_codes(e['hex'])
        tree = target_tree(groups[st], idx, ours, cache)
        got = cache[tree].get(idx) if tree in cache else None
        if got is not None and ours == tuple(c for c, _ in got):
            claimed.add((tree, idx))
            bytree.setdefault(tree, []).append((idx, e))
            # The US duplicates some messages across a group's trees.  A row
            # is assigned once, so every copy but the winner kept its US
            # wording; write the same translation into each identical one.
            for other in twins(groups[st], tree, idx, ours, cache):
                if (other, idx) not in claimed:
                    claimed.add((other, idx))
                    bytree.setdefault(other, []).append((idx, e))
        else:
            todo.append((st, idx, ours, e))
    # Pass 2: the ones left over, in case the US moved the message.
    for st, idx, ours, e in todo:
        spot = relocated(groups[st], ours, claimed, cache)
        if spot:
            claimed.add(spot)
            bytree.setdefault(spot[0], []).append((spot[1], e))
        else:
            bytree.setdefault(target_tree(groups[st], idx, ours, cache),
                              []).append((idx, e))

    # Hand-verified placements win over anything the rules worked out.
    byid = {e['id']: e for e in ents}
    for (tree, idx), rid in OVERRIDES.items():
        bytree.setdefault(tree, [])
        bytree[tree] = [(i, e) for i, e in bytree[tree] if i != idx]
        if rid is None:
            bytree[tree].append((idx, {'id': 'blank@%d:%X' % (tree, idx),
                                       'en': '', 'blank': True, 'hex': ''}))
        elif isinstance(rid, tuple):
            if rid[0] in byid:
                bytree[tree].append((idx, byid[rid[0]]))
        elif rid in byid:
            bytree[tree].append((idx, byid[rid]))
        else:
            print('  override names a row that does not exist: %s' % rid)

    tot = {'ported': 0, 'skipped': 0}
    dropped = []
    for tree in sorted(bytree):
        if only and tree not in only:
            continue
        lines, msgs = parse_tree(tree)
        byidx = {i: (a, b, eng) for i, a, b, eng in msgs}
        edits = []
        for idx, e in sorted(bytree[tree]):
            if idx not in byidx:
                print(f'  tree {tree} #{idx:02X}: no such message'); tot['skipped'] += 1; continue
            a, b, eng = byidx[idx]
            spec = OVERRIDES.get((tree, idx))
            if isinstance(spec, tuple) and spec[1] == 'jp':
                # Sanctioned deviation: emit this message with the Japanese
                # controls.  See the note beside the entry in OVERRIDES.
                eng = jp_engine_full(e['hex'], e['id'].split('#')[0])
            # Only port pairings the evidence actually establishes. Matching
            # engine token COUNTS is not evidence: the US build split some JP
            # streams across trees, so an index can land on an unrelated - or
            # empty - message and still tally. 73 of the first attempt did.
            #
            # A `us` field means usimport matched this index's fingerprint.
            # It only ever WROTE that field when the US message had text,
            # though, so a US message the localisers left blank paired just as
            # firmly and then looked unpaired here. Test the fingerprint
            # directly against the immutable .bin instead of inferring it from
            # whether the US line happened to be empty.
            if not (e.get('us') or '').strip():
                ours = jp_engine_codes(e['hex'], e['id'].split('#')[0])
                theirs = tuple(c for c, _ in eng)
                # An exact fingerprint is the pairing evidence.  The same
                # controls in a different ORDER are the same evidence: the US
                # transposed the occasional adjacent pair, and match_us_order
                # below refuses the swap unless it moves no text.
                from collections import Counter
                surplus = Counter(ours) - Counter(theirs)
                missing = Counter(theirs) - Counter(ours)
                # Exact, a reordering, or one control the US dropped. Anything
                # else is not this message; emit and the two gates below decide
                # whether the last two cases are actually safe.
                if not (ours == theirs
                        or (not surplus and not missing)
                        or (sum(surplus.values()) == 1 and not missing)
                        # any number of surplus delays: see drop_extra_delays
                        or (not missing and set(surplus) <= {0xF9})
                        # portraits against a blank US message: see
                        # drop_portraits_for_blank
                        or (not theirs and set(surplus) <= {0xF4})):
                    unverified.append(e['id'])
                    continue
            # NOT stripped. The US keeps a byte between a portrait control
            # and the first letter in some messages, and stripping silently
            # dropped it -- so a fix that restored one never reached the ROM.
            text = e.get('en') or ''
            body = emit(text, eng)
            if body is None:
                swapped = match_us_order(text, eng)
                if swapped is not None:
                    body = emit(swapped, eng)
            if body is None:
                cut = drop_extra_control(text, eng)
                if cut is not None:
                    body = emit(cut[0], eng)
                    if body is not None:
                        dropped.append((e['id'], cut[1]))
            if body is None:
                cut = drop_extra_delays(text, eng)
                if cut is not None:
                    body = emit(cut[0], eng)
                    if body is not None:
                        dropped.append((e['id'], ' '.join(cut[1])))
            if body is None:
                cut = drop_surplus(text, eng)
                if cut is not None:
                    body = emit(cut[0], eng)
                    if body is not None:
                        dropped.append((e['id'], ' '.join(cut[1])))
            if body is None:
                cut = drop_portraits_for_blank(text, eng)
                if cut is not None:
                    body = emit(cut[0], eng)
                    if body is not None:
                        dropped.append((e['id'], ' '.join(cut[1])))
            if body is None:
                ours = len([t for t in TOKEN.findall(e['en']) if '{'+t+'}' not in LAYOUT_TOK])
                print(f'  tree {tree} #{idx:02X} ({e["id"]}): engine tokens '
                      f'{ours} vs US {len(eng)} - skipped')
                tot['skipped'] += 1; continue
            edits.append((a, b, body)); tot['ported'] += 1
        if write and edits:
            for a, b, body in sorted(edits, reverse=True):
                lines[a:b] = body
            p = os.path.join(SCRIPT, f'dialogue {tree}.asm')
            io.open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
        print(f'tree {tree}: {len(edits)} message(s) '
              f'{"written" if write else "ready"}')
    print(f'\nported {tot["ported"]}, skipped {tot["skipped"]}'
          f'{"" if write else "  (dry run; pass --write)"}')

    # A row with no `us` is dropped above, deliberately: usimport could not
    # establish which US message it pairs with, and porting on index alone
    # mispaired 73 rows on the first attempt.  Dropping it is right; dropping
    # it SILENTLY is not.  These are finished translations that never reach
    # the ROM, and the only symptom in game is the US line still showing -
    # which is indistinguishable from simply not having translated it yet.
    if dropped:
        print(f'\n{len(dropped)} row(s) ported with a control the US build '
              f'does not have, dropped to match it:')
        for rid, tok in dropped:
            print(f'  {rid}: {tok}')
    if unverified:
        bystream = {}
        for i in unverified:
            bystream.setdefault(i.split('#')[0], []).append(i)
        print(f'\n{len(unverified)} translated row(s) NOT ported - JP engine '
              f'fingerprint differs from the US message:')
        for st in sorted(bystream):
            ids = bystream[st]
            print(f'  {st}: {len(ids):3d} rows  ({ids[0]} .. {ids[-1]})')


if __name__ == '__main__':
    main()
