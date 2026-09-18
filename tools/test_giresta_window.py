"""Soldier Fiend's Giresta must not leave the enemy action-name window behind.

work/giresta-slot3.state (BlastEm, ps4en_compose) is the "Giresta" window
opening at the top left.  The Giresta object then snapshots Plane A into
$FFFF2400 twice (loc_2301A and loc_231D0), and loc_B54A closes the window
by restoring rows 1-3 from that snapshot - so the snapshot must not hold
the window.  The US build cleared the wrong cells after the first snapshot
and nothing after the second; the window came back whole as it "closed".

This finishes opening the window, runs the second snapshot the way the
built ROM does (loc_24A08 + SoldierFiend_ClearSkillWindowSnapshot), runs
the erase to completion, and checks the plane.  It then repeats the erase
with the snapshot taken and NOT cleared - the US sequence - to show the
check would catch it.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastem_screen as bs
import menuharness as mh

STATE = "work/giresta-slot3.state"
SEALED = "work/giresta-sealed-slot4.state"    # same cast, Soldier Fiend under Sealis, frame $E
OBJ = 0xFFFF46C0                 # the enemy action-name window object ($C)
PA = 0xFFFF8000                  # Plane_A_Buffer


def machine(sym, state=STATE):
    st = bs.read_state(state)
    rom = open(mh.ROM, "rb").read()
    return mh.Machine(rom, {"ram": st["ram"], "vram": st["vram"], "d": [0] * 8,
                            "a": [0] * 7, "sp": 0xFFFFFE00, "pc": 0, "autoinc": 2})


def call(m, addr, **regs):
    m.pc = addr
    for k, v in regs.items():
        (m.d if k[0] == "d" else m.a)[int(k[1])] = v
    m.a[7] = 0xFFFFFE00 - 4
    m.wl(m.a[7], m.SENTINEL)
    n = 0
    while not m.step():
        n += 1
        assert n < 2000000, "runaway"


def window_rows(m):
    return [[m.rw(PA + r * 0x80 + c * 2) & 0x7FF for c in range(16)] for r in (1, 2, 3)]


def run(sym, clear):
    m = machine(sym)
    assert m.rw(OBJ + 0x12) == 0x3E, "state is not the Giresta window"
    buf = m.rl(OBJ + 0x14)                       # finish opening: copy the buffer in
    for r in range(3):
        for c in range(12):
            m.ww(PA + (r + 1) * 0x80 + (2 + c) * 2, m.rw(buf + r * 0x18 + c * 2))
    m.ww(OBJ + 0x18, 0xC)
    m.ww(OBJ + 2, 4)
    assert any(any(row) for row in window_rows(m))
    call(m, sym["loc_24A08"])                    # the object's end-of-action snapshot
    if clear:
        call(m, sym["SoldierFiend_ClearSkillWindowSnapshot"])
    for _ in range(12):                          # the erase, one frame per call
        if m.rw(OBJ + 2) == 5:
            break
        call(m, sym["loc_B54A"], a4=OBJ)
    assert m.rw(OBJ + 2) == 5, "erase did not finish"
    return window_rows(m)


def sealed(sym):
    """The tech-sealed path (loc_230EE..loc_230FE) must re-snapshot the plane
    after redrawing the enemy, as loc_231D0 and the JP do; the US did not,
    so the cast pose drawn at loc_2301A came back with the next window
    restore.  loc_254F4 (the redraw) goes through EniDecomp, which emu68k
    does not run: stub it and plant a marker tile - a fresh snapshot is the
    only way the marker can reach $FFFF2400."""
    m = machine(sym, SEALED)
    obj = 0xFFFFDC00
    assert m.rw(obj) == 0x8378 and m.rb(obj + 0x11) == 0xE, "state is not the sealed Giresta at frame $E"
    m.ww(sym["loc_254F4"], 0x4E75)
    m.ww(PA + 8 * 0x80 + 17 * 2, 0x7FF)
    for _ in range(60):
        if m.rw(obj) == 0:
            break
        call(m, sym["loc_22FC0"], a4=obj)
    assert m.rw(obj) == 0 and m.rw(0xFFFF4100) == 0x16, "object did not finish"
    assert m.rw(0xFFFF2400 + 8 * 0x50 + 17 * 2) == 0x7FF, "plane was not re-snapshotted"
    assert all(m.rw(0xFFFF2400 + r * 0x50 + c * 2) == 0
               for r in (1, 2, 3) for c in range(2, 14)), "window rows not cleared"
    print("  sealed:  object ran to Battle_Routine $16 and re-snapshotted the plane")


def main():
    sym = mh.Symbols()
    sealed(sym)
    rows = run(sym, clear=True)
    left = sum(1 for row in rows for t in row if t)
    print("  built:   %d tiles left in rows 1-3 after the erase" % left)
    assert left == 0, rows
    rows = run(sym, clear=False)
    left = sum(1 for row in rows for t in row if t)
    print("  US path: %d tiles left (the bug this guards against)" % left)
    assert left > 0
    print("test_giresta_window: OK")


if __name__ == "__main__":
    main()
