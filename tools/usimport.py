"""Attach the official US text to each JP entry as a `us` field.

Provenance is carried by WHICH FIELD holds the text, not by a guess:

    en present            -> our retranslation
    en empty, us present  -> will ship as the US baseline
    neither               -> nothing written for this line yet

The US build re-partitioned 26 JP streams into 43 trees, so a JP stream can
spill into a later tree with its indices restarting at zero. Messages are
paired on their ENGINE control codes; layout codes ($FC/$FD/$F5) are excluded
because the localisers re-wrapped every line and those never agree.

A pairing is only written when it is unambiguous. A wrong pairing would show
the translator the wrong reference text, which is worse than showing none.
"""
import io, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dialogue

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, 'ps4disasm', 'script')
LAYOUT = {0xFC, 0xFD, 0xF5}


def load_tree(n):
    """{index: (fingerprint, text)} for one disassembly tree."""
    p = os.path.join(SCRIPT, f'dialogue {n}.asm')
    out, cur, seq, txt = {}, None, [], []
    for ln in io.open(p, encoding='utf-8', errors='replace'):
        m = re.match(r'^;\s*\$?([0-9A-Fa-f]+)\s*$', ln.strip())
        if m:
            if cur is not None:
                out[cur] = (tuple(seq), ' '.join(txt))
            cur = int(m.group(1), 16); seq, txt = [], []
            continue
        if cur is None:
            continue
        quoted = re.findall(r'"([^"]*)"', ln)
        if quoted:
            txt.extend(quoted); continue
        for b in re.findall(r'\$([0-9A-Fa-f]{2})', ln):
            v = int(b, 16)
            if 0xF0 <= v <= 0xFE and v not in LAYOUT:
                seq.append(v)
    if cur is not None:
        out[cur] = (tuple(seq), ' '.join(txt))
    return out


def main():
    tm = json.load(io.open(os.path.join(ROOT, 'work', 'tree_map.json'),
                           encoding='utf-8'))['map']
    mapped = {int(k, 16): v for k, v in tm.items()}
    order = sorted(mapped.values())
    trees = {n: load_tree(n) for n in range(1, 44)}

    ents = dialogue.load(os.path.join(ROOT, 'work', 'dialogue_full.json'))
    stat = {'exact': 0, 'unique': 0, 'skipped': 0, 'nonstream': 0}
    for e in ents:
        st = e.get('stream')
        suf = e['id'].split('#')[1]
        if st is None or not suf.isdigit() or st not in mapped:
            stat['nonstream'] += 1
            continue
        i = int(suf)
        fp = tuple(x for x in bytes.fromhex(e['hex'])
                   if 0xF0 <= x <= 0xFE and x not in LAYOUT)
        base = mapped[st]
        nxt = next((t for t in order if t > base), 44)
        cands = list(range(base, nxt))          # this tree plus its US splits

        hit = None
        t0 = trees[base]
        if i in t0 and t0[i][0] == fp:          # same index, same fingerprint
            hit = t0[i][1]; stat['exact'] += 1
        elif fp:                                 # else a unique fingerprint match
            found = [v[1] for c in cands for v in trees[c].values() if v[0] == fp]
            if len(found) == 1:
                hit = found[0]; stat['unique'] += 1
        if hit is None:
            stat['skipped'] += 1
        elif hit.strip():
            e['us'] = hit.strip()
    dialogue.save(ents, os.path.join(ROOT, 'work', 'dialogue_full.json'))
    total = stat['exact'] + stat['unique'] + stat['skipped']
    print(f'US baseline attached to {stat["exact"] + stat["unique"]}/{total} '
          f'stream messages')
    print(f'  same index + fingerprint : {stat["exact"]}')
    print(f'  unique fingerprint match : {stat["unique"]}')
    print(f'  left unpaired            : {stat["skipped"]}')


if __name__ == '__main__':
    main()
