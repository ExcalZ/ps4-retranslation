"""Battle-menu automation on top of blastem_drive, plus a pool-frontier trace.

    python tools/battle_drive.py work/pd-slot7.state --rounds 2 --shots out/
    python tools/battle_drive.py work/pd-slot7.state \
        --script "comd browse:item.3 skill:1.2 tech:0.0 attack attack attack enemy"

Script tokens: `comd` (confirm COMD at the main menu), `attack`, `defend`,
`skill:PAGE.INDEX` / `tech:...` / `item:...` (open the list, page right,
move down, confirm, confirm a target if asked), `browse:KIND.PAGES` (page
through and cancel; a screenshot per page under --shots), `enemy` (run to the
next main menu), `wN` (N frames), single pad letters.  One token per party
member's command; the run then waits through the enemy phase.

Menu state is read from Battle_Routine / Battle_Routine_2 (RunBattleRoutines2's
1-based table), and the command icon is set by writing the character's slot
of Battle_Char_Comd_Index before confirming, so the run does not depend on
where the cursor was left.  Every store to VWFMenu_PoolTop or a battle mark
is logged with the frame it happened on (see battlepool_trace.frontier_sites),
together with every cell the pool refused (VWFMenu_Alloc_FullReally) - the
symptom the player sees as a hole in a name - and, at the end, the lag frames
(VInts the main loop was not ready for) with the PC each one interrupted.
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blastem_drive import BlastEm, listing_address
from battlepool_trace import frontier_sites, TOP, PEAK, MARKS
import winshot

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BATTLE_ROUTINE, BATTLE_ROUTINE_2, TOTAL_CMD = 0xFFFF4100, 0xFFFF4108, 0xFFFF4106
CMD_INDEX, ITEM_INDEX, GAME_MODE = 0xFFFF41A2, 0xFFFF41C4, 0xFFFFEF00
R2 = {"main": 2, "char": 5, "tech": 8, "target_enemy": 0xC, "target_char": 0xD, "skill": 0x11, "item": 0x17}
ICON = {"attack": 0, "tech": 1, "skill": 2, "item": 3, "defend": 4}


class Battle:
    def __init__(self, em, log=print):
        self.em, self.log = em, log
        lst = em.lst
        self.sites = dict(frontier_sites(lst))
        self.full = listing_address(lst, "VWFMenu_Alloc_FullReally")
        self.grow = listing_address(lst, "VWFMenu_Alloc_Grow")
        for a in list(self.sites) + [self.full, self.grow]:
            em.breakpoint(a)
        self.blank = self.grows = 0

    def snapshot(self):
        em = self.em
        return "top %2d base %2d act %2d ene %2d res %2d eff %2d" % (
            em.word(TOP), em.word(MARKS["VWFMenu_BattleBase"]), em.word(MARKS["VWFMenu_BattleActionMark"]),
            em.word(MARKS["VWFMenu_BattleEnemyMark"]), em.word(MARKS["VWFMenu_BattleResultMark"]),
            em.word(MARKS["VWFMenu_BattleEffectMark"]))

    def hook(self, pc):
        em = self.em
        if pc == self.grow:
            self.grows += 1
        elif pc == self.full:
            self.blank += 1
            self.log("  frame %5d  POOL FULL: cell left blank        %s" % (em.frame, self.snapshot()))
        else:
            self.log("  frame %5d  %06X %-52s %s" % (em.frame, pc, self.sites[pc].split(",")[0] + "," + self.sites[pc].split(",")[1][:30], self.snapshot()))

    def r2(self):
        return self.em.word(BATTLE_ROUTINE_2) & 0x7FFF

    def state(self):
        return (self.em.word(GAME_MODE), self.em.word(BATTLE_ROUTINE), self.r2())

    def wait(self, r2, limit=3000):
        """Run until Battle_Routine is 0 (menus) and Battle_Routine_2 is one of r2."""
        want = {R2[x] if isinstance(x, str) else x for x in ([r2] if not isinstance(r2, (list, tuple, set)) else r2)}
        for _ in range(limit):
            if self.em.word(GAME_MODE) != 0x14:
                raise RuntimeError("left battle mode at frame %d" % self.em.frame)
            if self.em.word(BATTLE_ROUTINE) == 0 and self.r2() in want:
                return self.r2()
            self.em.step_frame(self.hook)
        raise RuntimeError("frame %d: waited for %s, still at %s" % (self.em.frame, r2, self.state()))

    def press(self, b, hold=4, release=12):
        self.em.press(b, hold=hold, release=release, hook=self.hook)

    def comd(self):
        self.wait("main")
        self.press("C")

    def choose(self, icon):
        """At a character's command menu pick an icon by writing its index."""
        self.wait("char")
        n = self.em.word(TOTAL_CMD)
        self.em.write(CMD_INDEX + 2 * n, ICON[icon].to_bytes(2, "big"))
        self.em.frames(2, self.hook)              # let the cursor sprite settle
        self.press("C")

    def attack(self):
        self.choose("attack")
        r = self.wait(["target_enemy", "target_char", "char", "main"])
        if r in (R2["target_enemy"], R2["target_char"]):
            self.press("C")

    def pick_from_list(self, kind, pages=0, index=0):
        """Open the skill/item/tech window, page right `pages` times, move
        the cursor to `index`, confirm; then confirm a target if asked."""
        self.choose(kind)
        self.wait(kind)
        for _ in range(pages):
            self.press("R")
        for _ in range(index):
            self.press("D")
        self.press("C")
        r = self.wait(["target_enemy", "target_char", "char", "main", kind])
        if r in (R2["target_enemy"], R2["target_char"]):
            self.press("C")

    def browse(self, kind, pages=2, shot=None):
        """Open a list, page right and back (a screenshot per page when
        `shot` is a path prefix), cancel out."""
        self.choose(kind)
        self.wait(kind)
        for i in range(pages):
            self.press("R")
            if shot:
                self.em.frames(3, self.hook)
                winshot.capture(self.em.proc.pid, "%s_p%d.png" % (shot, i + 1))
        for _ in range(pages):
            self.press("L")
        self.press("B")
        self.wait("char")


def run_script(b, script, shots=None):
    em = b.em
    for i, tok in enumerate(script.split()):
        cmd, _, arg = tok.partition(":")
        if cmd == "comd":
            b.comd()
        elif cmd == "attack":
            b.attack()
        elif cmd in ("skill", "item", "tech"):
            page, _, idx = arg.partition(".")
            b.pick_from_list(cmd, int(page or 0), int(idx or 0))
        elif cmd == "browse":
            kind, _, pages = arg.partition(".")
            b.browse(kind or "item", int(pages or 2), shots and os.path.join(shots, "%03d_browse_%s" % (i, kind)))
        elif cmd == "defend":
            b.choose("defend")
        elif cmd == "enemy":                       # the enemy phase: run to the next main menu
            b.wait("main", limit=int(arg or 6000))
        elif cmd.startswith("w"):
            em.frames(int(cmd[1:]), b.hook)
        elif cmd in ("U", "D", "L", "R", "B", "C", "A", "S"):
            b.press(cmd)
        else:
            raise ValueError(tok)
        b.log("%-12s frame %5d  %s  peak %2d  grows %d  blank %d  lag %d  state %s" % (
            tok, em.frame, b.snapshot(), em.word(PEAK), b.grows, b.blank, em.lag, b.state()))
        if shots:
            os.makedirs(shots, exist_ok=True)
            winshot.capture(em.proc.pid, os.path.join(shots, "%03d_%s.png" % (i, tok.replace(":", "_"))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("state")
    ap.add_argument("--rom", default=os.path.join(ROOT, "work", "ps4en_compose.bin"))
    ap.add_argument("--script", default="comd attack attack attack attack attack enemy")
    ap.add_argument("--rounds", type=int, default=1)
    ap.add_argument("--shots")
    a = ap.parse_args()
    lst = os.path.splitext(a.rom)[0] + ".lst"
    with BlastEm(a.rom, a.state, lst=lst) as em:
        b = Battle(em)
        b.log("start        frame %5d  %s  peak %2d  state %s" % (em.frame, b.snapshot(), em.word(PEAK), b.state()))
        for r in range(a.rounds):
            b.log("== round %d" % (r + 1))
            run_script(b, a.script, a.shots and os.path.join(a.shots, "r%d" % (r + 1)))
        if em.lag_samples:
            b.log("lag frames: %d of %d VInts; interrupted PCs (frame, pc):" % (em.lag, em.vints))
            import collections
            by_pc = collections.Counter(pc for _f, _flag, pc in em.lag_samples)
            for pc, n in by_pc.most_common(20):
                b.log("  %4d x pc %06X" % (n, pc))
            b.log("  (frame pc): %s" % " ".join("%d:%06X" % (f, pc) for f, _flag, pc in em.lag_samples))


if __name__ == "__main__":
    main()
