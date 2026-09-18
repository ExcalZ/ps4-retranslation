"""Replay a battle savestate under BlastEm and log every pool frontier move.

    python tools/battlepool_trace.py work/pd-slot7.state "C R*4 C w600 ..." [--rom work/ps4en_compose.bin]

Each token is a pad press (letters from blastem_drive.BUTTON, `*n` = hold n
frames) or `wN` = run N frames.  Every instruction in the built ROM that
writes VWFMenu_PoolTop or one of the battle marks is breakpointed and logged
with the frame number and the pool state, together with every cell the pool
refused (VWFMenu_Alloc_FullReally) and each Alloc growth, so a leak shows up
as a mark that is set from a PoolTop nobody rewound.  tools/battle_drive.py
drives the menus by state instead of by keypress and is the usual entry.
"""
import argparse, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blastem_drive import BlastEm, listing_address
import winshot

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = open(os.path.join(ROOT, "ps4disasm/ps4.constants.asm"), encoding="utf-8", errors="replace").read()
BASE = 0xFFFF5400


def ram(name):
    return BASE + int(re.search(r"^%s\s*=\s*VWF_RAM_Base\+\$([0-9A-Fa-f]+)" % name, C, re.M).group(1), 16)


TOP, BBASE, PEAK = ram("VWFMenu_PoolTop"), ram("VWFMenu_BattleBase"), ram("VWFMenu_Peak")
MARKS = {n: ram(n) for n in ("VWFMenu_BattleBase", "VWFMenu_BattleActionMark", "VWFMenu_BattleEnemyMark",
                             "VWFMenu_BattleResultMark", "VWFMenu_BattleEffectMark")}


def frontier_sites(lst):
    """(address, source) of every instruction that stores to PoolTop or a mark."""
    out = []
    for line in open(lst, encoding="utf-8", errors="replace"):
        m = re.match(r"(?:\(\d+\))?\s*\d+/\s*([0-9A-F]+) : [0-9A-F ]+\t(.*)", line)   # "(1)" prefixes included files
        if not m:
            continue
        src = m.group(2).split(";")[0].strip()
        if re.search(r",\s*\(VWFMenu_(PoolTop|Battle\w*Mark|BattleBase)\)", src):
            out.append((int(m.group(1), 16), src))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("state")
    ap.add_argument("script")
    ap.add_argument("--rom", default=os.path.join(ROOT, "work", "ps4en_compose.bin"))
    ap.add_argument("--shots", help="directory for a screenshot after every token")
    a = ap.parse_args()
    lst = os.path.splitext(a.rom)[0] + ".lst"
    sites = dict(frontier_sites(lst))
    grow = listing_address(lst, "VWFMenu_Alloc_Grow")
    full = listing_address(lst, "VWFMenu_Alloc_FullReally")   # a refused cell; DrawString_Full is also the ink-less blank
    with BlastEm(a.rom, a.state, lst=lst) as em:
        for addr in list(sites) + [grow, full]:
            em.breakpoint(addr)
        state = {"grow": 0, "full": 0}

        def snapshot():
            return "top %2d base %2d act %2d ene %2d res %2d eff %2d" % (
                em.word(TOP), em.word(MARKS["VWFMenu_BattleBase"]), em.word(MARKS["VWFMenu_BattleActionMark"]),
                em.word(MARKS["VWFMenu_BattleEnemyMark"]), em.word(MARKS["VWFMenu_BattleResultMark"]),
                em.word(MARKS["VWFMenu_BattleEffectMark"]))

        def hook(pc):
            if pc == grow:
                state["grow"] += 1
                return
            if pc == full:
                state["full"] += 1
                print("  frame %5d  BLANK CELL (pool full) %s" % (em.frame, snapshot()))
                return
            src = sites[pc]
            print("  frame %5d  %06X %-58s %s" % (em.frame, pc, src, snapshot()))

        def flush(tag):
            print("%-8s frame %5d  %s  peak %2d  grows %d  blank cells %d" % (
                tag, em.frame, snapshot(), em.word(PEAK), state["grow"], state["full"]))

        flush("start")
        for i, tok in enumerate(a.script.split()):
            if tok.startswith("w"):
                em.frames(int(tok[1:]), hook)
            else:
                btn, _, hold = tok.partition("*")
                em.press(btn, hold=int(hold or 4), release=30, hook=hook)
            flush(tok)
            if a.shots:
                os.makedirs(a.shots, exist_ok=True)
                winshot.capture(em.proc.pid, os.path.join(a.shots, "%03d_%s.png" % (i, tok.replace("*", "x"))))


if __name__ == "__main__":
    main()
