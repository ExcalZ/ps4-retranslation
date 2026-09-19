"""Replay a battle savestate through every mid-battle enemy rebuild and show
that the recomposed group-name boxes survive the pool rewinds that follow.

    python tools/enemy_rebuild_trace.py work/compose9-metaslug.state [--rom R] [--arms|--deleter] [--shots DIR]

The rebuild (loc_14D46) is what the last two Zol Slugs' Fusion, ArthroPod +
Wiredine's Combine (Life Deleter) and Blade Right + Haken Left's Combine
(Twin Arms) all run after their animation.  It recomposes the enemy-name
boxes while the acting enemy's action-name window is still open, so before
VWFMenu_BattleRebuildNames the new names sat above VWFMenu_BattleEnemyMark,
the window's close rewound under them and the next turn's COMMAND/MACRO/RUN
labels took their cells ("ND MACRO" in the Meta Slug's box).

The state holds a lone Meta Slug, which never splits on its own, so the
first enemy turn is forced to the split object (its formation would be four
Jr. Ooze) and the spawned formation is rewritten at the rebuild to the pair
under test; from there the party only defends and the pair's own AI chooses
Fusion / Combine (the Zol Slug rule: exactly two alive).  Every rebuild, the
marks around it, and the two name boxes' pool slots are printed per round;
the fix holds when the slots a rebuild composed are still the ones the box
names a round later.
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blastem_drive import BlastEm, listing_address
from battle_drive import Battle, run_script
import winshot

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORMATION = 0xFFFF41F0
PAIRS = {"slugs": "0022 0822", "arms": "0054 0856", "deleter": "0017 0819"}   # (x, id) pairs, $FF ends


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("state")
    ap.add_argument("--rom", default=os.path.join(ROOT, "work", "ps4en_compose.bin"))
    ap.add_argument("--arms", action="store_true", help="Blade Right + Haken Left -> Twin Arms")
    ap.add_argument("--deleter", action="store_true", help="ArthroPod + Wiredine -> Life Deleter")
    ap.add_argument("--rounds", type=int, default=6)
    ap.add_argument("--shots")
    a = ap.parse_args()
    pair = PAIRS["arms" if a.arms else "deleter" if a.deleter else "slugs"]
    lst = os.path.splitext(a.rom)[0] + ".lst"

    st = open(os.path.join(ROOT, "ps4disasm", "vwf", "poolslot.bin"), "rb").read()
    slot_of_tile = {int.from_bytes(st[i:i + 2], "big"): i // 2 for i in range(0, len(st), 2)}

    def names(em):
        out = []
        for buf in (0xFFFF3168, 0xFFFF31B0):                 # the two group-name box maps
            row = em.read(buf + 0x18, 0x18)
            cells = [int.from_bytes(row[i:i + 2], "big") & 0x7FF for i in range(0, 0x18, 2)]
            out.append([slot_of_tile.get(c - 0x680, "-") if c != 0x680 else "." for c in cells[1:-1]])
        return out

    with BlastEm(a.rom, a.state, lst=lst) as em:
        b = Battle(em)
        rebuild = listing_address(lst, "loc_14D46")
        decide = listing_address(lst, "loc_D024")           # ability chosen, attack about to dispatch
        for at in (rebuild, decide):
            em.breakpoint(at)
        base_hook = b.hook
        forced = {}

        def hook(pc):
            if pc == rebuild:
                b.log("  frame %5d  loc_14D46 rebuild   %s  formation %s" % (em.frame, b.snapshot(), em.read(FORMATION, 16).hex()))
                if forced.get("split") and not forced.get("pair"):
                    em.write(FORMATION, bytes.fromhex("00000000 0203 " + pair + " 10ff 000000000000"))
                    forced["pair"] = 1
                    b.log("  frame %5d  spawned formation rewritten to %s" % (em.frame, pair))
            elif pc == decide:
                a4 = em.regs()["a"][4]
                fid, ability = em.word(a4 + 0x12), em.word(a4 + 0x24)
                if fid == 0x24 and not forced.get("split"):
                    em.write(a4 + 0x24, (0x12).to_bytes(2, "big"))
                    forced["split"] = 1
                    b.log("  frame %5d  Meta Slug forced to its split object" % em.frame)
                elif ability:
                    b.log("  frame %5d  enemy %02X chose ability %02X" % (em.frame, fid, ability))
            else:
                base_hook(pc)
        b.hook = hook
        b.log("start  %s  names %s" % (b.snapshot(), names(em)))
        for r in range(a.rounds):
            b.log("== round %d" % (r + 1))
            try:
                run_script(b, "comd defend defend defend defend defend enemy")
            except RuntimeError as e:
                b.log("stopped: %s" % e)
                break
            ids = [em.word(0xFFFF4540 + i * 0x40 + 0x12) for i in range(4) if em.word(0xFFFF4540 + i * 0x40)]
            b.log("round %d: enemies %s  names %s  %s" % (r + 1, ["%02X" % i for i in ids], names(em), b.snapshot()))
            if a.shots:
                os.makedirs(a.shots, exist_ok=True)
                em.frames(2, hook)
                winshot.capture(em.proc.pid, os.path.join(a.shots, "round%d.png" % (r + 1)))


if __name__ == "__main__":
    main()
