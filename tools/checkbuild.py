"""Invariants that must hold before a rom is worth putting in front of anyone.

Every check here corresponds to a bug that actually shipped this project a
broken build.  Failing here costs a second; failing in the emulator costs a
ten-minute play session, which is the scarce resource.

  1 RAM map overlap.  VWFMenu_Marks is 16 words at +$102, and Peak, Mark_Cur
    and RemapIdx used to sit at +$106/+$108/+$10A - inside it.  Three
    savestates showed Marks[2..4] holding exactly those variables' values.
  2 Generated binaries match a fresh generation.  Editing a generator without
    re-running it ships stale data that assembles perfectly.
  3 Table addresses are symbols, not literals.  Trusting script offsets put
    the name-range floor past the whole group, and every name drew fixed.
  4 Pool tiles disjoint from the glyphs chrome draws from.  The pool sits on
    top of the same bank; an overlap corrupts letters rather than erroring.
  5 The no-sweep remap entry saves the registers restored by its shared exit.
    Calling an internal label below that save consumed 52 bytes of the
    caller's stack and hard-locked START before the new-game handler ran.
"""
import os, re, subprocess, sys, tempfile

CONSTANTS = "ps4disasm/ps4.constants.asm"
VWF = "ps4disasm/vwf"
LISTING = "ps4disasm/ps4.lst"
ROM = "ps4disasm/ps4built.bin"
fails = []


def check(name, ok, detail=""):
    print("  %-46s %s" % (name, "ok" if ok else "FAIL"))
    if not ok:
        fails.append((name, detail))
        if detail:
            print("      %s" % detail)


src = open(CONSTANTS, encoding="utf-8", errors="replace").read()
num = lambda n: int(re.search(r"^%s\s*=\s*(\d+)" % re.escape(n), src, re.M).group(1))
SLOTS, DEPTH = num("VWFMENU_SLOTS"), num("VWFMENU_DEPTH")
BASE_SLOTS = num("VWFMENU_BASE_SLOTS")
SAVEN = num("VWFMENU_SAVEN")
SAVERECSZ = num("VWFMENU_SAVERECSZ")
BUCKETS = num("VWFMENU_BUCKETS")
opts = open("ps4disasm/ps4.options.asm", encoding="utf-8", errors="replace").read()
STRIPS = int(re.search(r"^vwf_menu_strips\s*=\s*(\d+)", opts, re.M).group(1))
check("composed save ledger covers the entire pool",
      STRIPS or SAVEN >= SLOTS,
      "%d records for %d slots" % (SAVEN, SLOTS))

# 1 -- RAM map --------------------------------------------------------
# Offsets are PARSED, never restated here.  A hardcoded copy of the layout
# validates itself rather than the build - the first version of this file did
# exactly that and missed a field moved back on top of Marks.  Only the SIZES
# live here, because the assembler has no way to express them.
SIZES = {"VWF_Scratch": 84, "VWF_Tiles": 32,
         "VWFDia_DirtyCell": 2, "VWFDia_DirtyLine": 2, "VWFDia_DirtySpan": 2,
         "VWFMenu_PoolTop": 2, "VWFMenu_Marks": DEPTH * 2, "VWFMenu_Peak": 2,
         "VWFMenu_Mark_Cur": 2, "VWFMenu_RemapIdx": 2,
         "VWFMenu_Keys": BASE_SLOTS * 8, "VWFMenu_Refs": BASE_SLOTS,
          "VWFMenu_StripNext": BASE_SLOTS,
         "VWFMenu_Scratch": 8 * 32 + 8, "VWFMenu_SaveTop": 2,
         "VWFMenu_SaveMark": DEPTH * 2,
         # records >= BASE_SLOTS live in VWFMenu_SaveStackX, outside the base
         "VWFMenu_SaveStack": min(SAVEN, BASE_SLOTS) * SAVERECSZ,
         "VWFMenu_StripHit": 1,
         "VWFMenu_BattleBase": 2,
         "VWFMenu_BattleActionMark": 2, "VWFMenu_BattleEnemyMark": 2,
         "VWFMenu_BattleResultMark": 2, "VWFMenu_BattleResultActive": 1,
         "VWFMenu_ForceCompose": 1,
         "VWFMenu_FieldReuseDepth": 1, "VWFMenu_FieldReuseBlocked": 1,
         "VWFMenu_ReclaimInhibit": 1,
         "VWFMenu_SaveStripIdx": 2, "VWFMenu_SaveStripOff": 2,
         "VWFMenu_NameSrc": 4, "VWFMenu_NoPad": 1,
         "VWFMenu_BattleEffectMark": 2,
         "VWFMenu_DeferN": 1, "VWFMenu_DeferList": 8,
         "VWFMenu_SavePassBase": 2,
         "VWFMenu_TakeGen": 2, "VWFMenu_PartyCache": 11 * 16,
         "VWFMenu_PartyEntry": 4, "VWFMenu_SkipNames": 1,
         "VWFMenu_GlueEnd": 4, "VWFMenu_GlueKey": 8,
         "VWFMenu_GluePhase": 1, "VWFMenu_GlueSlot": 1,
         "VWFMenu_GlueCandidate": 1, "VWFMenu_GlueActive": 1,
         "VWFMenu_GlueDeref": 1, "VWFMenu_GlueFailed": 1,
         "VWFMenu_GlueOwned": 1, "VWFMenu_LayoutMagic": 4,
         "VWFMenu_BattleMacroMark": 2, "VWFMenu_BattleOptionsMark": 2}
if STRIPS:
    SIZES["VWFMenu_StripOf"] = SLOTS * 2
else:
    SIZES["VWFMenu_Bucket"] = BUCKETS
found = dict(re.findall(r"^(\w+)\s*=\s*VWF_RAM_Base\+\$([0-9A-Fa-f]+)", src, re.M))
found.setdefault("VWF_Scratch", "0")
missing = sorted(set(SIZES) - set(found))
check("every VWF RAM field parsed from the constants", not missing, ", ".join(missing))
fields = [(n, int(found[n], 16), SIZES[n]) for n in SIZES if n in found]
over = []
for i in range(len(fields)):
    for j in range(i + 1, len(fields)):
        a, ao, al = fields[i]
        b, bo, bl = fields[j]
        if ao < bo + bl and bo < ao + al:
            over.append("%s +$%03X..%03X vs %s +$%03X..%03X" % (a, ao, ao + al - 1, b, bo, bo + bl - 1))
top = max(o + l for _, o, l in fields)
check("RAM map has no overlapping fields", not over, "; ".join(over))
# The VWF block ends where the window tile backups begin: Window_Create
# seeds Win_Saved_Plane_Maps_End with #$6040, so VWF_RAM_Base+$C40 is the
# hard ceiling.  The old 4086-byte figure was 1078 bytes too generous and
# let a relayout run StripOf and the battle marks straight through the
# saved plane maps - windows then restored garbage and were never erased.
# $FFFF6000 == VWF_RAM_Base+$C00.  The game keeps its own $20-aligned
# buffers from there ($FFFF6020, $6060, $60A0, ... in ps4.asm), so that is
# the wall - NOT $6040, where Win_Saved_Plane_Maps_End merely starts.
# Overrunning it silently corrupts those buffers; the symptom was severe
# artifacting when paging back through the item list.
QUIET = 0xC00
_ps4 = open("ps4disasm/ps4.asm", encoding="utf-8", errors="replace").read()
check("the game still owns $FFFF6020 upward",
      "($FFFF6020).l" in _ps4,
      "the VWF ceiling sits below it")
check("RAM map fits below the game buffers at VWF+$C00",
      top <= QUIET, "needs $%X, ceiling $%X" % (top, QUIET))

# The 32 field-only tails are deliberately outside VWF_RAM_Base, in RAM that
# battle setup has vacated before Enemy_Stats/Fighter data is populated.  They
# must be exactly contiguous and end at $FFFF443F; widening the base arrays
# would instead collide with the saved-plane maps at $FFFF6000.
tail = {n: int(v, 16) for n, v in re.findall(
    r"^(VWFMenu_(?:KeysX|RefsX|NextX|SaveStackX))\s*=\s*ramaddr\(\$FFFF([0-9A-Fa-f]{4})\)",
    src, re.M)}
tail_expected = {"VWFMenu_KeysX": 0x4200, "VWFMenu_RefsX": 0x4300,
                 "VWFMenu_NextX": 0x4320, "VWFMenu_SaveStackX": 0x4340}
check("field pool extension has the requested RAM bases", tail == tail_expected,
      repr(tail))
check("field pool extension ends at $FFFF443F",
      tail.get("VWFMenu_SaveStackX", -1) + 32 * 8 - 1 == 0x443F,
      "$FFFF%04X" % (tail.get("VWFMenu_SaveStackX", 0) + 32 * 8 - 1))

# A ceiling is only as good as the reason for it.  Independently: no VWF field
# may share an address with anything ps4.asm names literally.  This is what
# would have caught the repack running onto the game's $FFFF6000 buffers, and
# it does not depend on knowing which buffer starts where.
_lits = {int(m, 16) & 0xFFFF
         for m in re.findall(r"\$(FFFF[0-9A-Fa-f]{4})", _ps4)}
_clash = sorted({0x5400 + a for _n, o, l in fields
                 for a in range(o, o + l) if (0x5400 + a) in _lits})
check("no VWF field collides with a literal address in ps4.asm",
      not _clash,
      " ".join("$FFFF%04X" % a for a in _clash[:6]))

# 2 -- generated data is current --------------------------------------
gen = {}
for f in ("menustrips.bin", "menustripidx.bin", "menustripbase.bin",
          "menustripmap.bin", "menunames.bin", "menunameidx.bin",
          "poolslot.bin", "pooltile.bin",
          "menufont.bin", "menuwidth.bin", "menualpha.bin",
          "fielditemnames.bin", "fieldtechnames.bin", "fieldskillnames.bin",
          "dialogueitemnames.bin"):
    p = os.path.join(VWF, f)
    gen[f] = open(p, "rb").read() if os.path.exists(p) else None
for tool in ("menuvwf.py", "fixwinfont.py", "fieldstrings.py",
             "menupool.py", "menustrip.py"):
    r = subprocess.run([sys.executable, os.path.join("tools", tool)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        check("%s regenerates cleanly" % tool, False, (r.stderr or r.stdout).strip()[:200])
stale = [f for f, old in gen.items()
         if old is not None and open(os.path.join(VWF, f), "rb").read() != old]
check("generated binaries match a fresh generation", not stale, ", ".join(stale))

# 3 -- ranges are symbolic --------------------------------------------
lits = [n for n in ("VWFMENU_NAMES_LO", "VWFMENU_NAMES_HI",
                    "VWFMENU_ENEMY_LO", "VWFMENU_ENEMY_HI")
        if re.search(r"^%s\s*=\s*\$[0-9A-Fa-f]" % n, src, re.M)]
check("name ranges resolve through symbols, not literals", not lits, ", ".join(lits))

# 4 -- pool disjoint from chrome glyphs -------------------------------
slot = open(os.path.join(VWF, "poolslot.bin"), "rb").read()
pool = {0x680 + int.from_bytes(slot[i:i + 2], "big")
        for i in range(0, len(slot), 2)}
required_font_reclaim = set(range(0x6C1, 0x6D3)) | {0x6D7} | set(range(0x6D8, 0x6E0)) | set(range(0x7F8, 0x800))
check("field pool reclaims the dead lowercase/Japanese tiles",
      required_font_reclaim <= pool,
      "missing " + " ".join("$%03X" % t for t in sorted(required_font_reclaim - pool)))
# $7EE/$7EF (dakuten/handakuten) and $7F4/$7F5 (kuten/touten) are the dead
# voicing marks menupool.py's EXTRA reclaimed long before this; the rest of
# $7DA-$7F7 is the two digit runs, $7F0-$7F3 and the continue arrow.
reserved_fixed = ({0x6D3, 0x6D4, 0x6D5} | set(range(0x7DA, 0x7F8))) - {0x7EE, 0x7EF, 0x7F4, 0x7F5}
check("field pool preserves punctuation, digits and UI glyphs",
      not (pool & reserved_fixed),
      " ".join("$%03X" % t for t in sorted(pool & reserved_fixed)))
check("pool size matches VWFMENU_SLOTS", len(slot) == SLOTS * 2,
      "poolslot.bin has %d bytes for %d slots" % (len(slot), SLOTS))
# A missed lookup site would read half an offset and point at the wrong tile -
# the same shape as the code-to-tile mapping that once lived in two routines
# and was only fixed in one.  Fail the build, not the playtest.
vwfm = open("ps4disasm/vwf/vwfmenu.asm", encoding="utf-8", errors="replace").read()
bad = [i for i, ln in enumerate(vwfm.splitlines())
       if "VWFMenu_SlotTile" in ln
       and "move.b" in "".join(vwfm.splitlines()[i:i + 4])]
check("no move.b reads VWFMenu_SlotTile", not bad,
      "lines %s" % [b + 1 for b in bad])
# moveq takes -128..127 and the assembler wrapped `moveq #VWFMENU_SLOTS` to
# -110 without a word when the pool grew to 146: the chain bound went
# negative on its first decrement, every hash lookup missed, and nothing
# shared a tile.  Resolve each moveq'd VWFMENU_ constant and range-check it.
_cv = {n: int(v) for n, v in re.findall(r"^(VWFMENU_\w+)\s*=\s*(\d+)", src, re.M)}
def _ev(expr):
    e = re.sub(r"VWFMENU_\w+", lambda m: str(_cv.get(m.group(0), 10**6)), expr)
    return eval(e, {"__builtins__": {}}) if re.fullmatch(r"[\d\s()+\-*/]+", e) else 10**6
_mq = [(i + 1, m.group(1)) for i, ln in enumerate(vwfm.splitlines())
       for m in [re.search(r"^\s*moveq\s+#([^,]+),", ln)] if m and "VWFMENU_" in m.group(1)]
_over = [(l, e) for l, e in _mq if not -128 <= _ev(e.strip()) <= 127]
check("every moveq of a VWFMENU_ constant fits in a byte", not _over,
      "; ".join("line %d: moveq #%s = %d" % (l, e, _ev(e.strip())) for l, e in _over))
check("TileSlot reach covers every pool tile",
      all(t - 0x680 < num("VWFMENU_TILESPAN") for t in pool),
      "VWFMENU_TILESPAN")

# 5 -- callable remap entries have balanced stack frames ---------------
listing = open(LISTING, encoding="utf-8", errors="replace").read()
m = re.search(r"/\s*([0-9A-F]{6}) :\s+VWFMenu_RemapRegion_NoSweep:", listing)
addr = int(m.group(1), 16) if m else None
rom = open(ROM, "rb").read()
save = b"\x48\xE7\xFF\xF8"       # movem.l d0-d7/a0-a4,-(sp)
no_sweep_tag = b"\x3F\x3C\x00\x01" # move.w #1,-(sp)
check("no-sweep remap entry saves its register frame",
      addr is not None and rom[addr:addr + len(no_sweep_tag)] == no_sweep_tag
      and rom[addr + len(no_sweep_tag):addr + len(no_sweep_tag) + len(save)] == save,
      "entry is missing its tag or d0-d7/a0-a4 save paired with the shared restore")

# NoSweep restores an animation frame before its saved cells can safely be
# reclaimed and remapped.  Keep automatic pressure recycling inhibited for
# the entire shared remap pass.  Its entry tag makes only NoSweep invocations
# decrement the nesting count at the shared exit, so a normal remap cannot
# unwind an outer NoSweep invocation.
vwf_src = open(os.path.join(VWF, "vwfmenu.asm"), encoding="utf-8",
               errors="replace").read()
no_sweep = re.search(r"VWFMenu_RemapRegion_NoSweep:(.*?)"
                     r"VWFMenu_RemapRegion_Ready:", vwf_src, re.S)
remap_exit = re.search(r"VWFMenu_RemapRegion_Ready:(.*?)"
                       r"VWFMenu_RemapCell:", vwf_src, re.S)
set_inhibit = no_sweep and re.search(
    r"addq\.b\s*#1,\s*\(VWFMenu_ReclaimInhibit\)\.l", no_sweep.group(1))
clear_inhibit = remap_exit and re.search(
    r"subq\.b\s*#1,\s*\(VWFMenu_ReclaimInhibit\)\.l", remap_exit.group(1))
normal_tag = re.search(r"VWFMenu_RemapRegion:\s*move\.w\s*#0,\s*-\(sp\)",
                       vwf_src)
no_sweep_entry_tag = no_sweep and re.search(r"move\.w\s*#1,\s*-\(sp\)",
                                             no_sweep.group(1))
check("no-sweep remap nests automatic-reclamation inhibition",
      bool(set_inhibit and clear_inhibit and normal_tag and no_sweep_entry_tag),
      "NoSweep must count ReclaimInhibit and use an entry tag at the shared exit")

# 6 -- ps4.asm code stays where native savestates expect it ----------
# Text that the generators grow (dialogue trees, string tables) sits between
# `align` directives; when a block outgrows its slack the align moves and
# every routine after it shifts (+20 bytes from three in-place fixes, then
# +$1000 from an 8-byte dialogue edit crossing $21A000) and states saved on
# the published build trap.  Pin the anchors that bracket each region.
ANCHORS = {"GameMode_LoadBattle": 0x6B34, "Window_Create": 0x68900,
           "loc_2AA43C": 0x2C2476, "loc_200000": 0x21A000,
           "Battle_SetupWindow": 0x297AF6, "loc_27DB92": 0x297B92,
           "Art_ChazField": 0x2A8000, "VWFMenu_Alloc": 0x311DBE}
_sym = {}
for _m in re.finditer(r"^\S*\s*\d+/\s*([0-9A-F]{4,6}) :\s+([A-Za-z_][A-Za-z0-9_]*):", listing, re.M):
    _sym.setdefault(_m.group(2), int(_m.group(1), 16))
_off = ["%s at %06X (pinned %06X)" % (n, _sym.get(n, 0), a) for n, a in ANCHORS.items() if _sym.get(n) != a]
check("code anchors are where the published build has them", not _off, "; ".join(_off))
_al = re.search(r"/\s*([0-9A-F]{6}) : \(MACRO\)\s+align \$1000", listing[listing.index("CreditTextHeaders:"):])
_end = int(_al.group(1), 16) if _al else 0
check("dialogue/examine/credits block ends at or below $21A000", 0 < _end <= 0x21A000,
      "ends at $%06X: %d bytes over" % (_end, _end - 0x21A000))

print()
if fails:
    print("%d invariant(s) FAILED" % len(fails))
    sys.exit(1)
print("all invariants hold")
