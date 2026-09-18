"""Label every pool slot in a savestate by what its key spells.

    python tools/poolcells.py <savestate> [...]

For the composed-name build (and for composed text on either build): each
resident key is matched against the cells of every menu name and party
name, so a slot prints as e.g. `Laser Barrier[3]`.  Then the plane is walked
row by row, printing the slot each pool cell points at, so a cell that
displays the wrong tile shows up as a slot whose label does not belong on
that row.  Slots at or above PoolTop are flagged: they are live on screen
but no longer owned, and the next allocation will overwrite them.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blastem_ram import work_ram
import menustrip

BASE = 0x5400
C = open("ps4disasm/ps4.constants.asm", encoding="utf-8", errors="replace").read()
def off(name):
    return BASE + int(re.search(r"^%s\s*=\s*VWF_RAM_Base\+\$([0-9A-Fa-f]+)" % name, C, re.M).group(1), 16)
TOP, KEYS, REFS, MARKS = off("VWFMenu_PoolTop"), off("VWFMenu_Keys"), off("VWFMenu_Refs"), off("VWFMenu_Marks")
SLOTS = int(re.search(r"^VWFMENU_SLOTS\s*=\s*(\d+)", C, re.M).group(1))
PLANE = int(re.search(r"^Plane_A_Buffer\s*=\s*ramaddr\(\$([0-9A-Fa-f]+)\)", C, re.M).group(1), 16) & 0xFFFF
tileslot = open("ps4disasm/vwf/pooltile.bin", "rb").read()

d = json.load(open("work/script_translated.json", encoding="utf-8"))
ent = d["entries"] if isinstance(d, dict) and "entries" in d else d
segs = {}
for x in ent:
    segs.setdefault(x.get("segment") or x["id"].rsplit("#", 1)[0], []).append(x)
texts = set()
for seg, label, budget, symbol in menustrip.TABLES:
    for x in segs.get(seg, []):
        texts.add(x.get("en") or "")
for x in segs.get("00:006", []) + segs.get("00:005", []):     # party names, combos
    texts.add(x.get("en") or "")
by_key = {}
for t in sorted(texts):
    try:
        cells, span = menustrip.compose(t)
    except KeyError:
        continue
    for c in range(cells):
        k = bytes(span[y * 16 + c] for y in range(8))
        by_key.setdefault(k, "%s[%d]" % (t, c))

for p in sys.argv[1:]:
    ram = work_ram(p)
    w = lambda a: int.from_bytes(ram[a:a + 2], "big")
    top = w(TOP)
    print("== %s  PoolTop %d  marks %s" % (os.path.basename(p), top, [w(MARKS + i * 2) for i in range(16)]))
    label = {}
    for s in range(SLOTS):
        k = bytes(ram[KEYS + s * 8:KEYS + s * 8 + 8])
        if k == bytes(8):
            label[s] = "blank" if ram[REFS + s] else "-"
        else:
            label[s] = by_key.get(k, "?" + k.hex())
    for s in range(SLOTS):
        if label[s] != "-":
            print("   slot %2d refs %3d %s%s" % (s, ram[REFS + s], label[s], "   ABOVE PoolTop" if s >= top else ""))
    # Plane rows, read as names: each run of pool cells is matched against
    # every name's cell sequence; the best match is printed, with any cell
    # whose key is not that name's cell marked CORRUPT (what it holds instead).
    seqs = {}
    for t in sorted(texts):
        try:
            cells, span = menustrip.compose(t)
        except KeyError:
            continue
        seqs[t] = [bytes(span[y * 16 + c] for y in range(8)) for c in range(cells)]
    keyof = lambda s: bytes(ram[KEYS + s * 8:KEYS + s * 8 + 8])
    print("   plane, by name (slots in brackets; ! = at or above PoolTop):")
    for row in range(32):
        runs, run = [], []
        for col in range(64):
            t = w(PLANE + row * 128 + col * 2) & 0x7FF
            o = t - 0x680
            s = tileslot[o] if 0 <= o < len(tileslot) else 0xFF
            if s != 0xFF:
                run.append((col, s))
            elif run:
                runs.append(run); run = []
        if run: runs.append(run)
        for run in runs:
            keys = [keyof(s) for _, s in run]
            best, score = None, -1
            for t, sq in seqs.items():
                n = sum(1 for i, k in enumerate(keys) if i < len(sq) and sq[i] == k)
                if n > score or (n == score and best and len(sq) < len(seqs[best])):
                    best, score = t, n
            sq = seqs[best]
            bad = ["col %d slot %d holds %s" % (c, s, label.get(s, "?"))
                   for i, (c, s) in enumerate(run) if i >= len(sq) or sq[i] != keys[i]]
            above = [s for _, s in run if s >= top]
            print("   row %2d col %2d  %-16s %d/%d cells  slots %s%s%s"
                  % (row, run[0][0], best, score, len(run),
                     "-".join(str(s) for s in (run[0][1], run[-1][1])),
                     "  !" + str(above) if above else "",
                     ("  CORRUPT: " + "; ".join(bad)) if bad else ""))
