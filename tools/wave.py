"""Dump or count the rows a translation wave can actually land.

A row only reaches the ROM if treeport can port it, so this lists exactly the
rows whose JP engine fingerprint already matches the US message at the same
index.  Empty messages and bare {ctl.F6} event markers are excluded: both look
untranslated for ever and neither carries text to translate.

    python tools/wave.py                 remaining, by stream
    python tools/wave.py 1DA026          dump one stream for translation
"""
import io, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import treeport, dialogue, trpatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load():
    """(stream -> tree group, entries, engine cache).

    Routing must match treeport's, or this tool lies about what is left.  It
    used to test only the base tree, and after treeport learned about parallel
    trees, relocations and reorderings that made it report zero rows remaining
    while 253 were in fact portable.
    """
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
            (int(suf), treeport.jp_engine_codes(e['hex'])))
    groups = {st: treeport.tree_group(rws, mapped[st], cache)
              for st, rws in bystream.items()}
    return groups, ents, cache


def todo(groups, ents, cache, only=None):
    """Rows that are untranslated, portable, and have text."""
    out = []
    for e in ents:
        st = e.get('stream')
        suf = e['id'].split('#')[1]
        if st is None or not suf.isdigit() or st not in groups:
            continue
        if only is not None and st != only:
            continue
        if (e.get('en') or '').strip():
            continue
        idx, ours = int(suf), treeport.jp_engine_codes(e['hex'])
        tree = treeport.target_tree(groups[st], idx, ours, cache)
        eng = cache[tree].get(idx)
        if eng is None:
            continue
        theirs = tuple(c for c, _ in eng)
        # An exact fingerprint is not the only portable case: treeport also
        # drops surplus $F9 delays, which the localisers stripped wholesale.
        # Demanding equality here hid three rows that port perfectly well,
        # among them Forren shutting Daughter down.
        if ours != theirs and tuple(c for c in ours if c != 0xF9) != theirs:
            continue
        if not trpatch.TOK.sub('', e['jp']).strip():
            continue
        # A bare {ctl.F6} carrying a single stray kana is an event marker, not
        # a line of dialogue.  52 of these are all that is left of the portable
        # set, and translating them would be translating engine bookkeeping.
        tok = trpatch.engine_tokens(e['jp'])
        if tok and tok[-1] == 'ctl.F6' and len(trpatch.TOK.sub('', e['jp']).strip()) <= 2:
            continue
        out.append(e)
    return out


def main():
    groups, ents, cache = load()
    if len(sys.argv) > 1:
        s = int(sys.argv[1], 16)
        for e in todo(groups, ents, cache, s):
            tok = trpatch.engine_tokens(e['jp'])
            print(f"{e['id']} {tok if tok else ''}")
            print(f"  JP {e['jp']}")
            u = (e.get('us') or '').strip()
            print(f"  US {u if u else '(blank)'}")
        return
    rows = todo(groups, ents, cache)
    by = {}
    for e in rows:
        by.setdefault(e['stream'], []).append(e)
    print(f"{'stream':10} {'tree':5} {'todo':>5} {'JP chars':>9}")
    for st in sorted(by):
        n = sum(len(trpatch.TOK.sub('', e['jp'])) for e in by[st])
        print(f"${st:06X}   {groups[st][0]:<5} {len(by[st]):5} {n:9}")
    print(f"\n{len(rows)} rows remaining across {len(by)} streams")


if __name__ == '__main__':
    main()
