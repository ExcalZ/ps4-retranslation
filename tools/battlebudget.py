"""Report the battle pool budget: the persistent root and each transient surface.

Battle is deliberately outside the field reclaim capability - it keeps none of
the Window_Create/Destroy bookkeeping that makes a plane sweep safe to act on,
so `VWFMenu_Sweep` and `StripReuseOK` must never be granted there (see
work/handoff-vwf-pool.md for the two corruptions that came of trying).

That makes battle a pure budget problem: whatever the persistent HUD and enemy
banner cost is the root, and every transient surface has to fit in what is
left, from that root, without reclamation.

    python tools/battlebudget.py

Composed text dedupes by tile, so names sharing letters at the same pixel
phase cost once.  Strips do not: each takes a contiguous run of its own.  That
asymmetry is why the item page - long names, all strips - is the surface that
overflows first.
"""
import sys, io, json, re, os
sys.path.insert(0, 'tools')
from menustrip import compose

d = json.load(io.open('work/script_translated.json', encoding='utf-8'))
E = d['entries']
seg = lambda s: [(e.get('en') or '').strip() for e in E if e.get('segment') == s]
party  = [t for t in seg('03:000')[:5] if t]
enemies= [t for t in seg('02:001') if t]
eskill = [t for t in seg('02:002') if t]
techs  = [t for t in seg('00:002') if t]
skills = [t for t in seg('00:003') if t]
items  = [t for t in seg('00:001') if t and t != 'NOTHING']

constants = open('ps4disasm/ps4.constants.asm', encoding='utf-8', errors='replace').read()
SLOTS = int(re.search(r"^VWFMENU_SLOTS\s*=\s*(\d+)", constants, re.M).group(1))

def tiles(names):
    """composed text dedupes by TILE"""
    seen = set()
    for t in names:
        n, span = compose(t)
        for i in range(n):
            x = bytes(span[y*16+i] for y in range(8))
            if any(x): seen.add(x)
    return len(seen)

def runs(names):
    """strips take a contiguous run each, no dedupe between them"""
    return sum(compose(t)[0] for t in names)

print("battle pool budget, capacity %d slots\n" % SLOTS)
print("PERSISTENT (the root, once the HUD and enemy banner are live)")
p = tiles(party)
worst_enemy = max(enemies, key=lambda t: compose(t)[0])
e = tiles([worst_enemy])
print("  5 party names, composed      %2d" % p)
print("  enemy banner, composed       %2d   (worst: %s)" % (e, worst_enemy))
root = tiles(party + [worst_enemy])
print("  root, deduped together       %2d   -> %d free\n" % (root, SLOTS - root))

print("TRANSIENT, each measured from that root")
we = max(eskill, key=lambda t: compose(t)[0])
print("  enemy action name            %2d   (worst: %s)" % (compose(we)[0], we))
wt = max(techs, key=lambda t: compose(t)[0])
print("  player action name           %2d   (worst: %s)" % (compose(wt)[0], wt))
for label, pool, n in (("Tech page (8 rows)", techs, 8),
                       ("Skill page (8 rows)", skills, 8),
                       ("Item page (8 rows)", items, 8)):
    worst = sorted(pool, key=lambda t: -compose(t)[0])[:n]
    print("  %-28s %2d   worst case, strips" % (label, runs(worst)))
    print("  %-28s %2d   typical (mean %.1f cells)"
          % ("", round(n * sum(compose(t)[0] for t in pool)/len(pool)),
             sum(compose(t)[0] for t in pool)/len(pool)))
