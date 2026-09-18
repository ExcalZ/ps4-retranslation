"""Read the menu VWF pool's demand out of a savestate.

Accepts an Exodus .exs or a BlastEm native .state (see blastem_ram.py).

The measurement build keeps dedup keys for 200 tiles while only the first
87 have VRAM behind them, so PoolTop and Peak report the *true* deduped
demand rather than saturating at what VRAM can hold.

usage: python tools/poolpeak.py <savestate> [...]
"""
import re, sys, zipfile, os
from blastem_ram import work_ram

BASE = 0x5400          # VWF_RAM_Base, masked into the 64K work RAM image
TOP, PEAK, MARKS, KEYS = BASE+0x100, BASE+0x122, BASE+0x102, BASE+0x140
BATTLE_BASE = BASE + 0xAAC
TECH_LIST, SKILL_LIST = 0x412E, 0x4142
# Derived, not restated: menupool.py shrinks the pool whenever a new raw
# tile immediate appears in source, and a literal here would report a
# peak against a capacity the ROM no longer has.
_C = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "ps4disasm", "ps4.constants.asm"),
          encoding="utf-8", errors="replace").read()
VRAM_SLOTS = KEY_SLOTS = int(re.search(r"^VWFMENU_SLOTS\s*=\s*(\d+)",
                                       _C, re.M).group(1))

for p in sys.argv[1:]:
    ram = work_ram(p)
    w = lambda a: int.from_bytes(ram[a:a+2], "big")
    top, peak, battle_base = w(TOP), w(PEAK), w(BATTLE_BASE)
    marks = [w(MARKS+i*2) for i in range(16)]
    used = sum(1 for s in range(KEY_SLOTS) if any(ram[KEYS+s*8:KEYS+s*8+8]))
    print("%s" % os.path.basename(p))
    print("   live now  %3d   peak %3d   (VRAM holds %d)" % (top, peak, VRAM_SLOTS))
    print("   %s" % ("fits" if peak < VRAM_SLOTS
                     else "SATURATED at %d: demand met the ceiling, so the true"
                          " figure is this or higher" % VRAM_SLOTS
                     if peak == VRAM_SLOTS
                     else "OVER VRAM by %d tiles" % (peak - VRAM_SLOTS)))
    print("   non-blank keys resident: %d" % used)
    mode = w(0xEF00)
    depth, blocked, inhibit = ram[BASE+0x12C], ram[BASE+0x12D], ram[BASE+0x12E]
    allowed = (mode == 0xC and depth and not blocked and not inhibit)
    print("   reclaim gate: %s  (mode $%X, depth %d, blocked %d, inhibit %d,"
          " StripReuseOK %d)"
          % ("ALLOWED" if allowed else "denied", mode, depth, blocked,
             inhibit, ram[BASE+0x12A]))
    if allowed and peak >= VRAM_SLOTS:
        print("   -> sweep was permitted and still could not free a cell:"
              " the resident cells are genuinely live on the plane")
    print("   window marks: %s" % " ".join(map(str, marks)))
    print("   battle base: %d   tech IDs: %s   skill ID/count: %s" %
          (battle_base, ram[TECH_LIST:TECH_LIST+16].hex(" "),
           ram[SKILL_LIST:SKILL_LIST+16].hex(" ")))
    if peak >= KEY_SLOTS:
        print("   NOTE: peak reached the %d-key ceiling; the real demand is higher"
              % KEY_SLOTS)
