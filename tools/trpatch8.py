"""Apply and validate English translations for the menu/name bank.

Separate from trpatch.py because the two text systems share nothing: the 8x8
bank encodes through ps4.tbl (one byte = one 8x8 cell) rather than through the
dialogue font, and its binding constraint is display WIDTH, not stream budget.

The width rule is the subtle part, and the obvious reading of it is wrong.

"One byte is one cell" holds only for unvoiced text. The dakuten and
handakuten prefixes $F0/$F1 are combining marks and do NOT take a cell of
their own, so a byte count over-measures any name containing voiced kana.
Correct for that and every table lands exactly on a flat limit:

    table                entries   max cells
    Player items            157        10
    Player techniques        40         5
    Player skills            54         8
    Locations                54        10
    Party names              11         4
    Enemy names             153        10
    Enemy skills            110        10

Hitting the cap exactly in all seven is what pins these down - they are real
window widths, not the incidental maximum of the data.

The earlier rule here, max(10, original_bytes), is retracted. It was derived
from the byte count, and its supporting argument - that 22 item names exceed
10 cells and therefore cannot appear in the item menu - counted those 22 in
BYTES. Measured in cells they all fit 10, and there is no such exempt set.

The current English build uses two renderers.  Party/class strings still use
the encoded 8x8 cells described above, while item, Technique, Skill, location,
enemy, and enemy-action names use the menu VWF.  For those tables a "cell" is
an eight-pixel strip cell, not a source character.  The validator deliberately
imports menustrip.compose(), the same compositor that generates the ROM strips,
so the proofreader, validator, generated art, and runtime width table agree.

Casing: mixed case is available. The 8x8 font was located at $2A2B7E (Nemesis,
low bank) and english8.install_font() regenerates it with small caps, ligatures
and the creep party glyphs. ps4.tbl is untouched and still decodes the Japanese;
cell counts here come from english8, which knows each table's packing policy.
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from table import Table


# These are rendered with menufont.bin/menuwidth.bin.  The first four are
# prerendered strips; enemies and enemy actions use the same face at runtime.
VWF_SEGMENTS = {'00:001', '00:002', '00:003', '00:004',
                '02:000', '02:001', '02:002', '03:001',
                '00:008'}   # spaceship destination menu (tools/spacemenu.py)


def cells(tbl, text, entry=None):
    """Encoded length in cells, or ('err', message).

    Measures with the ENGLISH encoder, not ps4.tbl. ps4.tbl is the Japanese
    decoder and has no lowercase, so it would reject every mixed-case name;
    and it cannot know a table's packing policy, which is what decides how many
    cells a name actually occupies.
    """
    try:
        if entry is not None:
            if entry.get('segment') in VWF_SEGMENTS:
                from menustrip import glyph_of
                import math
                # the composer's own arithmetic, per {FC}-separated line:
                # the spaceship confirmation is two lines in one entry
                def line_cells(t):
                    px = sum(glyph_of(c, t)[1] for c in t)
                    return max(1, math.ceil(px / 8))
                return max(line_cells(t) for t in text.split('{FC}'))
            import english8
            return len(english8.encode(text, entry))
        return len(tbl.encode(text))
    except Exception as ex:
        return ('err', str(ex))


# Flat window width per table, in cells. See the module docstring for how
# these were pinned: each is the exact maximum the original data reaches.
SEGMENT_LIMIT = {
    '00:001': 10,   # player items
    '00:002': 7,    # player techniques (cost starts two cells later)
    '00:003': 8,    # player skills
    '00:004': 10,   # location names
    '02:001': 10,   # enemy names
    '02:002': 10,   # enemy skills / battle actions
    '03:000': 4,    # party names (the copy read by $0444C4)
    # '03:001' (class and vehicle names) is deliberately absent: see below.
}

# 02:000 is the big table's head and mixes two roles: the first 11 entries are
# the party names the status window shows in 4 cells, the rest are class and
# vehicle names. Split by index rather than giving the whole segment one cap.
# Both name lists mix three roles, so split them by index rather than giving a
# segment one cap:
#   party names   4 cells  (the status window; see the ォー ligature)
#   job titles    8 cells
#   vehicles      uncapped - they share the list with job titles but are not
#                 shown in the job field, and run longer than 8 in English
INDEX_LIMIT = {
    '02:000': [(0, 11, 4), (11, 19, 8), (19, 22, None)],
    '03:001': [(0, 8, 8), (8, 11, None)],
    # spaceship menu: the prompt window is 25 wide (text at x+1), the
    # list windows 10 wide (name at x+3); the confirmation tail follows
    # the chosen name and spacemenu.py checks it with the longest name
    '00:008': [(0, 1, 24), (1, 2, None), (2, 8, 7)],
}

# Job titles are capped at 8 by the status window. Vehicles share the same list
# but are not shown in that field and are left uncapped.
#
# Nothing in CODE enforces either. The reader at $05DF28 indexes the list by
# counting $FF and then copies until the next $FF into $FFE220 with no length
# check of any kind:
#
#     05DF28  lea ($2AA220).l,a0
#     05DF2E  lea ($FFE220).w,a1
#     05DF3A  cmpi.b #$FF,(a0)+      ; skip to entry d0
#     05DF46  cmpi.b #$FF,(a0)       ; copy until $FF
#     05DF4C  move.b (a0)+,(a1)+     ; no bound
#
# An earlier revision capped the WHOLE list at 8, inferred from the largest
# original entry (モタビアンマニア). That swept the vehicles in with the job
# titles and wrongly forced three item names to be abbreviated, since the
# vehicles also appear in the item list. The 8 is right for job titles and does
# not apply to vehicles.
# 01:003 is item DESCRIPTIONS - multi-line prose broken with {FC}, so the
# constraint is per line, not per entry, and this cap does not apply.
# 01:004 is the sound-test track list, already English in the Japanese ROM.
DESCRIPTION_SEGMENTS = {'01:003'}
DESCRIPTION_PX = 24 * 8     # the message window's interior, WinGroup_Menu $35


def effective_limits(entries):
    """{id: cells} after linking entries that share a Japanese string.

    37 names appear in more than one table - every player technique is also an
    enemy action, for instance. The same string must render identically in both
    places, so the binding cap is the SMALLEST window it appears in, not the one
    for the table you happen to be editing. Without this, ギフォイエ could be
    written at 10 cells as an enemy action and 5 as a player technique, and the
    two would silently disagree in-game.
    """
    by_jp = {}
    for e in entries:
        lim = limit_for(e)
        if lim is None or not e['jp']:
            continue
        prev = by_jp.get(e['jp'])
        by_jp[e['jp']] = lim if prev is None else min(prev, lim)
    out = {}
    for e in entries:
        lim = limit_for(e)
        if lim is not None and e['jp'] in by_jp:
            lim = by_jp[e['jp']]
        out[e['id']] = lim
    return out


# Two skills are combination attacks and never appear in the skill menu, so the
# 8-cell menu width does not bind them - they get 10. Keyed by the Japanese so
# the exception survives any re-extraction that shifts indices.
COMBO_SKILLS = {'アストラルフレア': 10, 'セントファイア': 10}


def limit_for(entry):
    """Cells available, or None where no flat per-entry cap applies."""
    seg = entry.get('segment')
    if entry.get('jp') in COMBO_SKILLS:
        return COMBO_SKILLS[entry['jp']]
    if seg in DESCRIPTION_SEGMENTS:
        return None
    ranges = INDEX_LIMIT.get(seg)
    if ranges:
        idx = int(entry['id'].rsplit('#', 1)[1])
        for lo, hi, lim in ranges:
            if lo <= idx < hi:
                return lim
        return None
    return SEGMENT_LIMIT.get(seg)


def description_problems(entry, en):
    """Line widths for the item descriptions, which are not a cell table.

    `01:003` has no flat cell cap and so had no check at all, which is why
    these were the one table with nothing to edit against.  They are drawn in
    TWO places with two faces, and a line must fit both:

      Item > Look   `loc_65BCC` -> RunText, composed with the MENU face into
                    the 24-cell message window: 192 px a line (measured on
                    screen: "A medicine that" is 64 px, the menu sum).
      shop Buy/Sell the vendor shows the same text through the dialogue
                    engine's VWFDia_DrawGlyph - the DIALOGUE face, in a box of
                    VWFDIA_CELLS*8 = 256 px (dialogue_reflow.LIMIT).

    The dialogue face is the wider of the two (about 1.45x), so it is usually
    the one that binds.  Two lines, split on the $FC we spell {FC}.
    tools/itemdesc.py and proofread.html measure the same way.

    Both limits fail silently in game rather than visibly: a third line is
    dropped outright, and an over-long line runs into the frame.
    """
    import re
    import menustrip
    import dialogue_reflow as R
    problems = []
    rows = en.split('{FC}')
    if len(rows) > 2:
        problems.append(f'{len(rows)} lines, the box holds 2 '
                        f'(the third is dropped, not wrapped)')
    for i, row in enumerate(rows):
        plain = re.sub(r'\{[^}]*\}', '', row)
        bad = sorted({c for c in plain if c not in menustrip.code})
        if bad:
            problems.append(f'line {i + 1} has no menu glyph for {bad!r}  [{row}]')
        w = sum(menustrip.width[menustrip.code[c]] for c in plain if c in menustrip.code)
        if w > DESCRIPTION_PX:
            problems.append(f'line {i + 1} is {w}px in the menu face, limit {DESCRIPTION_PX}px (Item > Look)  [{row}]')
        wd = R.px(row)
        if wd > R.LIMIT:
            problems.append(f'line {i + 1} is {wd}px in the dialogue face, limit {R.LIMIT}px (shop)  [{row}]')
    return problems


def check_line(tbl, entry, en, lim='auto'):
    if entry.get('segment') in DESCRIPTION_SEGMENTS:
        return description_problems(entry, en)
    problems = []
    n = cells(tbl, en, entry)
    if isinstance(n, tuple):
        problems.append('cannot encode: ' + n[1])
        return problems
    if lim == 'auto':
        lim = limit_for(entry)
    if lim is not None and n > lim:
        problems.append(f'{n} cells, limit {lim}')
    return problems


def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def save(doc, p):
    tmp = p + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    os.replace(tmp, p)


def apply_patch(script_path, patch_path):
    tbl = Table()
    doc = load(script_path)
    by_id = {e['id']: e for e in doc['entries']}
    patch = load(patch_path)
    lims = effective_limits(doc['entries'])
    problems = []
    for eid, en in patch.items():
        e = by_id.get(eid)
        if e is None:
            problems.append(f'{eid}: no such id'); continue
        for p in check_line(tbl, e, en, lims.get(eid)):
            problems.append(f'{eid}: {p}   [{en}]')
    # A name shared between tables must read the same in both.
    pending = dict(patch)
    for eid, en in patch.items():
        jp = by_id[eid]['jp'] if eid in by_id else None
        if not jp:
            continue
        for other in doc['entries']:
            if other['jp'] != jp or other['id'] == eid:
                continue
            twin = pending.get(other['id'], (other.get('en') or '').strip())
            if twin and twin != en:
                problems.append(
                    f'{eid}: [{en}] disagrees with {other["id"]} [{twin}] '
                    f'for the same name {jp}')
    if problems:
        print(f'REFUSING to apply - {len(problems)} problem(s):')
        for p in problems[:40]:
            print('  ' + p)
        return 1
    for eid, en in patch.items():
        by_id[eid]['en'] = en
    save(doc, script_path)
    done = sum(1 for e in doc['entries'] if (e.get('en') or '').strip())
    print(f'applied {len(patch)} -> {script_path}')
    print(f'translated now {done}/{len(doc["entries"])}')
    return 0


def check_all(script_path):
    tbl = Table()
    doc = load(script_path)
    lims = effective_limits(doc['entries'])
    problems, done = [], 0
    seen = {}
    for e in doc['entries']:
        en = (e.get('en') or '').strip()
        if not en:
            continue
        done += 1
        for p in check_line(tbl, e, en, lims.get(e['id'])):
            problems.append(f'{e["id"]}: {p}   [{en}]')
        if e['jp']:
            prev = seen.setdefault(e['jp'], (e['id'], en))
            if prev[1] != en:
                problems.append(
                    f'{e["id"]}: [{en}] disagrees with {prev[0]} [{prev[1]}] '
                    f'for the same name {e["jp"]}')
    print(f'{done}/{len(doc["entries"])} translated, {len(problems)} problem(s)')
    for p in problems[:60]:
        print('  ' + p)
    return 1 if problems else 0


if __name__ == '__main__':
    if len(sys.argv) >= 4 and sys.argv[1] == 'apply':
        sys.exit(apply_patch(sys.argv[2], sys.argv[3]))
    if len(sys.argv) >= 3 and sys.argv[1] == 'check':
        sys.exit(check_all(sys.argv[2]))
    print('usage: trpatch8.py apply <script.json> <patch.json>')
    print('       trpatch8.py check <script.json>')
