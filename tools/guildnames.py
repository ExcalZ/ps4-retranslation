"""Port the Hunters Guild job-board titles from script_translated.json.

Another table the extraction never covered: nine `dc.b "...", $FE` strings at
$071F6E, each with its own label, listed through the self-relative word table
`HuntersGuildTextOffset`.  The JP originals are at $071D96 in work/rom.bin,
found by searching the JP ROM for the reader's own instruction sequence --
`lea (X).l,a1 / moveq #7,d7 / moveq #0,d6` -- which occurs exactly once.

These COMPOSE, via VWFMENU_GUILD_LO/HI.  That is what lets them say what the
Japanese says: "The Ranch Owner of Mile" is 23 characters and could never have
fit the 16-cell fixed field, but it composes to 15 cells.

Two budgets, and the second is the one that bites.  Each title has to fit the
16-cell field.  But the board draws all eight rows at once and they are all
live on the plane together, so the sweep cannot reclaim any of them -- their
COMBINED distinct-tile demand has to fit the pool as well.  Checking only the
per-title width would let a later edit tip the board over and silently blank
the tails, which is the failure this table was moved to VWF in the middle of.

    python tools/guildnames.py            report
    python tools/guildnames.py --write    rewrite ps4.asm
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASM = os.path.join(ROOT, 'ps4disasm', 'ps4.asm')
SCRIPT = os.path.join(ROOT, 'work', 'script_translated.json')
SEGMENT = '00:007'
CELLS = 16
# Derived, never restated: menupool.py shrinks the pool whenever a new raw
# tile immediate appears in source.
POOL = int(re.search(r"^VWFMENU_SLOTS\s*=\s*(\d+)",
                open(os.path.join(ROOT, "ps4disasm", "ps4.constants.asm"),
                     encoding="utf-8", errors="replace").read(),
                re.M).group(1))

LABELS = ['GuildText_RanchOwner', 'GuildText_TinkerbellDog',
          'GuildText_MissingStudent', 'GuildText_FissureFear',
          'GuildText_StainLife', 'GuildText_DyingBoy', 'GuildText_ManTwist',
          'GuildText_SilverSoldier', 'GuildText_ListingPending']

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from menustrip import compose

ENTRY = re.compile(r'^(\s*dc\.b\s+)"([^"]*)"(.*)$')


LEGAL = set(" !',-.0123456789:?ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "abcdefghijklmnopqrstuvwxyz")


def board_tiles(titles, pending):
    """Worst-case distinct pool tiles the board can need.

    Eight rows, each showing either its own title or `pending` when the job is
    not yet listed, so counting all nine strings together over-states it: a
    substituted row costs `pending` INSTEAD of its title, not as well.
    Enumerate the 256 real boards and take the largest.
    """
    def tiles(text):
        n, span = compose(text)
        # A blank cell draws $680 and costs no slot.
        return {t for t in (bytes(span[y * 16 + i] for y in range(8))
                            for i in range(n)) if any(t)}

    per, sub = [tiles(t) for t in titles], tiles(pending)
    worst = 0
    for mask in range(1 << len(per)):
        live = set()
        for i, own in enumerate(per):
            live |= sub if mask >> i & 1 else own
        worst = max(worst, len(live))
    return worst


def main():
    lines = io.open(ASM, encoding='utf-8', errors='replace').read().split('\n')
    doc = json.load(io.open(SCRIPT, encoding='utf-8'))
    rows = [e for e in doc['entries'] if (e.get('segment') or '') == SEGMENT]
    rows.sort(key=lambda e: int(e['id'].rsplit('#', 1)[1]))
    if len(rows) != len(LABELS):
        print('%s has %d rows, expected %d' % (SEGMENT, len(rows), len(LABELS)))
        return 1

    changed = blank = 0
    for label, row in zip(LABELS, rows):
        try:
            at = next(i for i, l in enumerate(lines) if l.startswith(label + ':'))
        except StopIteration:
            print('%s: no such label in ps4.asm' % label)
            return 1
        at = next(i for i in range(at + 1, at + 4) if ENTRY.match(lines[i]))
        en = (row.get('en') or '').strip()
        if not en:
            blank += 1
            continue
        bad = sorted(set(en) - LEGAL)
        if bad:
            print('  %s: %r has no charset code for %s'
                  % (row['id'], en, ' '.join(repr(c) for c in bad)))
            return 1
        n_cells = compose(en)[0]
        if n_cells > CELLS:
            print('  %s: %r is %d cells in the %d-cell field'
                  % (row['id'], en, n_cells, CELLS))
            return 1
        m = ENTRY.match(lines[at])
        new = '%s"%s"%s' % (m.group(1), en, m.group(3))
        if new != lines[at]:
            changed += 1
        lines[at] = new

    named = [(r.get('en') or '').strip() for r in rows]
    need = board_tiles([t for t in named[:8] if t], named[8] or named[0])
    if need > POOL:
        print('  the board needs %d pool tiles, which is %d more than the %d '
              'the pool holds - the tails would blank' % (need, need - POOL, POOL))
        return 1

    print('guild titles: %d of %d translated, %d line(s) change, '
          'board needs %d of %d pool tiles'
          % (len(LABELS) - blank, len(LABELS), changed, need, POOL))
    if '--write' not in sys.argv:
        print('(dry run; pass --write to rewrite ps4.asm)')
        return 0
    io.open(ASM, 'w', encoding='utf-8', errors='replace',
            newline='\n').write('\n'.join(lines))
    print('rewrote the guild titles in ps4.asm')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
