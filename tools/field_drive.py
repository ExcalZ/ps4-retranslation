"""Replay a field-menu savestate under BlastEm and cost each keypress.

    python tools/field_drive.py work/field-slot0.state "R R L L D D B" [--shots out/]

For every token (a pad letter, `X*n` to hold n frames, `wN` to idle N
frames) it reports how many frames the token took, how many of them the
main loop overran (lag), and what the menu VWF did meanwhile: strings
composed, pool lookups, slots taken, cells refused, sweeps.  That is the
whole cost of a field window open, page flip or equip: the field never
composes per frame, so what the player can feel is these hitches.
"""
import argparse, collections, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blastem_drive import BlastEm, listing_address
from battlepool_trace import TOP, PEAK
import winshot

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COUNTED = ("VWFMenu_DrawString", "VWFMenu_Alloc", "VWFMenu_Alloc_Take", "VWFMenu_Alloc_FullReally",
           "VWFMenu_Sweep", "VWFMenu_Alloc_Scan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("state")
    ap.add_argument("script")
    ap.add_argument("--rom", default=os.path.join(ROOT, "work", "ps4en_compose.bin"))
    ap.add_argument("--shots")
    a = ap.parse_args()
    lst = os.path.splitext(a.rom)[0] + ".lst"
    with BlastEm(a.rom, a.state, lst=lst) as em:
        names = {}
        for n in COUNTED:
            try:
                addr = listing_address(lst, n)
            except KeyError:          # the strips build has no FullReally block
                continue
            names[addr] = n
            em.breakpoint(addr)
        counts = collections.Counter()

        def hook(pc):
            if pc in names:
                counts[names[pc]] += 1

        print("%-8s %6s %4s %7s %6s %6s %5s %7s %6s %4s %4s" % (
            "token", "frames", "lag", "strings", "lookup", "scan", "taken", "refused", "sweeps", "top", "peak"))
        for i, tok in enumerate(a.script.split()):
            f0, l0 = em.frame, em.lag
            counts.clear()
            if tok.startswith("w"):
                em.frames(int(tok[1:]), hook)
            else:
                btn, _, hold = tok.partition("*")
                em.press(btn, hold=int(hold or 4), release=40, hook=hook)
            print("%-8s %6d %4d %7d %6d %6d %5d %7d %6d %4d %4d" % (
                tok, em.frame - f0, em.lag - l0, counts["VWFMenu_DrawString"], counts["VWFMenu_Alloc"],
                counts["VWFMenu_Alloc_Scan"], counts["VWFMenu_Alloc_Take"], counts["VWFMenu_Alloc_FullReally"],
                counts["VWFMenu_Sweep"], em.word(TOP), em.word(PEAK)))
            if a.shots:
                os.makedirs(a.shots, exist_ok=True)
                winshot.capture(em.proc.pid, os.path.join(a.shots, "%03d_%s.png" % (i, tok.replace("*", "x"))))
        by_pc = collections.Counter(pc for _f, _fl, pc in em.lag_samples)
        if by_pc:
            print("lag PCs:", " ".join("%06X x%d" % (pc, n) for pc, n in by_pc.most_common(12)))


if __name__ == "__main__":
    main()
