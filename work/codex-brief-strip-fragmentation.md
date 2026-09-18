# Brief: menu VWF tile pool fragments; long names silently fail to draw

Phantasy Star IV (Mega Drive) English translation, `ps4disasm` 68K source,
AS assembler via `tools/sourcebuild.py`. Assume no prior context.

## The bug

Rudy's Status > Skills page draws `Earth Bind` and then leaves the next two
rows nameless, while their `10/10`, `5/ 5`, `2/ 2` counts render fine. Counts
are fixed-width; names are proportional "strips". The same signature appears in
the shop Sell list on later pages with a large inventory.

Reproduce: Status > Rudy > Skills, with 7 Techs learned. A savestate sitting on
the failure is `work/rudy-skills.state` (BlastEm).

## The system, in one page

Menu text is drawn from a pool of VRAM tiles, `VWFMENU_SLOTS = 76`
(`ps4disasm/ps4.constants.asm`). Two kinds of text share it:

* **composed** text allocates per glyph-cell and DEDUPES by tile;
* **strips** (name-table entries: item, tech, skill, enemy, combo, guild names)
  allocate a contiguous RUN of cells and do not dedupe.

`VWFMenu_DrawString` picks the path by SOURCE ADDRESS - `VWFMENU_NAMES_LO..HI`
and friends select strips, everything else composes or takes the fixed-width
label path.

Slot -> VRAM tile goes through `VWFMenu_SlotTile` (`vwf/poolslot.bin`), whose
own comment is "the pool is not contiguous". **VRAM scattering is already
handled.** The contiguity requirement is purely in slot-index space, because a
strip is recorded as head + count and both the upload loop
(`VWFMenu_StripEnsure_Tile`, walking `d7` up from the head) and the plane write
step `head + i`.

`VWFMenu_Sweep` clears all Refs and re-derives liveness ONLY from
`Plane_A_Buffer`. It then pins whole strip runs: if any one cell of a strip is
still visible, the entire run is marked live. Its comment explains why - a
partly covered name can leave a single cell on the plane, and a half-pinned run
would let a later allocation replace an interior cell while `StripEnsure` still
trusted the surviving head. This pinning is correct and should not be removed
casually.

Reclamation is gated by `VWFMenu_FieldReclaimAllowed` (field mode `$C`,
non-zero `FieldReuseDepth`, zero `FieldReuseBlocked`, zero `ReclaimInhibit`).
**Battle must never sweep and never take `StripReuseOK`** - it keeps none of the
saved-region bookkeeping, and two earlier attempts to let it corrupted the
battle windows. The gate is what keeps battle out; leave it in force.

## The measurement that matters

From `work/rudy-skills.state` via `tools/poolpeak.py`:

    PoolTop 71 of 76, peak SATURATED at 76
    reclaim gate: ALLOWED (mode $C, depth 14, blocked 0, inhibit 0)
    window marks: 0 0 16 16 16 16 16 16 16 37 37 64 71 71 0 0

Marks are PoolTop sampled at each window's creation, so the deltas are what
each layer allocated: baseline 16, windows 2-8 +21 -> 37, Tech list +27 -> 64
(matching `menustrip.compose` over Rudy's 7 tech names exactly), Skill list +7
-> 71, then the ceiling.

Refs, read straight out of the same state:

    refs below PoolTop:
      ...#########....#########################....###...########.....#######
    dead runs, longest first: [5, 4, 4, 3, 3]
    free:   19 dead below PoolTop + 5 above = 24 cells
    needed: Sword Cross 8 + Air Slash 6     = 14 cells
    distinct pool tiles actually visible on the plane: 18
    slots marked live in Refs:                         52

**Capacity is not the binding constraint. Contiguity is.** There is 24 free
against 14 needed, but the longest run is 5 and `VWFMenu_StripEnsure_Free`
searches for `d5` CONSECUTIVE dead slots.

The amplifier is pinning: 18 visible cells hold 52 slots live, because the
windows beneath Skills are each only partially covered, so each contributes one
visible cell and pins a whole run, scattering the free space.

## What has been tried and DISPROVEN

Do not re-attempt these; each was disproven by measurement, not argument.

1. **Trim the baseline / free the covered Tech window as a unit.** Aimed at
   total capacity, which is not the constraint.
2. **`VWFMenu_Compact`: walk PoolTop back over the trailing dead run at
   `VWFMenu_Mark`.** Telemetry: `0 runs, 0 cells, gap 27, stopped by a live
   slot 4 times`. The 27-cell opportunity exists, but the walk is blocked
   immediately because the covered window is still on the plane.
3. **Same walk moved after `Window_Draw`.** Identical numbers. Field windows
   ANIMATE open (`loc_6881E` grows the frame over several frames - it is why
   `VWFMenu_RemapRegion_NoSweep` exists), so `Window_Draw` paints only the
   first step and at NO point inside `Window_Create` is the window beneath
   actually covered. Any compaction hooked in `Window_Create` is dead on
   arrival.

The live telemetry is in RAM at `VWF_RAM_Base+$130..$13B`
(`CompactRuns/Cells/Deny/Floor/Gap/Blkd`), printed by `poolpeak.py`. It is what
disproved (2) and (3) and is worth keeping until this is settled.

## The two remaining options

**(b) Make strips scatter-tolerant.** Record a per-cell slot list instead of
head + count, so the 24 free cells become usable however they lie. This is the
only option that addresses the measured constraint. It touches `StripOf`,
`StripIdx`, `Sweep`'s run pinning and `RemapRegion`. Note the VRAM side already
scatters via `SlotTile`, so the change is bookkeeping plus the two `head + i`
walks, not a VRAM redesign.

**(c) Cut demand.** Draw the status-screen Tech list fixed-width: frees 27
cells and removes 7 strips from the pinning pool. Cheap and certain, loses VWF
on that list, and leaves the same failure waiting as Rudy learns more Techs.

Question for Codex: is (b) implementable without weakening `Sweep`'s
whole-run pinning invariant, and what is the minimal representation change?

## Ground rules

* Battle is OFF LIMITS for sweep/reuse. Keep `VWFMenu_FieldReclaimAllowed`.
* Do not claim an emulator symptom fixed from static or harness evidence alone.
* `tools/sourcebuild.py` runs `checkbuild.py` BEFORE `build.bat`, validating the
  PREVIOUS build's `ps4built.bin` against `ps4.lst`. An interrupted build leaves
  those inconsistent and later runs fail inside checkbuild with a misleading
  invariant error. Recovery: copy `ps4built.prev.bin` over `ps4built.bin`,
  assemble once via Python `subprocess` (`cmd /c build.bat` from a bash shell
  only prints the banner and does nothing), then run `sourcebuild.py`.
* Tests must be able to fail. Three in this tree once could not; every new
  check here is mutation-tested.

## Tooling

* `tools/blastem_ram.py` - extracts the 64K work RAM from BlastEm's native
  `BLSTSZ` savestate (no section table; the base is found by matching RAM
  windows the game copies from ROM against a known-readable Exodus state).
  Output is byte-identical to what Exodus exposes.
* `tools/poolpeak.py` - reads either format; prints PoolTop, peak, saturation,
  the reclaim gate, compaction telemetry and per-window marks.
* `tools/test_compact.py`, `tools/test_battle_text_lifetime.py` - structural and
  savestate-backed checks.
* `tools/menustrip.py` - `compose(text)` returns `(cells, span)`; use `[0]` for
  the cell count.

## Current state

Build `A1A579408CDF6B613E795896361C15A89B84E46D96031FEE634FFBE7E988B0EF`,
12 test files pass. Battle-side work is DONE and verified in play: item-list
page rebuild (`Battle_ItemPageRender`) and the Tech page-arrow offset. The
`VWFMenu_Compact` code is inert in effect but sweeps on every window create; if
neither option is pursued it should be backed out rather than left in place.
