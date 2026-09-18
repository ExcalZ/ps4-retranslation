# Question: should item names move from prerendered strips to per-cell composition?

Phantasy Star IV JP->EN translation, `C:\Users\Mark\Claude Projects\ps4-translate`.
Assume no prior context. This is an assessment-and-possibly-implement task on
the MENU VWF tile pool. `work/handoff-vwf-pool.md` has the full history; this
file is the self-contained version of what matters now.

## The system, in brief

Menu text is drawn from a pool of VRAM tiles, `VWFMENU_SLOTS = 88`
(`ps4disasm/ps4.constants.asm`). Two kinds of text share it:

  * **composed** text (`VWFMenu_DrawString_Compose` -> `VWFMenu_Alloc`):
    allocates one slot per 8px glyph-cell, keyed by the cell's 8-byte bitmap,
    and DEDUPES - a cell whose bitmap already has a slot reuses it.
  * **strips** (`VWFMenu_DrawStrip` -> `VWFMenu_StripEnsure`): name-table
    entries - item, tech, skill, enemy, combo, guild names - drawn from
    PRERENDERED tile art (`tools/menustrip.py` bakes it), one slot per cell,
    chained per name via `VWFMenu_StripNext` (a scatter-tolerant rewrite done
    by another session). Strips do NOT dedupe, neither within a name nor
    across names.

`VWFMenu_DrawString` picks the path by SOURCE ADDRESS: text inside
`VWFMENU_NAMES_LO..HI` (and the enemy/combo/guild ranges) goes to strips;
everything else composes or takes a fixed-width label path.

Liveness: `VWFMenu_Sweep` clears all refcounts and re-derives them from
`Plane_A_Buffer`, then pins every strip whose ANY cell is still visible - the
whole run, because a partly covered name must not have an interior cell
recycled from under it.

Battle (`Game_Mode_Index = $14`) MUST NOT sweep or reuse.
`VWFMenu_FieldReclaimAllowed` gates every reclaim path on field mode; two
earlier attempts to relax that corrupted battle windows. Leave it in force
whatever you change.

## Why the question is open now

The pool is at its ceiling with no tiles left. The window bank is full; the
`$7C0` second font bank was surveyed tile by tile and only four Japanese
punctuation tiles were genuinely free (`$7EE $7EF $7F4 $7F5` - dakuten,
handakuten, kuten, touten). `$7EC`/`$7ED` looked free by every textual test and
turned out to be the small 8 and 9 used for HP/TP; taking them corrupted the
status panel. Do not re-survey for tiles - that road is closed and documented
in `tools/menupool.py`.

So capacity is fixed at 88 and demand has to fit inside it.

## The measured failure that motivates this

Equip screen, field. The player equipped an item and the equipped-slot name
half-painted. Savestate read: `live now 65, peak 92, VRAM holds 88` - the
redraw transiently needs 92 and settles to 65. Traced: the path destroys and
recreates its windows correctly (`VWFMenu_Release` runs, marks roll back), so
there are no stale cells. It is genuine demand: window 8 opened at PoolTop 69
and needed 23 cells with 19 available.

The list on that screen had `Laser Barrier` TWICE:

    equip list as strips           40 cells
    with duplicate names shared    32 cells   -> saves 8

Eight cells against a four-cell shortfall, from one duplicate. Duplicate stacks
are ordinary - two Ceramic Mails on another page. Strips pay full price for
every copy. Renaming cannot fix this: no long name is involved.

Measured on ordinary item pages too, for shared PREFIXES (Titanium, Ceramic,
Graphite, Laconia, Guardian):

    page 2   66 cells -> 55 unique   (saves 11)
    page 3   57 cells -> 49 unique   (saves  8)

Measure with `tools/menustrip.py`: `compose(text)` returns `(cells, span)`;
`span[y*16 + t]` is row y of cell t, so a cell's bitmap is
`bytes(span[y*16+t] for y in range(8))`.

## What switching would buy and cost

Buy:
  * dedup across identical AND prefix-sharing names - the only lever that
    addresses duplicates at all, and it improves as names cluster;
  * no whole-run pinning - the fragmentation amplifier (18 visible cells once
    held 52 slots live);
  * deletion of `StripOf`/`StripNext`/`StripIdx`/`StripEnsure` and the strip
    halves of `Sweep`, `SaveRegion`, `RemapRegion`;
  * probably no item renaming needed at all.

Cost:
  * strips are PRERENDERED - that is their stated reason in the source. Names
    would compose per cell at runtime, with a dedup search per cell. Battle
    redraws these lists often; frame cost is UNMEASURED, and frame loss has been
    seen once this project from an unrelated change;
  * every path that has misfired in this area is in scope;
  * the switch is a build flag, `vwf_menu_strips` (`ps4disasm/ps4.options.asm`),
    with the compose path still wired at the main branch - BUT there are 32
    guards and most have no `else`. `=0` today silently drops
    `Battle_ItemPageRender` (a verified battle fix) and re-enables three dead
    Japanese voicing comparisons while `tools/menupool.py` keeps `$6EF-$6F2` in
    the pool regardless of the flag. `=0` is a stale fallback, not a working
    configuration.

## The decisive unknown

Per-cell composition for names was TRIED and ABANDONED before strips were
introduced, and the reason is not recorded anywhere in the tree. Find it before
anything else - a git log if one exists, comments near `VWFMenu_DrawStrip`,
`work/*.md`, and the older experiment ROMs `work/ps4us_vwfmenu_*.bin` whose
names read like a sequence of attempts. Overriding a decision whose rationale
cannot be reconstructed is precisely how this project lost a day to the `$6D9`
tiles.

## Recommended shape of the work

1. Recover the reason per-cell was abandoned. If it was frame cost, measure it;
   if it was a correctness failure, check whether the scatter-tolerant chain
   and the field reclaim gate (both later additions) already address it.
2. Make `vwf_menu_strips=0` a REAL configuration: write the missing `else`
   branches, make `menupool.py`'s `$6EF-$6F2` inclusion conditional on the
   flag, keep `Battle_ItemPageRender` (or an equivalent) under both.
3. Build `=0` and MEASURE, not judge: `tools/poolpeak.py <savestate>` reads
   PoolTop, peak, and per-window marks from a BlastEm `.state` or Exodus
   `.exs`. Compare the same savestates under both builds. The equip screen and
   `work/rudy-skills.state` are the reference cases.
4. Only then decide. A measurement costs a few hours; a wrong switch costs the
   kind of week this project has already had.

## Tooling

  * `tools/blastem_ram.py` - 64K work RAM out of a BlastEm native `.state`
  * `tools/poolpeak.py` - pool state from a savestate, either emulator format
  * `tools/menupool.py` - generates `poolslot.bin`/`pooltile.bin`; asserts the
    tile safety rules learned the hard way; do not loosen them
  * `tools/checkbuild.py` - static invariants; run after any RAM or pool change
  * `tools/test_strip.py`, `tools/test_itemtext.py`,
    `tools/test_battle_text_lifetime.py` - harness tests over the strip and
    lifetime paths; tests derive RAM offsets from the constants, never hardcode
  * `tools/poolreplay.py` - cost a savestate's screen, or a scripted
    transient, through the BUILT rom's name path; `tools/namecost.py` -
    instructions per name; `tools/buildflags.py` - which way the built rom
    was configured.  `PS4_ROM`/`PS4_LST` point them at another build.
  * `work/equip-overflow.state` (BlastEm slot_5, the equip case) and
    `work/status-saturated.state` (slot_2, status Item page 2) - reference
    states, captured on the 92-slot build (see Outcome)

## Build and verify

    python tools/sourcebuild.py          # regenerates, assembles, writes ps4en.bin
    for t in tools/test_*.py: python $t  # 11 files, all must pass
    python tools/checkbuild.py

Baseline: `77BE3D8666485BDFA3F85A9BE31C4695ED3DF0D42A08C780405AB6CA6A654BE2`,
11/11 tests, invariants clean.

Traps, all verified:
  * `sourcebuild.py` runs `checkbuild.py` BEFORE `build.bat`, validating the
    PREVIOUS `ps4built.bin` against `ps4.lst`. After an interrupted build:
    copy `ps4disasm/ps4built.prev.bin` over `ps4built.bin`, assemble once via
    Python `subprocess` (`cmd /c build.bat` from bash only prints the banner),
    then run `sourcebuild.py`.
  * VWF RAM must stay below `VWF_RAM_Base+$C00` (`$FFFF6000`); the game's own
    buffers start there. checkbuild has two independent guards for it.
  * A mutation test that restores with `mv` can leave a stale `__pycache__`;
    `rm -rf tools/__pycache__` after any such restore.
  * `script/dialogue N.asm` is regenerated by `treeport.py` - irrelevant to
    this task, but do not be surprised if those files change under you.

## Ground rule

Do not claim an emulator symptom fixed from static or harness evidence alone.
The player tests on BlastEm. For this task specifically, "fixed" means the
equip screen paints fully with a duplicate item in the list, AND battle lists
show no frame loss - both by eye.

# Outcome (2026-09-10): rationale recovered, `=0` made real, measured

Steps 1-3 of the recommended sequence are done.  Step 4 - the decision - is
the player's, by eye, and the build to test is `work/ps4en_compose.bin`
(SHA-256 `4BECF96A942BEC3E833E9470B93433310D0C1D516D8905D86F58073C86220437`).
The shipping build is untouched: `ps4en.bin` is still `77BE3D86...`,
byte-identical, 11/11 tests, invariants clean.

## 1. Why per-cell was abandoned - it IS recorded, just not in the tree

The 2026-08-29 Claude session that introduced strips was imported into the
Codex history and is readable at

    ~/.codex/sessions/2026/08/30/rollout-2026-08-30T16-41-49-01a0550c-fe15-7320-bf0b-e6195992f54d.jsonl

(`agent_message`/`user_message` payloads; grep for `prerender`).  What it
says, in order:

  * The player was seeing three things on the per-cell build: **tile
    corruption** ("pool tiles pointing at reclaimed slots", frame and sprite
    art bleeding through, artifacts when closing windows), a **slowdown**
    ("does not impact movement on the map, only areas where text is present",
    "at the end of the first battle"), and **stray digits** - the uses/HP
    numerals drawn relative to `a1` landing in the wrong place.
  * The player asked whether prerendered strings would help.  The assistant's
    answer, verbatim in substance: "**prerendering does not reduce VRAM** ...
    you *lose* the content dedup the pool currently gets ... On peak VRAM
    alone, prerendering is slightly worse."  The case for strips was
    ownership: a strip belongs to one window, so the allocator, the sweep and
    the SaveRegion/RemapRegion layer - "precisely where the corruption lives"
    - could be **deleted** and allocation become a plain LIFO.  Second, one
    DMA per strip instead of ~16 data-port writes per tile, "aimed straight
    at the slowdown".
  * The stray digits were diagnosed separately as an `a1`-advance mismatch
    and fixed by **padding each name to its stock character count**.  That
    fix is independent of strips; the compose path simply never had it.

So per-cell composition was not found defective as a renderer.  It was
replaced on the hypothesis that strips would let the shared-ownership layer
be deleted.  **That deletion never happened**: the pool, sweep and remap
stayed "as the fallback for enemy names", and strips then grew their own
reuse/validate/chain bookkeeping (`StripOf`, `StripNext`, `StripEnsure`,
`StripValidate`, the strip halves of `Sweep`/`SaveRegion`/`RemapCell`)
inside the very layer they were meant to remove.  Nor did the DMA happen:
`VWFMenu_StripEnsure_Tile` writes each tile through the data port, eight
longs at a time.  The dedup loss was the acknowledged price of a benefit
that was not collected.

The corruption the player saw has since been addressed on its own terms
(plane-derived sweep, `VWFMenu_FieldReclaimAllowed`, `Release`, the
scatter-tolerant chain) and the slowdown mechanism - a full-pool sweep on
every draw - is gated to the field and is the same code under both settings.

Two corrections to this brief's own numbers, both from the code:

  * **Strips already share identical resident names.**  `StripEnsure_Find`
    looks the index up below PoolTop and reuses the chain.  Measured on the
    strip build: `Laser Barrier` drawn twice costs 8 then 0 cells
    (`tools/namecost.py --top 60 "Laser Barrier" "Laser Barrier"`).  The
    "40 -> 32, saves 8" arithmetic above is wrong; the duplicate was never
    the cost.
  * **"Peak 92 vs 88" mixes two builds.**  The equip savestates
    (`work/equip-overflow.state` = BlastEm `slot_5`) were captured on the
    92-slot build - the marks reach 92 - and `poolpeak.py` reports the
    current constant.  On that build the screen saturated at 92; on this one
    it saturates at 88.  True demand is "at least 92", not "92".

## 2. `vwf_menu_strips=0` was never a configuration, for a reason not listed

Beyond the missing `else` branches: **the five name tables in ROM still hold
the US text** (`InventoryNames` starts `DAGGER, HUNT-KNIFE, ...`;
`TechniqueNames` `FOI, GIFOI, ...`).  Strips deliver the translation by
INDEX and never read the table text; the game keeps walking the US bytes
for terminators and laying out against their character counts.  Composing
"the name" under `=0` would have drawn the US abbreviations.

What `=0` now is (all new code under `if vwf_menu_strips=0`/`else`, so the
`=1` build did not move a byte):

  * `tools/menustrip.py` also emits `menunames.bin` (the translated names in
    the menu charset, `$FE`-terminated) and `menunameidx.bin` (word offset
    per strip index).  Same `code` map and width table the strips were
    rendered from, so the composed cells are the strip's own cells - the
    test compares the composer's 1bpp keys against `menustrip.compose`.
  * `VWFMenu_DrawName` (vwfmenu.asm): entry address -> index through the
    shared `VWFMenu_StripMap`, compose the translated text, then in
    `DrawString_Done` pad to the stock character count and put `a0` back on
    the stock terminator - the same `a1`/`a0` contract as `DrawStrip`.
    `VWFMenu_NameSrc` (RAM long, +$ABA) carries the stock entry across the
    compose loop.
  * `VWFMenu_StripCells` has an `=0` body that measures the translated text;
    all 54 place-name banners agree with the strip table.
  * `VWFMenu_FieldReclaimAllowed` moved outside the strips guard (the
    compose path gates its sweep on it under both settings).
  * The 14 battle pool-bookkeeping sites (`BattleBase` capture/rewinds,
    `Battle_ItemPageRender`) and the location-banner sizing are now under
    `if vwf_menu=1` - they never depended on strips.  So is the retirement
    of the three Japanese voicing comparisons (`$6F1`/`$6F2`/`loc_27DC1E`),
    which closes the LATENT TRAP noted in `work/handoff-vwf-pool.md`:
    `menupool.py`'s `$6EF-$6F2` inclusion is now correct under both flags.
  * `tools/disasmport.py`, `sourcebuild.py` (either setting builds; it says
    which), `checkbuild.py` (new RAM field, new generated files),
    `emu68k.py` (six opcodes the new path needed, each caught by a trap),
    and the tests: `tools/buildflags.py` reads the built listing, strip-only
    checks skip on the composed build with a printed reason, and
    `test_strip.py` gains composed-only checks (keys identical to the strip
    art; a name drawn twice costs 0; `Leather Cloth`+`Leather Helm` share 4
    cells).  Both builds pass 11/11 and `checkbuild`.

`work/ps4en_compose.lst` is the `=0` listing; `PS4_ROM`/`PS4_LST` point the
harness tools at it without reassembling.

## 3. Measured, in the harness, same savestate under both builds

`tools/poolreplay.py` keeps a savestate's composed baseline (party names,
labels) and redraws the screen's names through the built rom's real
`VWFMenu_DrawString`, no sweep allowed.  `tools/namecost.py` counts
instructions per name.

Settled screens (slots used, of 88):

    screen                                       strips   composed
    equip (equip-overflow.state)                    60        57
    status Item page 2 (status-saturated.state)     82        71
    Item page (BlastEm slot_1)                      73        67

The equip transient as the marks recorded it - PoolTop 69 with four dead
cells at 22-25, window 8 drawing Wood Cane, Graphite Shield, Laser Barrier:

    strips    Wood Cane +6 -> 75, Graphite Shield +9 -> 84,
              Laser Barrier: 0 of 8 cells drawn (needs 8 above PoolTop or
              8 dead below; there are 4 and 4)                   -> FAILS
    composed  Wood Cane +2 -> 71 (four dead cells taken per cell),
              Graphite Shield +9 -> 80, Laser Barrier +8 -> 88   -> fits, 0 spare

    python tools/poolreplay.py work/equip-overflow.state --top 69 --dead 22-25 \
        --draw "Wood Cane,Graphite Shield,Laser Barrier,Laser Barrier"

So the mechanism that rescues the equip screen is not dedup of the
duplicate.  It is that the composer allocates PER CELL and takes dead slots
below PoolTop without a sweep, whereas a strip must land whole - entirely
above PoolTop, or entirely in dead slots gathered by a permitted sweep.
Prefix sharing is the second, smaller effect here (`Psi Ring`/`Psi Robe`:
3 cells); it is the larger effect on Item pages (11 cells on page 2).

CPU, instructions through `VWFMenu_DrawString` (harness counts, not cycles):

    name, pool at 60 cells       strips first/redraw   composed first/redraw
    Graphite Shield (9 cells)        1166 /  765           9781 / 5677
    Dagger (4 cells)                  803 /  622           4716 / 2762
    Laser Barrier (8 cells)          1094 /  737           8654 / 5026
    empty pool, Graphite Shield       863 /  465           3841 / 2437

Composed is 5-8x the instructions, and it grows with occupancy: the
content search compares every cell against every key below PoolTop (about
50 cycles per slot per cell).  At roughly 8-10 cycles an instruction that is
of the order of 0.6-0.8 of a frame per long name with a 60-cell pool, so an
8-row Item page costs a few frames on open or page-flip, and a 4-row battle
page about half that per keypress.  That is an ESTIMATE from instruction
counts; the ground rule stands - frame loss is judged by eye.  If it shows,
the lever is the search, not the composer: a first-byte bucket over the keys
would cut the dominant term several-fold before any decision to abandon.

## 4. What the player's test should cover, on `work/ps4en_compose.bin`

  1. The equip screen with a duplicate item in the list (the `slot_5` case):
     every name paints fully.
  2. Battle: Item, Tech and Skill pages, page-flipping, several turns - any
     visible hitch or frame drop on open or flip.
  3. Status > Skills (Rudy with 7 Techs) and the shop Sell list on a late
     page - the earlier strip-fragmentation cases; no blank rows.
  4. Field Item pages 2-3 (Titanium/Ceramic/Graphite clusters) flipping back
     and forth - no artifacts on the revealed rows.

The harness says composition fits every measured screen with margin where
strips saturate, at a CPU cost that only the emulator can weigh.  If 2 is
clean, switching is the only lever that scales with the name set and the
recommendation is to switch (flip `vwf_menu_strips` to 0; `=1` stays
buildable as the fallback).  If 2 shows loss, optimise the key search and
retest before concluding "don't switch".

# Playtest round 1 (2026-09-10): equip-panel artifact traced and fixed

Reported on `4BECF96A`: the equipped-items panel read `P:Force Cand` after
equipping, some framerate drop after scrolling many menus, a couple of frames
of party-name artifacting on battle item-page swaps; field Item and Status
pages clean.  Savestate: `work/compose-slot0.state` (BlastEm ps4en_compose
slot_0; slot_1, saved later, is the map with the menu closed).

## What the state shows

`tools/poolcells.py` (new: labels every slot by the name cell its key
spells, then reads each plane row as a name and flags cells whose slot holds
something else):

    row 14 col 19  panel weapon row:  [Ps][Force Cane 0..5][d]
    row 14 col 36  list Force Cane:   slots 54-60, intact

The panel's cells 20-25 point at the LIST's slots 54-59, shifted one cell;
19 and 26 point at slots that now hold other names.  (`/2-HAND` is stock:
tile `$6F7` sits at x+3 on that row in the strip build too.)

## The mechanism, reproduced in the harness (`tools/test_shared_cells.py`)

Composed cells are allocated by content, so when the panel (outer window)
redraws its weapon row while the list (inner window) still shows the same
name, every panel cell hits the list's slots.  The list is then destroyed
and rebuilt: `Release` rolls PoolTop back to the list's mark and cleared the
refcounts above it, the rebuilt list allocates from the mark in whatever
order it now draws, and the panel's cells show what landed there.  The
strip build has the same structure but `StripEnsure_Find` re-finds a name
by INDEX, so a LIFO rebuild re-lands the same chain and the stale references
stay valid by luck - the harness shows it breaking there too once the list
is rebuilt in another order or scrolled.

## The fix (composed build only; `=1` bytes unchanged)

`VWFMenu_Alloc`, field mode only:
  * the dedup scan covers the whole key table, not just below PoolTop - a
    key above the frontier still has its tile (only Take rewrites either;
    `Reset` now clears keys and counts), so a rebuilt list re-finds the
    very slots the panel points at;
  * growth skips slots the last sweep marked live instead of overwriting
    them.
`VWFMenu_Release` no longer clears counts blind: `Window_Destroy` sweeps the
plane right after the restore, and that sweep is the truth.  Battle keeps
its plain bump (no sweeps there, counts never cleared).

Reproduction: panel drawn, list drawn, panel redrawn sharing the list's
slots, list released and rebuilt reversed / scrolled to other names.  Before:
the weapon row corrupts on both rebuilds.  After: intact on both, and the
reversed rebuild costs 0 new cells (every key re-found).  12/12 tests on
both builds, invariants hold, pool numbers unchanged (57/71/88).

Build to retest: `work/ps4en_compose.bin`
`F9310E097956EE35F712B95E022B81BA750BFE7055BBE094C1DA71134E0A1244`.

## Still open

  * Battle party-name flicker on page swap: not diagnosed - a savestate
    taken right after a swap (even a clean one) is needed.  The candidate is
    the same sharing in the other direction: the page rewind
    (`Battle_ItemPageRender`) frees slots that HUD cells share; the HUD's
    next redraw heals it, which matches "a couple of frames".
  * Framerate after heavy scrolling: consistent with the composer's per-cell
    search (`tools/namecost.py --top 60`: ~10k instructions per 9-cell name
    at 60 occupancy).  The lever if it matters is a first-byte index over the
    keys; not attempted.
  * `poolpeak.py`'s "live now" is PoolTop; on the composed build live cells
    can sit above it after a Release, so read `poolcells.py` instead.

Note: another session is editing this tree concurrently (`ps4.asm`,
`handoff-vwf-pool.md`, `ps4en.bin` changed at 17:30).  `ps4en.bin` is now
`0D447A2D...` from that session's edits; the `=1` configuration built here
from the same tree matches it byte for byte, so the strips build is still
unaffected by any of this work.

# Playtest round 2 (2026-09-10): the appended tile

Reported on `F9310E09`: an extra glyph tile after Ceramic Shield, Ceramic
Mail, Ceramic Knife, Laser Sword, Shadowblade, and after Resta, Barta,
Eliminate, Zan, Gifoie, Sword Cross, Air Slash; VRAM showed the offending
tile holding a large numeral 4.  States: `work/compose2-slot3.state`
(equip list) and `compose2-slot4.state` (tech list).

Every affected name is one whose ink ends on a cell boundary, so its last
cell composes to all zeroes (`menustrip.compose`: the 1px gap after the
final glyph spills into a new cell).  `poolcells.py` showed all of them
sharing one slot whose key is all zeroes and whose refcount was 5.  That
was a hit, not an upload: round 1 widened the dedup scan to the whole key
table, and a never-uploaded slot's key is ALSO all zeroes, so the blank
cell "found" a slot that had never been written and displayed whatever
VRAM held there - the stale numeral.  The strip build bakes such cells as
paper tiles, so it never composed a zero key at all.

Fix, composed build only:
  * an ink-less cell gets the blank tile `$680` and no slot (the a1 advance
    is unchanged - it still counts as a cell);
  * `VWFMenu_Reset` fills the key table with all-ones, which no glyph cell
    composes to, instead of zeroes.
Side effect: a third of the names cost one slot fewer than their strip
(status Item page 2: 70 of 88, was 71).  `test_strip.py` checks a
blank-tailed name costs cells-1 slots with `$680` last; the other tests
and `poolreplay.py` now expect the blank tile there.  12/12 on both builds,
invariants hold, `=1` still byte-identical to `ps4en.bin`.

Build to retest: `work/ps4en_compose.bin`
`4B9D6395410368BB923853D09E70F0D2AE57B7239FACB69598BEA1A04D689DC4`.

# Playtest round 3 (2026-09-10): PlasmaDagger's two blank cells

`work/compose3-plasma.state`: PoolTop 88, marks all 0, thirty slots dead in
the refcounts.  The screen's settled demand is 71 (`poolreplay`), so this
was not capacity.  It was a consequence of round 1: hits revive slots above
PoolTop, so after a Release to a low mark the whole pool can be live above a
PoolTop of 0 - and the composer's pressure sweep fires on `PoolTop + cells >
cap`, which never triggered.  Growth walked every live slot to 88 and gave
up with dead cells waiting for a sweep nobody ran.

Fix: `VWFMenu_Alloc` sweeps once (field only) before reporting the pool
full, then rescans.  `test_shared_cells.py` covers it: 62 cells live above
a PoolTop of 19, half of them gone from the plane and unswept, and a new
name still draws in full.  `poolreplay.py` now wipes keys above its baseline
(the whole-table scan was re-finding the savestate's own keys).

Composed build to retest: `work/ps4en_compose.bin`
`F7681A95F3851BBE5CD9E4DD8FCB4949DA879C6D4EE833921A021D53818F1E2E`.

# Not the pool: "<name> does not know any field techniques!" overflowing

Both builds.  `Win_MacroMessage` copies the character name and then a blind
32 bytes of the message into `$FFFFE220`.  The reworded texts (message
wording batch 2, the other session) are 37 and 33 bytes with their
terminator, so the terminator was never copied and `LoadWindowTiles` read on
into stale RAM.  The copy now runs through the terminator (`if vwf_menu=1`);
`$FFFFE220` has room to `$FFFFE252`.  `ps4en.bin` is `47B72BE3...` with it.

Addendum (other session): the same blind copy exists at two more sites,
`Win_TechMessage` (`loc_60700`) and the field-skill window (`loc_61A54`),
whose tables have `loc_2AA84A` / `loc_2AAA06` at index 0 - the "no field
techniques / skills" case from the Tech and Skill menus.  Both now copy
through the terminator under `vwf_menu=1`, same bytes as the macro fix.
Strips build is `26583CE6...`; `work/ps4en_compose.bin` (`F7681A95...`)
predates this and would still garble those two windows if retested there.

Rebuilt: `work/ps4en_compose.bin` is now `AC77ECCC...`, from the same tree
as `26583CE6...`, so both builds carry all three copy fixes.  12/12 on the
composed build, invariants hold.  That is the composed build to retest.

# Decision (2026-09-14): composition ships

After the HUD cache, the item pre-render skip and the pressure-sweep rule
(work/STATUS.md, 2026-09-13), the player's verdict on the composed build was
"much better", and `vwf_menu_strips = 0` is now the default in
`ps4.options.asm`.  Strips remain buildable as the fallback.
