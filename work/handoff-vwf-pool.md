# Handoff: scoped menu VWF tile-pool reclaim

Phantasy Star IV (Mega Drive) JP->EN retranslation. Repo builds a ROM from a
68000 disassembly via `python tools/sourcebuild.py`.

## Resolution and playtest follow-up (2026-09-09)

The scoped field reclaim was necessary, but the 2026-09-09 playtest disproved
the claim that it had resolved every reported symptom. Three independent
faults remained:

* Hunter Knife and Claw LOOK text was complete in both the source and assembled
  ROM, but the forced proportional renderer could still exhaust the live pool
  across the two description rows and stop mid-sentence. Every translated
  static LOOK row fits the stock 28-cell field (the longest is 26), so
  `Win_ItemActionLook` now uses the original pool-free `LoadWindowTiles`
  renderer. Dynamic item notices remain proportional.
* Tech page 2 -> page 1 still corrupted because the first widening pass missed
  `loc_E8C`, the copy helper used only by `Battle_TechPrevWin`. It restored
  12 columns into the now-14-column Tech window. That helper now copies all 14.
* Double Slash and Illusion could disappear because battle submenu strip
  allocations survived after the submenu closed. The Tech, Skill, and Item
  selected/cancelled exits now return `VWFMenu_PoolTop` to the
  `VWFMenu_BattleBase` captured for that character's command window.
  Page-to-page transitions deliberately do not roll back: their private
  buffers still contain live raw tile IDs.
* A later report of Technique User displaying `Res` and a level-up displaying
  only `Technique has been mastered!` exposed a second battle lifetime leak.
  This was not a fallback to the stock `RES`: Technique User reads the full
  title-case `Resta` from `EnemySkillNames`. With two pool slots left, its
  four-cell composed run draws two cells and blanks the rest. The learned-Tech
  path uses the legacy table only as the ordinal key for a full translated
  strip; without the strip's four contiguous slots, its three stock field
  cells are all blank.
* Player action names, enemy action names, and the recurrent battle-results
  panel now each have a dedicated pool mark. Their teardown restores only the
  allocations made after that exact surface opened. The results panel uses an
  active flag so the first draw records a mark and every later draw releases
  the preceding panel before replacing it. These boundaries do not sweep and
  do not share `VWFMenu_BattleBase`.

The earlier field-side safeguards remain:

* `VWFMenu_DrawString_Composed` computes the actual cell count first. It sweeps
  only when `PoolTop + cells > VWFMENU_SLOTS` **and** `Game_Mode_Index == $C`,
  the field-window mode. Battle never invokes this sweep, even when drawing at
  `$FFFF8600` inside `Plane_A_Buffer`.
* `Win_ItemList` opens one short `VWFMenu_StripReuseOK` scope around its
  synchronous row loop and sweeps once after `Window_Create` has recorded the
  covered region. `VWFMenu_StripEnsure` may claim a contiguous dead run only in
  that scope.
* `VWFMenu_Sweep` treats every validated strip as indivisible: if any member is
  live on the plane, the whole run is live. `VWFMenu_StripEnsure` accepts an
  existing strip head only when the declared run is in bounds and every later
  slot is still a continuation.
* `VWFMenu_RemapRegion` refreshes field liveness and opens the same bounded
  reuse permission while restoring saved strip records. The no-sweep animation
  entry and all exits clear the flag; `VWFMenu_Reset` also clears it.

The important distinction for reclamation is whether the active window system
has save/remap bookkeeping. Field does; battle does not. Battle instead uses
explicit submenu, action-window, and results-panel lifetime boundaries.

## Symptoms covered

The original report was whole item names drawing **blank** in the camp Item
menu.

Repro (in game): go to the second page of the item list or later, open LOOK or
DSCD, cancel back, then cycle to page 1 and forward to page 2 again. Names
render as empty cells - the row and its checkbox are there, the text is not.

Blank versus truncated remains diagnostic. A truncated composed run exhausted
the pool part-way; a wholly blank name means the contiguous **strip** allocation
failed and `VWFMenu_DrawStrip` filled every cell with `$680`. Hunter Knife
and Claw LOOK were the composed-run case. Missing Double Slash/Illusion were
battle strip lifetime exhaustion. The page-2-to-page-1 corruption was a
separate window-width mismatch. Technique User's partial Resta and the blank
level-up insertion were later action/results lifetime exhaustion.

The latest playtest reported that item rows may still be blank for one or two
frames before populating normally. The persistent blank-row failure is no
longer reproduced, but this transient has not been diagnosed or claimed fixed.

## Why

Menu text is drawn two ways, both out of one 83-slot VRAM tile pool
(`VWFMENU_SLOTS`, tiles `$682-$6C0` plus 20 reclaimed frame tiles; see
`tools/menupool.py`):

* **composed** - `VWFMenu_DrawString_Compose` builds glyphs per cell and calls
  `VWFMenu_Alloc` for each. Alloc scans for a slot with `Refs == 0` before
  growing `VWFMenu_PoolTop`.
* **strips** - prerendered name art. `VWFMenu_StripEnsure` allocates a
  **contiguous run** of slots, because `VWFMenu_StripOf` records a run from its
  first slot.

Originally, `VWFMenu_StripEnsure_Grow` only ever grew:

    move.w  (VWFMenu_PoolTop).l, d4
    move.w  d4, d3
    add.w   d5, d3                  ; d5 = cells this strip needs
    cmpi.w  #VWFMENU_SLOTS, d3
    bhi.w   VWFMenu_StripEnsure_Full   ; -> -1, the whole name draws blank

It never reclaimed a freed slot and never swept. So once opening LOOK or DSCD
had grown the pool past what a page of strips needed, every later page failed.
Each page's tiles go stale the moment they leave the plane, but nothing
collects them.

`VWFMenu_Sweep` existed and could collect them - it recomputes `VWFMenu_Refs`
by scanning the plane - but the composer called it whenever the pool was
**completely** full, including in battle:

    cmpi.w  #VWFMENU_SLOTS, (VWFMenu_PoolTop).l
    bcs.s   VWFMenu_DrawString_NoSweep
    jsr     (VWFMenu_Sweep).l

## Why the obvious fixes break battle - READ THIS FIRST

`VWFMenu_Sweep` decides liveness by reading `Plane_A_Buffer` ($FFFF8000, 64x32
cells) and nothing else. That answer is only safe to ACT on where something
maintains the pool across windows.

Every `VWFMenu_SaveRegion` / `_Mark` / `_Release` / `_RemapRegion` call site is
inside `Window_Create` / `Window_Destroy` in `ps4disasm/ps4.asm` (~137950,
~138186, ~138205). That is the **field** window system.

**Battle keeps none of it.** Battle has its own window code which block-copies
plane regions (`loc_27DD04`, a `trap #1` block move). No Mark/Release, so the
pool never rewinds per window. No SaveRegion, so covered tiles' keys are never
recorded. No RemapRegion, so restoring a saved region puts back raw cell
indices that may now point at another string's glyph.

So a tile referenced only by a saved battle window looks dead to the sweep.
Reuse hands it out. The restore corrupts.

### Attempt 1 - REVERTED

Sweep at `SLOTS - 31` (31 = the composer's own per-run cap) so a run never
starts without room to finish, and let `StripEnsure` sweep and reuse a free run.

Fixed the item list. In battle: the Skill list drew "Illusion" through the tail
of "Double Slash", and the framerate collapsed - every menu draw swept, decided
nearly everything was free, and re-uploaded tiles to VRAM.

### Attempt 2 - REVERTED

Gate both behaviours on `a1` lying inside `Plane_A_Buffer`, on the theory that
battle composes into staging buffers.

Wrong. Some battle windows do (`$FFFF048A`, `$FFFF0900`, copied to `$FFFF3500`/
`$FFFF3580`), but **`loc_199E` draws the battle Tech list with
`lea ($FFFF8600).w, a1`** - inside the plane. The gate passed and battle broke
again: the Tech list scrambles when paging from page 2 back to page 1.

Both attempts were reverted at that checkpoint. The later scoped implementation
kept battle out of strip reuse, but the unconditional full-pool composer sweep
remained and reproduced one page-restore corruption. Removing that battle sweep
was still correct, but the 2026-09-09 playtest exposed an additional independent
12-versus-14-column restore bug in `loc_E8C`.

## Constraints a fix must satisfy

1. A strip needs its cells **contiguous**. Alloc's single-slot scan is not
   reusable for it.
2. Anything that only changes **when** the sweep runs will keep breaking
   battle. The asymmetry has to be removed, not detected.
3. The sweep must not free a tile that a saved-but-not-visible region still
   depends on, unless something repoints that region on restore.
4. Battle draws both inside and outside `Plane_A_Buffer`, so the buffer address
   cannot be used to tell battle from field.

## Chosen direction

Use the engine's own window-system discriminator: `Game_Mode_Index == $C` is
the verified field mode used by `LoadWindowGroup`. Dynamic field messages may
preflight and reclaim there. Static LOOK descriptions use the fixed renderer,
because all rows fit and they need no pool allocation. Battle never sweeps; it
releases submenu-only allocations at final selected/cancelled exits instead of
trying to infer liveness from incomplete plane state.

## Files and symbols

    ps4disasm/vwf/vwfmenu.asm    the whole menu VWF engine
      VWFMenu_Alloc              per-cell allocator; DOES reclaim
      VWFMenu_StripEnsure        scoped contiguous-run reuse + validation
      VWFMenu_Sweep              plane liveness + atomic strip expansion
      VWFMenu_DrawString_Composed field-only preflight sweep
    ps4disasm/ps4.constants.asm  VWFMENU_SLOTS, pool layout, RAM map
    ps4disasm/ps4.asm            Win_ItemActionLook (fixed description renderer)
                                 loc_199E (battle Tech list, $FFFF8600)
                                 loc_E8C (previous-page 14-column restore)
                                 Battle_*Selected / Battle_BackFrom* pool release
                                 loc_4A94 / loc_4B6E (player action-name scope)
                                 loc_B4E0 / loc_B59A (enemy action-name scope)
                                 loc_4624 (recurrent battle-results scope)
                                 Window_Create / Window_Destroy (field hooks)
    tools/menupool.py            computes the 83 slots from savestates

## Testing

    python tools/sourcebuild.py            build (writes ps4en.bin)
    python tools/test_strip.py             strip allocator + banner geometry
    python tools/test_itemtext.py          item menu text paths
    python tools/test_battle_tech_layout.py Tech geometry + submenu lifetimes
    python tools/test_battle_text_lifetime.py action/results name lifetimes

`tools/menuharness.py` runs real 68000 code against a savestate without an
emulator - `emu68k.py` raises on unimplemented opcodes rather than guessing, so
a trap means "add the opcode", not "the ROM is wrong". It has bitten twice with
addressing modes the assembler accepts but the emulator lacks (`move.b d16(a2),d1`,
`sub.w #imm,d0`); use the idiom the neighbouring code already uses.

`test_strip.py` now asserts both sides of the boundary: a full pool still
fails outside the explicit Item-page scope, while the scoped path reclaims a
contiguous run and leaves `PoolTop` at the cap. It also corrupts an old Hunter
Knife continuation deliberately and verifies that the stale head is rejected,
then leaves one strip cell visible and verifies that Sweep pins all eight.

`test_itemtext.py` audits all 320 static description rows against the 28-cell
field, confirms LOOK uses `LoadWindowTiles`, and retains the forced dynamic
overflow test: in field mode all nine cells draw after a sweep; in battle only
the five remaining slots draw and every old reference stays live.
`test_battle_tech_layout.py` now checks all six 14-column Tech paths, including
`loc_E8C`, and the selected/cancelled release for all three battle submenus.
`test_battle_text_lifetime.py` proves Technique User's source is
`EnemySkillNames:Resta`, reproduces a two-of-four-cell partial Resta and an
all-blank learned-Tech strip from the same pool pressure, then checks the exact
player, enemy, and results mark/restore pairs in the assembled ROM.

The complete source build (0 errors, 0 warnings), `disasmport.py` repeatability
check, and all ten regression scripts pass for `ps4en.bin` SHA-256
`3F10D33007050DB769CC2A6CEF713698858E73E85D22AC51DEF2B8F00E6527DC`.
These are static and harness checks; the reported in-game scenarios still
require emulator playtesting.

Two testing traps already hit here: three test files computed an `ok` flag and
exited 0 regardless (fixed; check new files with
`for f in tools/test_*.py; do grep -L sys.exit $f; done`), and an assertion that
pinned a bug to one magnitude ("blanks at prefill 60") went stale the moment an
unrelated width changed.

---

# Follow-up (2026-09-09): after the reuse-scope fix

Two reports from play, and they are the SAME cause: strip allocation still
cannot reclaim outside the two scopes the fix opened.

`VWFMenu_StripReuseOK` is set in exactly two places:

* `loc_5B482` - the field Item page repaint
* `VWFMenu_RemapRegion` - field `Window_Destroy` reveal

and `VWFMenu_DrawString_Composed` only sweeps when `Game_Mode_Index == $C`.

## 1. Status screen: skill panels blank (Hahn's Ether Vision)

`loc_5DAAC` draws `SkillNames` through `LoadWindowTiles`. It is a field window,
so the composer half is fine - but it is **not inside a reuse scope**, so
`VWFMenu_StripEnsure` is back to grow-or-fail and every skill name blanks once
the pool is high. Both COMBAT and FIELD come up empty, not one missing entry,
which is the signature of the whole allocation failing rather than a name being
absent.

CORRECTED ARITHMETIC. An earlier draft of this section counted class names at
29 slots. They are FIXED-WIDTH and cost the pool nothing - `test_paths` asserts
`party/class names $280CB0 -> fixed`, and the range comment beside
`VWFMENU_ENEMY_LO` says why (creep-coded, the VWF face gives them width 0).

What actually costs pool:

    class names (03:001)   0 slots   fixed-width
    party names            16 slots for all five, COMPOSED so tiles dedupe
    skill names            a contiguous strip RUN each, no dedupe between
                           them; mean 5.7 cells, so ~32 slots for four

So ONE character's status screen is roughly 36 slots and fits 83 comfortably.
The failure is cumulative, not per-screen: nothing reclaims between characters,
so paging through the party leaves every previous character's skill strips
resident until the pool is gone. That is consistent with the failure appearing
on the fourth character rather than the first, but it is a weaker claim than
"a status screen cannot fit" - which is what the earlier draft said, wrongly.

CONFIRMED BY EXPERIMENT (2026-09-09). Entering the camp fresh and opening
Hahn's Skills page FIRST still fails to draw Ether Vision. So it is not
accumulation across characters - one screen does it, and the mechanism is
`PoolTop` being a high-water mark rather than an occupancy count:

* the Skills window opens on top of the Tech window;
* `Window_Create` -> `VWFMenu_SaveRegion` records the covered Tech strips'
  keys and frees their `Refs`;
* but `VWFMenu_Release` is the ONLY thing that lowers `PoolTop`, and it runs
  on `Window_Destroy`.  The Tech window is covered, not destroyed, so
  `PoolTop` stays where its 37 slots of strips left it;
* `VWFMenu_StripEnsure` outside a reuse scope only ever APPENDS at `PoolTop`.
  It never looks below it.

So the freed slots are sitting there and the strip allocator cannot reach
them.  Hahn is the worst case because he has 10 unique techs - 37 slots, where
every other character has 1 to 5.  Measured for his screen from a cold pool:

    10 techs        37
    4 equipped      28   (item names are long: Ceramic Knife 8, Laser Barrier 8)
    Ether Vision     7
                    ---
                    72 of 83, before the party-name list and the rest

**Suggested fix:** the criterion the scope is written against - "Window_Create
records every covered tile and Window_Destroy remaps the saved cells on
reveal" - is true of *every* field window, not just the Item page. The status
screen should qualify on the same grounds. Scoping it to `loc_5B482` looks like
caution rather than necessity; widening it to the field character/status
repaint is the smaller change. (Reasoning, not tested - verify the status
screen really goes through the same Window_Create/Destroy pair first.)

## 2. Battle item list: blank past ~8-9 unique items

Working as designed, and still the original bug. Battle is excluded twice: the
composer sweep is gated on `Game_Mode_Index == $C`, and no reuse scope is ever
opened there. So the pool grows until `StripEnsure` fails.

That exclusion is CORRECT and should stay until battle has the same
bookkeeping - see the section above on why recycling a tile a battle window
saved by raw index corrupts the restore. Battle needs one of:

* the same Mark/Release/SaveRegion/RemapRegion hooks on its own window paths;
* a sweep that also scans battle's private page buffers; or
* less demand - the item description and the USE/LOOK/DSCD notices were made
  proportional recently and cost 21-24 pool tiles each where they previously
  cost zero.

Do not simply widen the `Game_Mode_Index` gate to include battle. That is
attempt 1 again.

---

# Separate bug: the pool claimed tiles the code writes by raw index

Symptom: an artifact instead of the ":" separator in the battle Skills menu.

`loc_1CC8` does not draw that separator through the text system at all:

    jsr     (loc_27DC7A).l        ; the count digits
    move.w  #$6FF, -$6(a1)        ; the separator, as a raw tile number
    add.w   d0, -$6(a1)           ; plus the attribute

`$6FF` is one of the 20 frame tiles `tools/menupool.py` reclaimed into the
pool, so composed glyphs now land on it and this write picks up whatever was
last composed there.

`menupool.py` finds "unused" frame tiles by scanning SAVESTATES. That can only
see what was on screen in the states it was given, so a tile written by raw
index from a menu no savestate captured looks free. Cross-checking the
reclaimed list against immediates in `ps4.asm` finds five such tiles:

    $6FF   loc_1CC8 skill separator, plus two sites in the vehicle window
    $6EB   move.w #$6EB, d2 -> +$E000 -> plane
    $6EC   move.w #$6EC, d2 -> +$E000 -> plane
    $6F2   cmpi.w #$6F2, d7   frame code reading a cell back
    $6E0   addi.w #$6E0, $1E(a1)

Suggested fix: `menupool.py` should exclude any tile the code names as an
immediate, found by a static scan of `ps4.asm`, in addition to the savestate
evidence it already uses. Match only the two shapes that really name a tile -
a bare `#$6xx`, or a nametable word `#$X6xx` whose high nibble is an
attribute. Do NOT mask every 3-4 digit immediate to `& $7FF`: palette values
like `#$EEE` and `#$EE0` then masquerade as tiles $6EE and $6E0, which is
wrong twice over (two of my own scans made exactly that mistake).

Cost: the pool drops from 83 to about 78 slots, which tightens every budget in
this document. Correctness first - a repurposed tile is a visible artifact
wherever that code runs, and $6FF alone has three sites.

---

# State check (2026-09-09, later)

## Item descriptions are fixed-width again

`Win_ItemActionLook` calls plain `LoadWindowTiles` with `d4 = 0`, so
`ForceCompose` is never set and `VWFMenu_DrawWindowRun` takes its `.fixed`
path - one fixed cell per character. There is only one draw site for
`InventoryDescriptions2`, so this is EVERY description, not some.

Nine of the ten item-action sites still compose (six USE paths, three DSCD
notices); Look is the only one back to fixed-width. If that was deliberate
budget relief it is a reasonable trade - the description is the single largest
pool consumer on that screen at ~21 tiles, against zero fixed - but it leaves
the screen inconsistent: the DSCD refusal composes while the description
beside it does not, which is visible as "Land Master cannot / be discarde"
losing its tail to the pool cap while the description never touches the pool
at all. Decide which way that screen should go rather than leaving it split.

## The battle skill counter is not a budget item

It is `move.w #$6FF, -$6(a1)` - a raw stock tile index, not composed text.
Replacing it with a fixed-width lowercase "x" would save nothing and lose the
glyph. The only problem with it is that `menupool.py` gave `$6FF` to the pool;
see the section above.

Vehicle battles rendering correctly does NOT contradict that: the same three
`$6FF` sites are latent, and only corrupt once the pool has grown far enough
to hand that slot out. Do not treat "the vehicle window looks fine" as
evidence the tile is safe.

---

# Fourth context: the item shop Sell list (2026-09-09)

Strips blank out in the shop Sell menu with a large inventory.

**The dialogue box is NOT competing for these tiles.** `vwf/vwfdia.asm` states
it: "The dialogue box is a private 128-tile region at VRAM $B000". The menu
pool is tiles $682-$6FF, VRAM $D040 up. Reverting lines like "Which will you
sell to me?" to fixed-width would free ZERO menu-pool tiles. Do not spend
effort there.

The cause is the same one as the status screen: the shop draws item-name
strips through `LoadWindowTiles`, and every shop path is outside the only
reuse scope in the game. `grep StripReuseOK ps4disasm/ps4.asm` returns exactly
two lines, both in `loc_5B482`, the field Item page.

The screenshot evidence is worth keeping because it pins the mechanism: a
3-cell "Claw" drew AFTER two 9-cell names had blanked. Failures go by LENGTH,
not by order - which is precisely grow-or-fail on a CONTIGUOUS run, not simple
exhaustion.

CORRECTION: an earlier draft said eight rows nearly exhaust the pool cold.
Wrong - page 1 fits comfortably. The failure is CUMULATIVE across pages, and
the reported case is page THREE.

The observed pattern pins it exactly. Page 3 was: Cure Paralysis(9) drew,
Titanium Slicer(9) drew, Moon Atomizer(9) BLANK, Titanium Axe(8) BLANK,
Claw(3) drew, Claw(resident, free), Wood Cane(6) BLANK, Ceramic Sword(9)
BLANK. Only `PoolTop` in 58..62 reproduces exactly those hits and misses, so
pages 1-2 left about sixty slots standing.

## Freeing and REUSING are different things

The obvious objection is "surely off-screen pages are freed?" They are:
`VWFMenu_Sweep` rebuilds liveness from the plane and correctly marks pages 1
and 2 dead. Three separate facts make that useless to a strip:

    VWFMenu_Sweep        clears Refs - the slots ARE marked free
    VWFMenu_Release      lowers PoolTop, but only from Window_Destroy, and the
                         shop window stays open across pages
    VWFMenu_StripEnsure  only ever APPENDS at PoolTop; it never looks below it

So the reclaimed slots sit below `PoolTop` where the strip allocator cannot
see them. The space is freed and cannot be spent.

`VWFMenu_Alloc` - the composed path - DOES scan for `Refs == 0` before
growing. That asymmetry is the entire bug, and it is why composed text keeps
working on these screens while strip tables blank out.

## The scope should be a criterion, not a list

This is now the fourth context to hit the same bug - the field status screen,
battle, the shop Sell list, and the original Item page. Each one has needed
its own scope added by hand.

The criterion the scope is written against - "Window_Create records every
covered tile and Window_Destroy remaps the saved cells on reveal" - is a
property of the FIELD WINDOW SYSTEM, not of any particular screen. It is true
of the status screen and the shop exactly as it is of the Item page. Enumerate
it once, as a condition, and all four are covered; keep enumerating screens
and there will be a fifth.

Battle remains the genuine exception, and for the documented reason: it keeps
none of that bookkeeping, so there is nothing to reclaim into.

---

# Current actionable checkpoint plan (2026-09-09) — TODO

This section is the continuation plan, not a claim that any checkpoint below
has shipped or passed an emulator playtest. Preserve the historical analysis
above: it explains the failed approaches and the invariants this work must not
violate.

## Clarified evidence

The reported `Res` in VWF and the later level-up message were **separate
events**. `Res` was a smallcaps VWF allocation symptom, not the level-up
insertion falling back to the stock `RES` spelling. The level-up message
separately omitted the learned Technique name. They nevertheless independently
show pool exhaustion: the former demonstrates a partial composed allocation;
the latter demonstrates a failed atomic translated-name strip allocation.

## Required order

1. Complete and prove **Checkpoint A** before shrinking the pool or changing
   battle allocation policy. It establishes the safe field capability model.
2. Complete **Checkpoint B** next. Its new 76-slot capacity is a hard input to
   every subsequent budget and test.
3. Complete **Checkpoint C** only after B has regenerated the ROM and the
   field budgets have been remeasured. Battle must not inherit field Sweep or
   strip-reuse permission.
4. Treat **Checkpoint D** as the final UI-consistency pass after the capacity
   and lifetime behavior are stable.

## Checkpoint A — managed field-window pressure retry (TODO)

Extend the existing field-only reclaim design to every window path that is
actually managed by the field window system: `Window_Create` must have saved
the covered region and `Window_Destroy` must remap it on reveal. Use an
explicit capability depth/inhibit boundary, rather than a growing list of
screen labels: enter only while a managed field repaint can safely reclaim,
narrowly inhibit it across animations or retained raw-cell buffers, and unwind
it exactly on every exit.

Do not enable it from the destination address alone. `$FFFF8600` is used by
both field and battle, and battle's private copies remain invisible to a plane
sweep.

Acceptance criteria:

* Field Status/Tech/Skills and shop Sell pages can repaint under a deliberately
  full pool without blank strip rows or stale-strip corruption.
* Nested field windows balance capability depth and inhibit state on normal,
  cancel, and animation exits; `PoolTop`, saved-region records, and remapped
  cells remain valid.
* Add harness coverage for the managed-field high-pressure transition, plus
  static checks that no battle path can acquire this capability.
* The observed one-to-two-frame item-row blanking is either eliminated or
  remains explicitly reproduced and diagnosed; do not silently relabel it
  fixed.

### Checkpoint A status (Claude, 2026-09-09)

Resumed after the Codex session ended. The capability model is IMPLEMENTED and
is criterion-based, not a screen list:

    VWFMenu_FieldReclaimAllowed   field mode ($C) AND FieldReuseDepth != 0
                                  AND FieldReuseBlocked == 0
                                  AND ReclaimInhibit == 0
    FieldReuseDepth               incremented in VWFMenu_Mark once SaveMarkPush
                                  and SaveRegion have both succeeded; retired in
                                  VWFMenu_SaveMarkPop after RemapRegion
    FieldReuseBlocked             untracked nesting fails closed
    ReclaimInhibit                nesting count, entered by the NoSweep remap;
                                  both RemapRegion entries push a per-invocation
                                  tag so the shared exit unwinds exactly once

`VWFMenu_StripEnsure` and the composer sweep both gate on it, so the status
screen and shop Sell pages are covered by the same condition as the Item page.

Build `D13322C24DBD5276AB081EE7D5A5AF985572468F9E62620C81E510AF499E298F`.
All ten harnesses pass. Note there are TEN test files now, not nine -
`test_battle_text_lifetime.py` is easy to miss when running the suite by hand.

Closed this session:

* `test_battle_text_lifetime.py` had `SLOTS = 83` hard-coded; it now reads
  `VWFMENU_SLOTS` from `ps4.constants.asm`. Verified by temporarily setting the
  constant to 76 and confirming the test's behaviour changed, then restoring it.
  `test_itemtext.py` already read the constant.
* Added the static battle-exclusion checks the acceptance criteria asked for.
  The dynamic pressure tests prove battle is denied at run time; these assert
  the structure behind it, which a refactor could remove without turning any of
  them red: the gate contains `cmpi.w #$C,d0`, the three capability counters
  have zero references from `ps4.asm`, and `VWFMenu_StripReuseOK` has exactly
  two (the Item page set/clear pair).

STILL OPEN for A: no emulator playtest has been run against this build. The
acceptance criteria require the field Status/Tech/Skills and shop Sell pages to
repaint under a full pool in play, and the one-to-two-frame item-row blanking
to be either eliminated or explicitly reproduced. Harness evidence does not
settle either.

## Checkpoint B — source-driven raw tile exclusions (TODO; depends on A)

`tools/menupool.py` currently contains a manually derived savestate allow-list
but does not actually scan source despite its comments. Keep the savestate
evidence as the tentative free set, then remove every tile explicitly named by
a code immediate. The current exclusion set is:

    $6E0  $6EB  $6EC  $6EF  $6F0  $6F2  $6FF

The `$6EF`/`$6F0` vehicle remap comparisons are in addition to the five names
already identified in the historical section. A conservative source rule is
intentional: naming a raw tile is enough to keep its VRAM pattern out of the
composed pool.

Parse instruction operands only (after removing comments; never `dc.*` data).
Recognize a bare `#$6xx` or an attributed nametable word `#$X6xx`, allowing
leading zeroes; do not obtain a tile number by masking arbitrary immediates.
That preserves the distinction between actual tile operands and palette values
such as `#$EEE`/`#$EE0`.

The resulting layout is 63 contiguous plus 13 scattered tiles: **76 slots**.
Regenerate `poolslot.bin` and `pooltile.bin`, update `VWFMENU_SLOTS`, and make
all capacity consumers derive the same value. Known consumers include
`tools/guildnames.py`, `tools/poolpeak.py`, `test_strip.py`,
`test_itemtext.py`, and `test_battle_text_lifetime.py`; `checkbuild.py` already
parses the assembly constant and must additionally assert that the pool has no
intersection with source-named raw tiles.

Acceptance criteria:

* Parser tests include positive `$6FF`, `$E6EF`, and `$16C0` cases and negative
  `$EEE`/`$EE0` palette cases; the assembled/generated pool is disjoint from
  all currently named raw tiles.
* The exact seven-tile exclusion is visible in generator output and guarded by
  a regression test, so a new raw immediate fails the build rather than
  silently reclaiming its tile.
* The Guild board renders all eight rows at its measured 76-tile maximum with
  no blank tail. `guildnames.py` currently reports 76 of 83, so 76 is an exact
  fit, not headroom.
* Rebuild and remeasure every supplied high-pressure state. In particular,
  historical `ps4en-fieldtech.exs` recorded Peak 80 and must not be treated as
  proof that a 76-slot build fits merely because its current visible set is
  smaller.

### Checkpoint B status (Claude, 2026-09-09) — IMPLEMENTED, playtest pending

Build `F3414E34B75FE56B658D5DE6CDDD35319B880EBDFA549329266C4540B260E026`.
All eleven harnesses pass (`test_menupool.py` is new).

`tools/menupool.py` now actually scans source. Savestate evidence gives the 20
candidates; every tile named by a code immediate is then removed, leaving
**63 contiguous + 13 reclaimed = 76**, and the seven exclusions match the
prediction exactly:

    $6E0  addi.w  #$6E0, $1E(a1)          ps4.asm:60131
    $6EB  move.w  #$6EB, d2               ps4.asm:308158
    $6EC  move.w  #$6EC, d2               ps4.asm:308171
    $6EF  cmpi.w  #$E6EF, (a1)            ps4.asm:308201
    $6F0  cmpi.w  #$E6F0, (a1)            ps4.asm:308206
    $6F2  cmpi.w  #$6F2, d7               ps4.asm:140283
    $6FF  move.w  #$6FF, -$6(a1)          ps4.asm:2793

The generator prints the exclusions with their source lines, so a new raw
immediate is visible rather than silently costing a slot.

#### Two parser traps, both hit while writing this

1. Masking any immediate with `$7FF` turns palette values into tiles - `#$EEE`
   becomes $6EE, `#$EE0` becomes $6E0. The rule matches only a bare `#$6xx` or
   an attributed `#$X6xx`.
2. The immediate must be the WHOLE hex run. Without that, `move.l #$96FD9580`
   matches its "96FD" prefix and steals $6FD, giving 75 slots instead of 76.
   The pattern ends in a negative lookahead rather than ``, which is one
   backslash away from a literal backspace and produced a silently
   never-matching regex twice.

#### Deviation from the spec, deliberate

The spec asks that "the pool has no intersection with source-named raw tiles".
That cannot hold literally: the CONTIGUOUS run contains 18 immediates in the
same numeric range that are not tile references - `move.w #$690, (a1)` writes
an object's type field at offset 0 straight after `Battle_LoadObject`, and
`addi.w #$6C0, $1E(a4)` adds to a position field. Excluding those would delete
most of the pool.

So the source rule is applied to the RECLAIMED candidates only, where a
frame-range tile named by an immediate is a real dependency.
`test_menupool.py` asserts the reclaimed set is disjoint from named tiles, and
separately that every contiguous-range name is still one of those known
false-positive shapes, so a genuine tile reference landing in the run cannot
hide behind the exemption.

#### Capacity is derived everywhere now

`guildnames.py` and `poolpeak.py` were restating 83; both now parse
`VWFMENU_SLOTS`. `test_strip.py` and `test_itemtext.py` already did;
`test_battle_text_lifetime.py` was fixed earlier this session.

#### Two things the acceptance criteria flag, unresolved

* **The Guild board is 76 of 76.** `guildnames.py` reports an exact fit with
  zero headroom, as predicted. The build fails if a title grows, which is the
  right behaviour, but there is no margin at all in play.
* **Recorded peaks exceed the new capacity.** `ps4en-fieldtech.exs` peak 80
  and `vwfmenu11-status.exs` peak 83, against 76. (A third,
  `trace-fixedwidth.exs`, reads peak 35632 with `live now 65535` - that is an
  uninitialised pre-VWF state, not a signal.) Those peaks were recorded by
  older builds: the word space has since gone 8px to 3px, the item menu became
  pool-free, and Checkpoint A added reclamation. They are therefore not
  predictions for this ROM - but per the criteria they must not be waved away
  either. Settling it needs those scenarios replayed on this build.

## Checkpoint C — battle root/headroom and on-demand pages (TODO; depends on B)

Battle remains outside field capability, Sweep, and strip reuse. The existing
submenu/action/results marks are useful local lifetimes, but the actual root
and headroom must be measured against the new 76-slot ceiling. Capture the
baseline after the persistent battle HUD/enemy text is live, then account for
each transient surface from that root.

For Tech, Skill, and Item page navigation, regenerate the destination page on
demand from its source list rather than retaining private raw tile-ID page
buffers past the point where their allocations need to be reused. Any such
change must be paired with explicit page/window lifetime ownership. Do **not**
call `VWFMenu_Sweep` in battle or grant battle `StripReuseOK`; either shortcut
recreates the documented raw-page-restore corruption.

Acceptance criteria:

* Worst-case battle list/page transitions, enemy Technique names (including
  smallcaps `Res`), player actions, and learned-Tech results all fit from the
  measured root or fail predictably only when a deliberate capacity test asks
  them to.
* Page 2 -> 1 Tech restoration remains 14 columns and no raw page buffer is
  reused after its tile ownership ends.
* Add harness/emulator coverage that starts at a near-full battle baseline and
  exercises each final selected/cancelled exit plus both page directions.

### Checkpoint C status (Claude, 2026-09-09) — MEASURED, part 2 not attempted

Guild board and high-Tech verification were deferred by the project owner:
roughly 15 hours of playtime away, so they remain open by decision rather than
by evidence. Checkpoint B's two flags are NOT resolved.

`tools/battlebudget.py` (new) reports the root and every transient surface
against the current `VWFMENU_SLOTS`. At 76:

    ROOT (persistent HUD + enemy banner, deduped)     26   -> 50 free
      5 party names, composed                         16
      enemy banner, composed (GrassSlaughterer)       10

    TRANSIENT, each from that root
      enemy action name (Ultrasonic Wave)             10   fits
      player action name (Ragrants)                    6   fits
      Tech page, 8 rows                     45 worst / 34 typical   fits
      Skill page, 8 rows                    64 worst / 45 typical   worst OVERFLOWS
      Item page, 8 rows                     77 worst / 61 typical   BOTH overflow

The item page is the surface that cannot fit, which is exactly the reported
symptom - battle items blanking past eight or nine uniques. And because battle
has no reclamation at all, page navigation ACCUMULATES: two item pages is
~122 against 50 free.

Composed text dedupes by tile; strips do not. That asymmetry is why the item
page - long names, all strips - overflows first, while the tech page (short
names) fits even at worst case.

#### Part 2 not attempted, deliberately

Regenerating pages on demand plus per-page mark/release is the right shape, and
it is consistent with the BattleActionMark / BattleEnemyMark / BattleResultMark
lifetimes already in the tree. But the two halves are coupled: rewinding
PoolTop on a page change is only safe if the destination page is REGENERATED,
because a retained raw page buffer restore depends on the very tiles being
released. Getting that wrong reproduces the documented page-restore corruption.

This is a battle change, and battle is where two previous attempts shipped
corruption on harness evidence alone. It should not land without a playtest.

The good news is that this one IS reachable: the battle item page overflows at
eight or nine uniques, which the project owner already hit in normal play -
unlike the guild board. So part 2 can be verified early, and should be, before
anything else in battle is touched.

## Checkpoint D — DSCD consistency and polish (TODO; depends on C)

Once capacity and lifetimes are proven, make the item action screen internally
consistent. LOOK is fixed-width deliberately because its static two-line text
fits 28 cells. Decide whether DSCD notices should remain fixed-width with it,
or become a bounded proportional surface with an explicit safe lifetime. Do
not mix renderer choices accidentally, and do not reintroduce a proportional
dynamic notice without a field-pressure test for its complete two-line run.

Acceptance criteria:

* LOOK, USE, and DSCD behavior is intentional and documented, including
  wrapping/truncation policy.
* Item page, LOOK/DSCD round trips, and later-page inventory redraws have no
  persistent blanks, partial notice tails, or visual regressions.

## Continuation note for Claude

Start by reading this checkpoint section and the historical constraints above,
then inspect the current tree before changing code: earlier notes describe
attempts that were reverted and must not be reapplied wholesale. Work one
checkpoint at a time, build with `python tools/sourcebuild.py`, and run the
relevant harnesses plus the full regression suite after each checkpoint. Record
the generated ROM hash, exact capacity, measured peak/root values, and
emulator scenarios actually exercised. Do not claim an emulator symptom fixed
from static or harness evidence alone.

---

# Field Skill names fall back to the US table (2026-09-09) — TODO

Reported from play: using `MedicalPower` from the field Skills menu shows
`MEDIC PW`, and `Recover` shows the all-caps `RECOVER`.

Same shape as the item and technique cases already fixed. Menu LISTS draw
prerendered strips keyed by the table's offsets, so `SkillNames` itself was
never retranslated and still holds the US abbreviations:

    SkillNames:  "CROSSCUT" "RAYBLADE" "DBLSLASH" "FLAELI" "FLARE" "VORTEX"
                 "ASTRAL" "AIRSLASH" ... "RECOVER" "MEDICE" "MEDIC PW"

Any path that copies those bytes into RAM to build a sentence gets the US
name. `fieldstrings.py` generates a translated parallel table for exactly this
reason, but only for two of the three segments:

    TABLES = (("00:001", 160, "fielditemnames.bin"),     items   -> fixed
              ("00:002",  40, "fieldtechnames.bin"))     techs   -> fixed
                                                          skills -> MISSING

## Recipe

1. Add `("00:003", 54, "fieldskillnames.bin")` to `fieldstrings.py` TABLES.
2. Declare `VWFField_SkillNames: binclude "vwf/fieldskillnames.bin"` beside
   the other two in `vwf/vwfmenu.asm`.
3. Repoint the four field sites that copy `SkillNames` into RAM - ps4.asm
   lines ~129219 (`loc_61AD4`), ~129508 (`loc_61E3A`), ~129960 (`loc_6243C`),
   ~130085 (`loc_625A4`). Confirm each is a RAM-assembly path before changing
   it.
4. Do NOT touch `loc_27DE5E` (~308506). That is the battle name-table
   dispatch feeding `loc_27DB9C`; `SkillNames` is inside the strip range, so
   battle lists already draw the translated strips.
5. Add `fieldskillnames.bin` to the file list in `tools/checkbuild.py`.

## Budget: no overflow

`fieldstrings.py` validates techs as `name + " is used!" <= 24 fixed cells`.
Longest skill name is 13 characters (`Positron Bolt`, `Barrier Field`), so the
worst sentence is 22 cells. Zero skills exceed the field. Apply the same check
to the new segment so a later rename cannot break it silently.

Not applied yet: the tree was left untouched so the emulator test in progress
runs against build D13322C2 unchanged.

# Checkpoint C part 2 - battle item pages (implemented, awaiting playtest)

## The symptom

Past roughly 8-9 unique items, entries stop drawing in the battle item list.

## The cause

The battle item menu keeps four private page buffers (`$FFFF3600`-`$3900`) and
pre-renders all four when the menu opens. Every item on every page therefore
takes a strip run at open time, against a measured battle root of 26 with 50
slots free (`tools/battlebudget.py` reports Item 77 worst / 61 typical - both
overflow). Battle keeps no `SaveRegion`/`Mark`/`Release` bookkeeping and
`VWFMenu_Sweep` derives liveness from `Plane_A_Buffer` only, so nothing is ever
reclaimed mid-battle. The pool simply runs out partway down the list.

## The fix

Only the page actually on screen may own tiles. `Battle_ItemPageRender`
(ps4.asm, before `loc_2310`) rewinds `PoolTop` to `VWFMenu_BattleBase` and
re-renders the destination page:

    Battle_ItemPageRender:
        movem.l d0-d7/a0-a6, -(sp)
        move.w  (VWFMenu_BattleBase).l, (VWFMenu_PoolTop).l
        ... Battle_GetFighterStatsAddr / loc_211A / loc_204E ...

`loc_211A` versus `loc_2122` was the blocker resolved first: `PlaneMapToRAM`
takes `a1` as its DESTINATION and preserves it (`movem.l d0-d2/a0-a2,-(sp)`
then `movea.l a1, a2`), so `loc_211A` (`lea ($FFFF0600).l, a1`) composes a page
off-plane while `loc_2122` (`lea ($FFFF8600).w, a1`) writes the live plane. The
rebuild wants the off-plane form.

Wired into both page handlers (after the `move.w d1, (a0,d0.w)` index store,
distinguished by `#$1A` vs `#$1B`), guarded by `if vwf_menu_strips=1`. It is
deliberately NOT wired into `loc_FBE`/`loc_FF8`, the window-open slide, which
re-enters once per frame and would rebuild continuously.

## Constraints honoured

C forbids two things in battle, both verified structurally in
`tools/test_battle_text_lifetime.py`:

  * never calls `VWFMenu_Sweep`  - battle has no saved-region bookkeeping
  * never takes `StripReuseOK`   - the two earlier battle regressions came
                                   from exactly this
  * does rewind `PoolTop` to `VWFMenu_BattleBase`

Plus: both page directions call it (2 sites), and it is absent from the
open-animation span `loc_FBE`..`Battle_FillTechList`. The call-site check was
mutation-tested - removing one `bsr.w` makes it FAIL.

Build `D1AD36F37289557984D8F9D9DB05061735B884773EAE303A40E22477A12F956B`,
all 11 test files pass.

## Status: NOT verified in play

Structural evidence only. Per this document's own rule, an emulator symptom is
not fixed until seen fixed on the emulator. Scenario to exercise:

  1. a battle item list with more than 8-9 unique items
  2. page forward AND back through all four pages
  3. exit by selecting an item, and separately by cancelling
  4. re-open the menu afterwards in the same battle

## Known remaining waste (harmless)

The original open-time pre-render chain (`loc_200A`/`loc_1FCA`) is still in
place, so all four pages are still rendered once when the menu opens. That is
now pointless work rather than a correctness problem, because every page the
player actually reaches is rebuilt on the way in. Removing it is a follow-up
optimisation, not a fix; leaving it in keeps the change minimal and means a
failed playtest points at the rebuild rather than at a missing initial state.

## Regression found in playtest, and fixed

The first cut of `Battle_ItemPageRender` locked paging: after moving to page 2
neither direction responded until the menu was closed and reopened, and the
nav arrows were visibly gone from the window frame.

Cause: the `$66E6`/`$6EE6` arrow words at offsets `$0` and `$1A` of the page
buffer are NOT decoration. `Battle_ItemWindow` gates paging on them:

    cmpi.b  #$E6, $1B(a2)   ->  loc_2310   (page right)
    cmpi.b  #$E6, $1(a2)    ->  loc_235C   (page left)

`a2` is the page buffer, and the test reads only the LOW BYTE of each arrow
word at an ODD offset - which is why grepping for `66E6`/`6EE6` finds every
write and no read. `loc_204E` runs `Battle_SetupWindow` over that buffer and
then block-copies the composed window back over it (`loc_27DD04`, a1 = the
original a0), so the rebuild wiped both arrows and with them both gates.

Fix: restore the arrows after `loc_204E`, on the same two conditions
`loc_1FCA`/`loc_200A` use - left iff this is not page 0 (`cmpa.l
#Battle_Item_List, a2`), right iff the next page has a first item (`tst.b
$4(a2)`). `a0` and `a2` both survive `loc_204E`'s `movem.l d7/a0/a2/a5`, which
is the same guarantee `loc_200A` already relies on.

Second symptom, same playtest: reopening the menu on a page later than 1 could
still hide strips. The open-time pre-render chain still runs and can exhaust
the pool before it reaches the retained page, and the rebuild only fired on
page CHANGE. Fixed by also rebuilding on the first frame of the open animation
(`loc_2024`, the `bset #7` fall-through), which runs after the pre-render chain
has finished and before the slide's final `PlaneMapToRAM` paints the plane.

Harness: the call-site count check was replaced with span checks that each
arrival path (`loc_2310`, `loc_235C`, `loc_2024`) is wired, plus checks that
the rebuild writes both arrows at the offsets the gate reads. Mutation-tested:
replacing the left-arrow write with `nop` makes it FAIL.

Build `157AEBD48A8918BE855518606D6966829BE2F73258B9F1F4FC0AA35F9420F47C`,
all 11 test files pass. Still unverified in play.

## Checkpoint C: VERIFIED IN PLAY (build 157AEBD4)

Playtest confirms the battle item list pages correctly in both directions past
the 8-9 item threshold, and reopening on a later page renders. Checkpoint C is
closed.

Residual, D-priority: switching pages shows stray cells for a frame or two
before the repaint lands. Same class as the existing field-menu paging repaint
already logged at D. Cosmetic, not a tile-ownership fault - the rebuild happens
before the slide's final PlaneMapToRAM, so what is briefly visible is the
previous page's plane content, not a blank or corrupt buffer.

# Open: Rudy's Skills page truncates (status screen)

Reported: Rudy's Skills list draws `Earth Bind` then leaves the next two rows
nameless, with their `5/ 5` and `2/ 2` counts intact - the classic strip
starvation signature (counts are fixed-width, names are strips).

Measured demand, via `menustrip.compose`:

    techs  Resta 4  Grants 4  Anti 3  Zan 3  Limpas 4  Giresta 4  Gigrants 5
           = 27 cells over 7 techs
    skills Earth Bind 6  Sword Cross 8  Air Slash 6
           = 20 cells
    both layers = 47 of 76

So the two lists alone are NOT the whole story - 47 fits. The residue is what
else is already resident when Skills opens. `work/rebuilt-status.exs` measures
peak 53 on a character with only TWO techs (`tech IDs: 14 18`), so the
non-tech baseline of a status screen is already large; Rudy adds five more
techs on top of that baseline and the previously recorded status peak of 83
is consistent with going over.

Why reclaim does not rescue it: `VWFMenu_FieldReclaimAllowed` gates correctly
in field mode and reclaim only fires under allocation pressure
(`cmpi.w #VWFMENU_SLOTS, d3 / bls -> append`), which is right. But sweep
derives liveness from `Plane_A_Buffer`, and the Techs window is still open
UNDERNEATH Skills and only partially covered - its surviving cells are still
referenced on the plane, so they are not free to take. This is exactly the
question already raised once ("is it possible to clear Techs once Skills is
pulled up?") and deferred.

Next step is a savestate taken ON the failing Rudy Skills page;
`tools/poolpeak.py` reads peak, live, resident keys and per-window marks
straight out of it and settles what the baseline actually consists of. Guessing
at the composition from the screenshot is not worth doing when the measurement
is one file away.

## Measured: Rudy's Skills failure, from a BlastEm savestate

`tools/blastem_ram.py` (new) extracts the 64K work RAM from BlastEm's native
`BLSTSZ` savestate, which has no parseable section table but stores work RAM
uncompressed and contiguous. It locates the base by content: windows of RAM
that the game copies from ROM at boot are taken from a known-readable Exodus
state and matched verbatim, and the offset the majority agree on is the base
(94 of the sampled windows agreed; the runner-up got 5). The result is
byte-identical to what Exodus exposes, so every existing .exs reader works
unchanged. `poolpeak.py` now accepts either format.

Reading the failing page directly:

    live now 71   peak 76   SATURATED at 76
    reclaim gate: ALLOWED (mode $C, depth 14, blocked 0, inhibit 0)
    window marks: 0 0 16 16 16 16 16 16 16 37 37 64 71 71 0 0
    tech IDs: 16 02 05 26 0d 04 01        (7 techs - Rudy)

The marks are PoolTop sampled at each window's creation, so the deltas are what
each layer allocated:

    baseline through window 8      16
    windows 2-8                   +21  -> 37
    windows 9-10   (Tech list)    +27  -> 64     matches the 27 cells computed
                                                  from menustrip for Rudy's
                                                  7 tech names, exactly
    window 11      (Skill list)    +7  -> 71     then hit the ceiling

Skills need 20 cells and only 12 were left. `Earth Bind` (6) drew; `Sword
Cross` (8) and `Air Slash` (6) did not. That is the whole failure.

The important negative result: the reclaim gate was ALLOWED, not denied. All
four conditions held, so `VWFMenu_Sweep` ran under pressure and still freed
nothing. This is NOT the earlier Hahn bug recurring and it is not a gating
defect - the resident cells are genuinely live in `Plane_A_Buffer`. The Tech
window sits underneath Skills and is only partially covered, so its 27 cells
stay referenced. `poolpeak.py` now prints the gate state and says so directly,
because a saturated peak looks identical whether sweep was denied or simply
found nothing to take.

So the lever is one of:
  a. retire the covered Tech cells - needs liveness that does not depend on the
     partially-visible window still being on the plane;
  b. cut the 37 cells consumed before the Tech list (windows 2-10) - not yet
     identified, and worth identifying before choosing;
  c. draw skill names fixed-width, as LOOK/DSCD/USE already do, which costs
     zero pool and is the cheapest certain fix.

### Correction: the pool is FRAGMENTED, not full

The Tech frame is completely covered by the Skills frame - same dimensions,
same position - so its cells are provably invisible once Skills is up. Reading
the Refs array straight out of the savestate:

    PoolTop 71 of 76
    refs below PoolTop:
      ...#########....#########################....###...########.....#######
    dead runs, longest first: [5, 4, 4, 3, 3]
    free: 19 dead below PoolTop + 5 above = 24 cells
    needed: Sword Cross 8 + Air Slash 6 = 14

There is nearly twice the space required. What is missing is a contiguous run.
`VWFMenu_StripEnsure_Free` searches for `d5` CONSECUTIVE dead slots because a
strip is recorded as head + count, and both the VRAM upload
(`VWFMenu_StripEnsure_Tile`, walking `d7` from the head and indexing
`SlotTile`) and the plane write step `head + i`. The longest run available is
5, so an 8-cell name cannot land even though 24 cells are free.

Note this is NOT a VRAM-contiguity requirement. `VWFMenu_SlotTile`
(`vwf/poolslot.bin`) already maps slot -> VRAM tile with the comment "the pool
is not contiguous", and the upload loop resolves each cell through it. The
constraint is purely the head+count bookkeeping in slot-index space.

So the earlier framing - "trim the baseline" or "retire the covered Tech
cells" - was aimed at the wrong quantity. Total capacity is not the binding
constraint at the moment of failure; contiguity is.

Options, re-ranked against this:

  a. Release the covered Tech window as a UNIT before Skills allocates, so its
     27 cells return as one run instead of being recovered piecemeal by an
     opportunistic sweep under pressure. Directly analogous to the battle item
     page fix (rewind to a known base, then draw the visible page), which is
     now verified in play. Best fit for the measured failure.
  b. Make strips scatter-tolerant - store a per-cell slot list instead of
     head+count. Removes the constraint permanently but touches StripOf,
     StripIdx, Sweep's run pinning and RemapRegion: the exact machinery behind
     both earlier battle regressions.
  c. Fixed-width skill names. Zero pool cost, certain, loses VWF on that list.
  d. Trim the 37 cells spent before the Tech list. Helps capacity, does not
     address fragmentation, so it would only postpone the failure.

## Option (a) implemented: VWFMenu_Compact

`VWFMenu_Compact` (vwf/vwfmenu.asm, called from the head of `VWFMenu_Mark`
under `if vwf_menu_strips=1`) walks `PoolTop` back over the trailing run of
dead slots at window-create time, so a covered window's cells come back as ONE
contiguous run instead of being recovered piecemeal under pressure.

Why Mark is the right hook: `Window_Create` calls it after
`Window_BackupTiles` and `SaveRegion`, so the covered window's cells no longer
reference pool tiles on the plane and a fresh sweep marks them dead - and it
runs before the new window allocates anything, which is exactly when the run
is needed. Compaction happens before the new mark is recorded, so the mark is
the compacted value and `Release` stays consistent.

Three limits make walking PoolTop backwards safe:

  1. gated on `VWFMenu_FieldReclaimAllowed`, which excludes battle and every
     untracked/no-sweep scope - the same criterion already proven in play;
  2. clamped to the innermost open window's own mark, so it can only ever give
     back allocations made by the window currently on top, never an ancestor's
     (and never below a mark that `Release` will later restore);
  3. the walk stops at the first live slot, and `VWFMenu_Sweep` pins a whole
     strip run whenever any one of its cells is still visible, so a strip can
     never be cut in half.

Verified against `work/rudy-skills.state` in `tools/test_compact.py`: no
Tech-range slot is visible on the plane (the frame is fully covered), so the
walk takes PoolTop 64 -> 37 and hands Skills 39 contiguous cells against the 14
it needs. The test also pins the degenerate cases - an all-dead tail stops at
the floor, an all-live tail is a no-op.

Build `BA78DDA3B596ABFBF5ADDE34BAFDA8A3BD032AFF73BED79FC6CE013FB9ACF2EF`,
all 12 test files pass. NOT yet verified in play.

Playtest scope - this touches every field window create, not just Skills:
  1. Rudy's Status > Skills page, the reported failure
  2. back out of Skills to Techs and confirm the Tech list redraws intact
  3. page between characters in the Status screen
  4. field item Use/Look/Dscd, shop Sell with a large inventory
  5. a battle, to confirm the gate really does exclude it

## Playtest round 2: compaction did NOT fix the Skills page

Reported: (1) Rudy's Skills unchanged; (2) backing out of Skills to Techs is
fine; (3) character switching requires backing out to the member list first,
and works; (4) shop Sell dropped Ceramic Sword and Shadow Blade on page 2
occasionally; (5) battle lists all work, but the Tech page arrow is misaligned.

### (5) fixed: battle Tech page arrow

The battle Tech window is 14 cells wide (`moveq #$E, d1`), so its page arrow
belongs in the last cell at offset $1A. It was still at $16, the last cell of
the 12-wide window it used to be before the Tech list was widened by 2. The
paging GATE read the matching odd byte $17(a2), so paging worked and only the
drawn position was wrong - the pair was self-consistent, just two cells left of
where it should be. Moved both together:

    $FFFF3616/3716/3816 -> $FFFF361A/371A/381A     (the three page buffers)
    cmpi.b #$E6, $17(a2) -> $1B(a2)                (Battle_Tech_Index gate)

The Skill window is 15 wide with its arrow at $1C and gate at $1D, which is
already correct; the item window is 14/$1A/$1B, also correct.

### (1) and (4): why compaction did not fire is not yet known

The savestate supplied (slot_2) is a field/shop state at depth 3, not the
Skills failure, so it cannot answer this. Rather than guess again, the build
now carries compaction telemetry in the spare VWF RAM at $130-$137, cleared on
mode reset and printed by `poolpeak.py`:

    VWFMenu_CompactRuns  $130   times PoolTop actually moved
    VWFMenu_CompactCells $132   cells handed back in total
    VWFMenu_CompactDeny  $134   times the reclaim gate or depth check refused
    VWFMenu_CompactFloor $136   times the floor clamp ended the walk

These separate three failure modes that look identical from outside:
  * runs=0, deny=0      -> compaction never reached its walk
  * deny>0              -> the gate refused (inhibit/blocked/untracked depth)
  * floor>0, cells=0    -> it ran, but the dead tail belongs to an ANCESTOR
                           window rather than the one on top, so the clamp
                           allowed nothing

The third is the live hypothesis. Marks $102 show windows at depth 11 (64),
12 (71) and 13 (71), so the window that actually draws the skill names may be
nested BELOW the Tech window's depth. If so the clamp - deliberately written to
never free an ancestor's cells - is exactly what blocks the reclaim, and the
fix is to widen it in a principled way rather than remove it.

Build `18C8E47709488B9C8C20E4057A37D9A26BEDB5A6A534CD2396E3D88F40A53678`,
all 12 test files pass.

## Telemetry round 1: the floor clamp is the blocker, but not in the expected way

`slot_3` (new build, on the failure) read:

    compaction: 0 runs gave back 0 cells; 3 denied by the gate,
                14 bound by the floor clamp

So compaction is reached and mostly permitted, but PoolTop never moved and the
walk ended AT the floor 14 times. `cells=0` with `floor=14` means PoolTop was
already equal to the floor on entry every time - the walk had nothing to walk.

That does not match the window flow as read from `Window_Create`:

    LoadWindowGroup / BackupTiles / SaveMarkPush / SaveRegion
      -> VWFMenu_Mark            <- compaction hooks here
      -> Window_Draw             <- this window's cells are allocated here
      -> addq.b #1, Windows_Opened_Num

Because Window_Draw runs after Mark, the previous window's allocations are
already counted when the next window is created. Marks 10=37 and 11=64 say 27
cells were allocated between those two creates, so at Mark(11) the floor should
have been 37 against a PoolTop of 64 - a 27-cell gap. The telemetry says that
gap was never there.

Two live explanations, needing different fixes, so round 2 measures rather
than guesses. Added:

    VWFMenu_CompactGap  $138   largest PoolTop-floor gap ever seen
    VWFMenu_CompactBlkd $13A   walks stopped by a LIVE slot (vs by the floor)

  * gap = 27 and blkd > 0  -> the opportunity exists and a live slot ends the
    walk early. The dead tail is real but is not a TAIL: strip pinning keeps
    something live above it. Fix is about pinning, not the clamp.
  * gap = 0 always         -> the marks the clamp reads are not the ones the
    window flow suggests, so the floor is not the previous window's mark in
    practice. Fix is in how the floor is chosen.

Build `F0CA017CFAF8F0EC7EA6ABE99E9B24768C7109144F786101C0B00194221D0178`,
all 12 test files pass.

### Build-tree note

`sourcebuild.py` runs `checkbuild.py` BEFORE `build.bat`, and checkbuild
validates the PREVIOUS build's `ps4built.bin` against `ps4.lst`. An interrupted
build leaves those two inconsistent and every later run then fails inside
checkbuild on a stale-listing symptom that looks like a real invariant
violation - it reported "no-sweep remap entry saves its register frame FAIL"
while the actual fault was an assembler error (`jump distance too big`) in the
new code. Recovery: restore `ps4built.prev.bin` over `ps4built.bin`, assemble
once via `subprocess` (`cmd /c build.bat` from a bash shell only prints the
banner and does nothing), then run `sourcebuild.py` normally.

## Telemetry round 2: the hook was one step too early

`slot_4` (with gap/blocked counters):

    compaction: 0 runs gave back 0 cells; 1 denied, 9 bound by the floor clamp
    largest PoolTop-floor gap seen: 27; walks stopped by a live slot: 4

The 27-cell opportunity DID exist - exactly the Tech list's allocation. The
walk was stopped by a LIVE slot, not by the clamp. `VWFMenu_Compact` sweeps
immediately before walking, so liveness at that instant is plane-derived:
the Tech cells were still on the plane.

Which they are, because `VWFMenu_Mark` runs BEFORE `Window_Draw`:

    BackupTiles / SaveMarkPush / SaveRegion / Mark   <- old window still painted
    Window_Draw                                      <- covering frame lands here
    Windows_Opened_Num++

`Window_Draw` writes the new window's frame into `Plane_A_Buffer` via
`GetPlaneAOffset` and does not draw list text, so immediately after it the
covered window's tiles are gone from the plane and the very same walk succeeds.
So the approach was right and the hook point was wrong.

Fix: `VWFMenu_CompactAfterDraw`, called from `Window_Create` after
`bsr.w Window_Draw`. It runs the walk and then RE-RECORDS this window's mark -
`Windows_Opened_Num` is not incremented until Window_Create returns, so
`Marks[n]` is still this window's entry, and `Release` must roll back to the
compacted PoolTop rather than the pre-compaction one. Without that rewrite the
reclaimed run would be leaked back on close.

`VWFMenu_Mark` no longer calls compaction; the test pins that, pins the
ordering against `Window_Draw` in ps4.asm, and pins the mark rewrite.

Build `A1A579408CDF6B613E795896361C15A89B84E46D96031FEE634FFBE7E988B0EF`,
all 12 test files pass. Expect `CompactRuns > 0` and `CompactCells >= 27` on
the next savestate if this is right.

## Telemetry round 3: compaction at window-create cannot work, and here is why

`slot_5`, with the hook moved after `Window_Draw`, read exactly as before:

    0 runs, 0 cells; gap 27; walks stopped by a live slot: 4

So even after `Window_Draw` the covered window is still live on the plane.
That is because field windows ANIMATE open: `loc_6881E` grows the frame over
several frames (the reason `VWFMenu_RemapRegion_NoSweep` exists at all is that
loc_6881E calls into the remap machinery while animating). `Window_Draw` at
create time paints only the first step, so at NO point during Window_Create is
the window underneath actually covered.

Compaction hooked anywhere inside Window_Create is therefore dead on arrival.
Both hook points are disproven by measurement, not by argument.

### What the numbers actually say

Re-reading the measurements together:

    distinct pool tiles visible on the plane        18
    slots marked live in Refs                       52
    total free                                      24  (19 below PoolTop + 5 above)
    needed for the two dropped names                14
    longest contiguous free run                      5

Capacity is NOT the binding constraint - 24 free against 14 needed. Contiguity
is. And the amplifier is strip pinning: 18 visible cells hold 52 slots live,
because a partially covered name leaves one cell on the plane and `Sweep` must
pin that name's WHOLE run (correctly - see its comment; a half-pinned run lets
a later allocation replace an interior cell while StripEnsure still trusts the
head). The windows below Skills are partially covered, so each contributes one
visible cell and pins a full run, scattering the free space.

That is a property of the pool's own bookkeeping, not of any window's
lifetime, which is why every lifetime-based fix has missed.

### Remaining options, honestly ranked

  b. Scatter-tolerant strips: record a per-cell slot list instead of
     head+count, so the 24 free cells are usable however they lie.  This is
     the only option that addresses the actual constraint.  It touches
     StripOf, StripIdx, Sweep's pinning and RemapRegion - the machinery behind
     both earlier battle regressions - but `VWFMenu_FieldReclaimAllowed`
     already keeps battle out of every reclaim path, which is the guard that
     was missing when those regressions happened.
  c. Cut demand so fragmentation stops biting: draw the status-screen Tech
     list fixed-width.  Frees 27 cells AND removes 7 strips from the pinning
     pool.  Cheap, certain, and consistent with LOOK/DSCD/USE, at the cost of
     VWF on that list.

Option (a) is withdrawn: it was aimed at a tail that does not exist.

`VWFMenu_Compact`/`CompactAfterDraw` and their telemetry are still in the tree
at build A1A57940. They are inert in effect (0 runs) but not free - they sweep
on every window create. If neither (b) nor (c) is pursued immediately, back
them out rather than leave a no-op sweep in the window path.

# VRAM budget: feasibility of reclaiming more menu tiles

Menu font addressing: tile = `$680 + code` (`general/tables/wincharset.asm`).
Codes 1-64 have a SECOND copy at `$7C0 + code`; codes 65-127 do not. That is
the whole reason the pool stops where it does - anything the fixed-width path
draws from codes 1-64 can be served from `$7C0`, freeing `$680+code` for the
pool; codes 65+ have only the one copy.

Current: 76 slots = contiguous `$682-$6C0` (63) + 13 reclaimed.

## 1 + 3. JP punctuation and border+dakuten cells

Hyphen and question mark need no work and carry no risk: they are codes `$31`
and `$33`, inside 1-64, so the fixed path already draws them from `$7F1`/`$7F3`
and `$6B1`/`$6B3` are ALREADY pool. The Shadow Blade description is unaffected.

Unmapped by any charset entry AND unnamed by any source immediate:

    $6D7 $6D8 $6D9 $6DA $6DD $6DE $6E3 $6F7 $6F9      = 9 tiles

NOT free, contrary to first appearance: `$6D3 $6D4 $6D5` are '.', apostrophe
and comma (codes 83-85), and `$6D6` is the code-`$56` charset entry.

Caveat, from menupool.py's own history: absence of a source immediate is not
proof. `$6FF` looked free by exactly this test and was the battle skill
separator, written by computed index. Each of the 9 needs a computed-index
check before it is handed to the pool.

## 2. Lowercase a-h vs i-z

a-h (`$6B9-$6C0`) are ALREADY in the pool - same `$7C0` mechanism. Nothing to
recover there.

i-z plus '.'/'/',' (`$6C1-$6D8`, 24 tiles) are the single biggest block
available, but need a second copy somewhere before `$680+code` can be released.
Free VRAM exists: `$782-$79F` (30) and `$7A1-$7BF` (31) are blank, and both sit
clear of `$700-$76F`, which `VWFMenu_SaveRegion` borrows as record-index
markers. So a 24-tile second bank fits with room to spare.

Scope: upload a second copy of codes 65-88 at font-load time, and make the
fixed-width path use that base for codes >= 65. Bounded, but it touches the
fixed draw path that every menu uses.

## 4. Reordering the pool: NO benefit - do not do this

`VWFMenu_SlotTile` (`vwf/poolslot.bin`) already maps slot -> VRAM tile, and its
comment is literally "the pool is not contiguous". VRAM order is already
decoupled from slot order. Slots themselves are a dense `0..SLOTS-1` index
space, and `StripEnsure` searches for consecutive SLOT indices, never tile ids.
Reordering `poolslot.bin` changes which VRAM tile backs a slot and cannot
change run-finding at all. Fragmentation is dynamic - it depends on which slots
are pinned at runtime - so no static layout helps. This is the largest-scope
idea on the list and its payoff is exactly zero.

## Why capacity IS the right lever after all

Earlier this document concluded "capacity is not the binding constraint,
contiguity is". That is true at the moment of failure but it understated the
remedy. `VWFMenu_StripEnsure_Grow` appends whenever `PoolTop + cells <= SLOTS`,
and the region ABOVE PoolTop is always contiguous. Fragmentation only bites
once PoolTop is near the ceiling and allocation has to fall back to hunting a
dead run below it. Raising SLOTS restores contiguous append space directly.

Rudy's page needs PoolTop 64 + 20 = 84.

    today                  76   fails
    +9 (items 1 and 3)     85   fits, with 1 slot of margin
    +24 (item 2)          109   fits comfortably
    +7 (relocate the excluded immediates $6E0 $6EB $6EC $6EF $6F0 $6F2 $6FF)
                          116

So items 1-3 are worth doing and item 2 is the one that actually settles it.
This is a better answer than option (b) scatter-tolerant strips: same outcome
for the measured failure, no change to strip bookkeeping, and no risk to the
Sweep pinning invariant.

# Pool raised to 83 slots; compaction retired

Baseline for this change is Codex's scatter-tolerant strip build
`D0769EACB31029B6E81C6CBADBCFE433EEC75A10669FDF9A00C7E5DF676A99B2`.

## Retired: VWFMenu_Compact / CompactAfterDraw

Removed from `Window_Create`, `vwfmenu.asm` and the constants, along with the
`$130-$13B` telemetry and `tools/test_compact.py`. Scatter-tolerant strips
supersede it, and it was measured at 0 cells reclaimed while sweeping on every
window create - a cost that only grew once Sweep had to traverse strip chains.

## Reclaimed: 7 katakana tiles, 76 -> 83

    $6D7 $6D8   codes 87/88, inside the old CHROME range but mapped by no
                charset entry.  CHROME narrowed to $6C1-$6D6 (codes 65-86) in
                both menupool.py and checkbuild.py; they now fall in CONTIG.
    $6D9 $6DA $6DD $6DE $6E3   added to CANDIDATES.

`$6F7` and `$6F9` passed the same textual test and are NOT reclaimed. Rendering
the candidates out of savestate VRAM showed them as `/` and `P` - the `$77-$7A`
HP/TP label glyphs the fixed path draws by code, exactly the `$6FF` trap
menupool.py already warns about. Render before trusting a textual scan; the
tooling for it is a dozen lines against `tools/png.py` with VRAM at file offset
`$AD` in a BlastEm state and Plane A at `$C000`.

## RAM layout consequence

`VWFMenu_Refs` is SLOTS bytes at `$500` and had only 76 before Codex's
`StripNext`. Moved `StripNext` `$54C -> $560`; Refs now has 96 bytes of room
and StripNext 160. `checkbuild.py`'s overlap invariant is what catches this -
run it after any SLOTS change.

**Blocker for item 2 (the 24 i-z tiles):** at 107 slots `VWFMenu_StripOf` needs
214 bytes at `$B40` and has exactly 166, and Refs would need 107 against 96.
Both must be relocated before the slot count can rise again. `VWFMenu_Keys`
(8*SLOTS at `$140`, room 960) is fine to 120.

## Tooling trap worth remembering

A mutation test that restores its backup with `mv` keeps the backup's mtime.
When the mutated line is the same length as the original, Python's
`__pycache__` invalidation (mtime + size) does not trip, and later
`import menupool` runs the MUTATED bytecode - which regenerates `poolslot.bin`
wrongly and produces a test failure that contradicts running the same tool
directly. `rm -rf tools/__pycache__` after any such restore.

Build `8F9E28932076088F357C9771B73072B5C7D07BA4CE7AA7E1D5A63ABEC2C123ED`,
all 11 test files pass, all checkbuild invariants hold.

# Item 2 (reclaim i-z, +24 slots): plan and open unknown

## The draw-path change is small and now understood

`VWFMenu_DrawWindowRun` already branches on the code:

    tst.w   d1
    beq.s   .fixed          ; space uses the blank at $680
    cmpi.w  #65, d1
    bcc.s   .fixed          ; codes 65+ live at $680+code
    addi.w  #$13F, d1       ; codes 1-64 use the copy at $7C0
    .fixed: add.w d2, d1    ; d2 = $680

`$13F` maps code 1 -> $7C0 and code 64 -> $7FF. Adding a second bank for codes
65-88 at, say, `$7A1` is the mirror of that: codes 65-88 take
`addi.w #$E0, d1` ($680+65+$E0 = $7A1, $680+88+$E0 = $7B8), codes 89+ keep
`$680+code`. Three sites compute `$680+code` (`ps4.asm` 140212, 308212, 308217)
but only this routine is live in the vwf_menu build.

`$782-$79F` and `$7A1-$7BF` are blank in VRAM and clear of `$700-$76F`, which
`SaveRegion` borrows for record-index markers, so a 24-tile bank fits.

## Open unknown: where the font is uploaded

Not yet located. It is NOT `VWFMenu_FixedArt` - that mechanism is
`VWFMENU_FIXED0 = $681`, `VWFMENU_FIXEDN = 1` (the colon only). The `$7C0`
copy is made by the game's own font loader, which does not appear under any
`winfont`/`MenuFont` name, nor as a literal `$D000`/`$F800` VRAM address or the
matching VDP control longs. Find that before writing any of the above: the
second bank has to be populated the same way the `$7C0` one is.

## RAM relocation required first

At 107 slots two arrays no longer fit:

    VWFMenu_Refs     $500  room  96  needs 107
    VWFMenu_StripOf  $B40  room 166  needs 214

The map tops out at `$BF5` against a 4086-byte ($FF6) quiet region, so ~1KB is
free above it. Move `Refs -> $C00` and `StripOf -> $C80`; `StripNext` ($560,
room 160) and `Keys` ($140, room 960 vs 8*107=856) both still fit, so only two
constants change. `checkbuild.py`'s overlap and quiet-region invariants verify
this - run it after any SLOTS change.

## Current ceiling is one slot

Field item list, 8 items plus 5 party names, measured with `menustrip.compose`:

    Graphite Suit 8  Ceramic Shield 9  Cure Paralysis 9  Moon Atomizer 9
    Titanium Axe  8  Wood Cane      6  Ceramic Sword  9  Shadow Blade   8
    items 66 + party names 16 = 82 of 83

At the old 76 slots the first seven (74) fit and Shadow Blade did not - which
is exactly the reported symptom, and confirms the player was still running a
pre-83 build. 83 covers this list by one slot; item 2 is what turns that into
real headroom.

# Item 2 done: pool 83 -> 105

## The measurement that set the target

`slot_6`, taken on the field item list with the 83-slot build:

    live now 79   peak 79   (VRAM holds 83)
    window marks: 0 0 16 16 62 0 0 ...

Seven items consumed 63 cells (79 minus the 16-cell baseline) where
`menustrip.compose` predicted 58. Shadow Blade needs 8, so the real demand is
87 against 83 - short by 4. The earlier "82 of 83, it will just fit" claim came
from `compose()` alone and was wrong by 5 cells; every pool figure that has
held up this session came from a savestate, and that one did not.

## What changed

`ArtNem_Font` decompresses to 87 tiles - codes 1-87 - and the art table loads
it twice, at `$681` and at `$7C0`. The `$7C0` copy is why codes 1-64 can be
served by the fixed path while `$680+code` belongs to the pool. Codes 65-86 had
no second copy, which is what locked `$6C1-$6D6` out.

  * `tools/menulower.py` extracts codes 65-86 from `Font.bin` and re-compresses
    them with `nemcmp` (asserting a decomp round-trip) into
    `general/art/nemesis/FontLower.bin` - 22 tiles, 189 bytes.
  * Both art tables gained `dc.w $07A1 / dc.l ArtNem_FontLower`, so the codes
    are reloaded at `$7A1-$7B6`. That range is blank in VRAM and clear of
    `$700-$76F`, which `SaveRegion` borrows as record-index markers.
  * `VWFMenu_DrawWindowRun` now maps codes 1-64 to `$7C0` (`+$13F`), 65-86 to
    `$7A1` (`+$E0`), and 87+ to `$680+code`.
  * `CHROME` is empty, so `$6C1-$6D6` joins the pool. 105 slots, 18 spare
    against the measured 87.

Note code 88 has no stock art at all - `Font.bin` stops at 87 - so `$6D8` was
already free and is unrelated to this.

## RAM relayout

`VWFMenu_SaveStack` is 10 bytes per slot, so at 105 it ran from `$800` to
`$C19` and straight over the battle fields. The map now leaves every sized
array room through SLOTS=120:

    Keys      $140   8*S      Refs      $500   S
    StripNext $580   S        SaveStack $800  10*S
    StripOf   $CB0   2*S      battle fields $DA0-$DAE

`checkbuild.py`'s overlap and quiet-region invariants are what caught this;
run it after any SLOTS change.

## Tests: four failed, all correctly

`test_strip`, `test_battle_text_lifetime`, `test_itemtext` and
`test_battle_tech_layout` hardcoded RAM offsets (`$B40`, `$BE8`, `$BEE-$BF4`)
or spelled out instruction bytes containing them; `test_fieldtext` computed the
old two-way code mapping. All now derive from `ps4.constants.asm` - including
the `rollback` instruction in `test_battle_tech_layout`, which encodes two RAM
addresses - so the next SLOTS change moves them automatically instead of
failing spuriously.

The chrome invariant in `checkbuild.py` was replaced rather than deleted: if
the pool contains `$6C1-$6D6` it now REQUIRES the `FontLower` art-table entry
and the `$7A1` mapping in `DrawWindowRun`. Losing either half would turn every
lowercase letter in a party name into whatever the pool last wrote there.

Also deleted the stale `VWFMENU_VRAM` paragraph, which described a
"slots at or above VWFMENU_VRAM draw blank" cap that no constant implements -
it reads exactly like an explanation for a missing name and is not one.

Build `0E36DA05E9751BFF4A27EC943ACF90BAA19CF288B09724CE5BFDF8AC00AEC8B8`,
all 11 test files pass, all checkbuild invariants hold. NOT verified in play.

## Regression after item 2: the mapping lived in TWO routines

Playtest: menus themselves drew correctly, but closing one produced corruption.

`VWFMenu_DrawWindowRun` is not the only place that turns a charset code into a
tile. `VWFMenu_DrawString_Label` - the chrome/label path, reached for anything
that is not a name-table entry - carried its own copy:

    cmpi.w  #65, d1
    bcc.s   VWFMenu_DrawString_LabelCell   ; 65-127 already sit at $680+code
    addi.w  #$13F, d1

Only the first site was updated, so every chrome label containing a lowercase
i-z, '.', "'" or ',' still drew from `$6C1-$6D6` - which item 2 had just handed
to the tile pool. The menus themselves looked right because their list text
goes through the strip/compose paths; the damage showed on close, when the
reveal redraws chrome through the label path.

The battle site at `ps4.asm` ~308212 is fine: its `addi.w #$680, d2` only
builds the base-plus-attribute that it hands to `VWFMenu_DrawString`, so it
inherits whichever mapping that routine uses.

Fixed by giving the label path the same three-way split, and by tightening the
checkbuild invariant from "DrawWindowRun has the $7A1 leg" to "every site with
a `#$13F` leg also has an `#$E0` leg, and there are at least two". Mutation
tested: blanking either `#$E0` makes it FAIL.

Lesson for the next mapping change: `grep '$13F'` across `vwfmenu.asm` before
assuming there is one code-to-tile site. There were two.

Build `49E1C53940C9FE81A4187AEFDA1B75E8156A83D65A812A0E239968E311CD5523`,
all 11 test files pass, all checkbuild invariants hold.

# Item 2 REVERTED: there is no free VRAM in the window bank

The `$7A1` second copy corrupted the field map and blanked chrome labels.
Cause, read straight out of `slot_7`'s VRAM:

    $E000  tile $700   Plane B nametable      01 0a 01 0b 01 0c ...
    $F000  tile $780   sprite attribute table links 1,2,3,4 ascending
    $F400  tile $7A0   hscroll table          fe 08 fe 08 00 00 ...
    $F800  tile $7C0   the codes 1-64 font copy

`FontLower.bin` was written into the HSCROLL TABLE. That is both symptoms at
once: font art appearing as map tiles, and labels drawn from `$7A1` reading
scroll values as glyphs.

The premise was wrong. `$782-$79F` and `$7A1-$7BF` looked blank in ten
savestates, but those are zeroed VDP table entries, not unused tile art -
and the two field states already showed 22 fewer blanks than the menu states,
which was the tell. This is exactly the `$6FF` mistake that `menupool.py` warns
about in its own comments: absence of evidence in a savestate is not evidence
a tile is free. The art-table scan agreed with the wrong answer because map
tilesets do not load through those tables at all.

Reverted: pool back to 83, both code-to-tile mappings back to the two-way form,
`FontLower` binclude and both art-table entries removed, `FontLower.bin`
deleted, `CHROME` restored to `$6C1-$6D6`, `test_fieldtext` expectation
restored. `tools/menulower.py` is kept but PARKED, with the VRAM map above in
its docstring so the idea is not retried blind.

Kept from the attempt, because both are improvements regardless:

  * the RAM relayout (every sized array has room through SLOTS=120);
  * the tests now derive RAM offsets from `ps4.constants.asm` instead of
    hardcoding them, including the `rollback` instruction bytes in
    `test_battle_tech_layout`;
  * `checkbuild.py`'s chrome invariant is now conditional - it asserts
    disjointness while `$6C1-$6D6` are chrome, and if they are ever handed to
    the pool it instead REQUIRES a second copy plus the mapping on every
    fixed-width path (there are two, not one).

Build `4BED540E86CB76FA50AE474441619E708B3096A991A45FAFAC8A396198007EB3`,
all 11 test files pass, all checkbuild invariants hold. This is the 83-slot
build with the two-routine label fix, i.e. the last known-good behaviour plus
the katakana reclaim.

## Where capacity can still come from

Measured need is 87 (field item list, 8 items + party names). 83 is 4 short.

  * Codes 37-48 and 53-56 are mapped by no charset entry, so their tiles in
    the `$7C0` bank - `$7E4-$7EF` and `$7F4-$7F7`, 16 tiles - are unused. They
    cannot be reached today because `poolslot.bin` stores a BYTE offset from
    `$680` and `$7E4-$680` exceeds 255. Widening `VWFMenu_SlotTile` to word
    offsets reaches them: +16, giving 99. Six lookup sites use `move.b` on it.
  * Reducing demand: the eight visible item names cost 66 cells by
    `menustrip.compose` and 63 were measured for seven of them, so shortening
    two or three names buys the same 4 cells with no code change.

# Open bug: a closed field window is left on Plane A

Confirmed against `work/field-leftover-window.state` (saved on build
`4BED540E`; `$7A1` is blank and the hscroll table at `$F400` is intact, so the
FontLower damage is genuinely gone).

After closing a field menu, Plane A still holds 105 window-bank cells:

    rows 0-12, cols 25-36   frame tiles $6E9 $6EA $6F3 $6F7
    12 further cells        pool tiles $682-$68D

Plane A is the overlay - elsewhere it is 100 cells of `$680`, the blank - and
the map is on Plane B, which is why the leftovers appear painted over terrain.
The visible "6"s are those 12 pool cells: PoolTop rolled back to 0 on close, the
slots were handed to whatever drew next, and the stale plane cells now display
that new art. The digits are incidental; the cells are simply not being erased.

This is NOT the FontLower fault and NOT the katakana reclaim: slots 0-11 map to
`$682-$68D` under the 76-, 83- and 105-slot pools alike, so the tile numbers are
unchanged by any of that work. `slot_7`, also a field state, has ZERO
window-bank cells on Plane A, so the leak is intermittent rather than universal
- something about how that particular menu was dismissed.

Likely the same defect as the "little repainting when paging back" already
logged at D-priority; it is more visible over terrain than over another window.

Where to look: `Window_Destroy`'s restore of `Win_Saved_Plane_Maps` (the
backed-up cells) versus `VWFMenu_RemapRegion`. `RemapCell` rewrites a marker
cell to `SlotTile[slot]+$680` via `VWFMenu_RemapCell_Point`, so a cell that
should have been restored to map content but is still carrying a `$700-$76F`
marker would come back as a pool tile exactly like these. Worth checking
whether the backup restore and the remap can both claim the same cells, and
what happens when a window is dismissed by a path that skips one of them.

Not investigated further this session - it is a distinct defect from the pool
capacity work and deserves its own reproduction (which menu, dismissed how).

## Prime suspect for the leftover window: the katakana reclaim overrode better evidence

Repro (user): launch, load save, open party menu (A), close it (B / S on
keyboard). Leftover window on Plane A over the terrain.

`menupool.py` states where its candidate list came from:

    # Candidates: unreferenced across the savestate sweep.  That evidence alone
    # is NOT sufficient - a savestate can only show what happened to be on
    # screen in it ...

The original list starts at `$6DB`. `$6D9`, `$6DA`, `$6DD`, `$6DE` and `$6E3`
were deliberately NOT in it - the sweep had found them REFERENCED. This session
added exactly those five, plus `$6D7`/`$6D8` by narrowing CHROME, on the
strength of "mapped by no charset entry and named by no code immediate".

That is the weaker test, and in the wrong direction. The sweep is positive
evidence a tile is in use; "nothing names it literally" only proves no literal
names it, and frame art is reached by computed index - which is the failure
mode the comment right above the list warns about, and the same one that caught
`$6FF`, `$6F7` and `$6F9` earlier.

Layout note that makes this concrete: `ArtNem_WindowTiles` loads at `$680` and
`ArtNem_Font` (87 tiles) is loaded over `$681-$6D7`, so everything from `$6D8`
up is surviving WindowTiles art - frame pieces and leftover kana in the same
blob. Rendering a tile as kana therefore does NOT prove it is a dead glyph;
it only proves Font did not overwrite it.

Bisect build `F142D0FC5CF7E882AB99E97B8BE6E4A1ABFC23E6D85139D68175A361532FD487`
backs all seven out: pool 76, CHROME `$6C1-$6D8`, CANDIDATES from `$6DB`. This
is Codex's scatter-tolerant strip work plus the RAM relayout and the test
derivations, with none of this session's tile reclaim.

  * leftover window GONE  -> the reclaim caused it; the seven tiles are in use
    and the savestate sweep was right. Capacity must come from the $7C0 bank
    (codes 37-48 / 53-56, needs word-width poolslot) instead.
  * leftover window STAYS -> the reclaim is exonerated and the defect is in the
    close path itself (`Window_Destroy` -> `loc_6881E` -> `RemapRegion`),
    predating this session's work.

All 11 test files pass on the bisect build.

## Cause found: the RAM relayout ran through the window tile backups

The leftover window survived the bisect build, so the katakana reclaim was NOT
the cause. The cause was this session's RAM relayout, done for item 2 and left
in place after item 2 was reverted.

`Window_Create` seeds `Win_Saved_Plane_Maps_End` with `#$6040`, so the window
tile backups start at `$FFFF6040` = `VWF_RAM_Base+$C40`. That is the real
ceiling for the VWF block. The relayout put `VWFMenu_StripOf` at `$CB0` and the
battle marks at `$DA0-$DAE`, both past it, straight through the saved plane
maps. `Window_Destroy` then restored garbage, so the window was never erased -
which is exactly the reported repro (open party menu, close it, leftovers over
the terrain).

Visible in the savestates: at `VWF+$DA0`, `slot_6` (pre-relayout) holds
`00 10 00 10 ...` while `slot_9` (post-relayout) holds `20 71 20 72 20 73 ...`
- consecutive tile ids with attributes, i.e. plane map data being overwritten.

`checkbuild.py` did not catch it because its ceiling was wrong: it asserted the
map fits a "4086-byte quiet region", which is 1078 bytes past `$C40`. Corrected
to `$C40` and tied to the `#$6040` seed, with a second check that the seed still
says `$6040` so the two cannot drift apart. Mutation tested: putting `StripOf`
back at `$CB0` now FAILS.

Reverted to the original addresses (`Refs $500`, `StripNext $54C`,
`StripOf $B40`, battle marks `$BE6-$BF4`).

Consequence for future capacity work: there is NO room to grow the sized arrays
in place. `Keys` (8*S), `Refs` (S), `StripNext` (S), `SaveStack` (10*S) and
`StripOf` (2*S) already fill `$140-$BF5` against a `$C40` ceiling, so raising
VWFMENU_SLOTS at all requires finding space, not just moving fields up. At 76
slots the block ends at `$BF5`, leaving 75 bytes - about 5 more slots' worth of
`SaveStack` alone. Any real increase needs a different home for one of the big
arrays, and `$C40` is a hard wall.

Build `34AD3CB8D8AF0065AC52486D1BB8F208FCDD48869DEB02A3D73EAB2A1E631CAC`:
Codex's scatter-tolerant strips, original RAM layout, pool 76, plus the test
derivations and the corrected ceiling. No tile reclaim from this session.

# Tile reclamation: where it actually stands

## RAM is not the blocker; the block is full of padding

At 76 slots the VWF block tops out at `$BF6` against the `$C40` ceiling - 74
bytes spare, 3 slots' worth at 22 bytes/slot (Keys 8, Refs 1, StripNext 1,
SaveStack 10, StripOf 2; `VWFMENU_SAVEN = VWFMENU_SLOTS`).

But the block carries 972 bytes of internal padding:

    after Keys        $3A0..$4FF   352
    after SaveMark    $732..$7FF   206
    after StripNext   $598..$5FF   104
    after SaveStack   $AF8..$B3F    72
    after DirtySpan   $086..$0FF   122   (+ five smaller)

Repacking it tightly fits well over 100 slots without moving anything outside
`$140-$C40`. So RAM stops being the constraint the moment it is repacked, and
no hunt for free work RAM is needed - which is just as well, given that
"unnamed and unchanging across savestates" is the same weak evidence that has
misfired three times today.

## Tiles ARE the blocker: 8, not 16

The `$7C0` bank duplicates looked like 16 free tiles by charset evidence (codes
37-48 and 53-56 are mapped by no `wincharset.asm` entry). Sweeping every plane
in all 10 savestates says otherwise:

    $7E4 $7E5 $7E6 $7E7 $7E8 $7E9 $7EA $7EB   referenced 2-52 times each
    $7EC $7ED $7EE $7EF $7F4 $7F5 $7F6 $7F7   never referenced

Codes 37-44 are drawn by something that does not go through the charset. Only
codes 45-48 and 53-56 are free: **8 tiles**, giving 84 slots.

Reaching them still needs `poolslot.bin` widened from byte to word offsets
(`$7EC-$680` = 364), touching `VWFMenu_SlotTile` and its six `move.b` lookups.

## 84 does not clear the measured 87

The field item list measured 79 used with seven items plus a 16-cell party-name
baseline; Shadow Blade needs 8, so 87. 84 is three short, and an inventory only
grows. Tile reclamation alone cannot settle this - the window bank is simply
full, and every remaining candidate has now been checked.

Demand side is the honest complement: the eight visible item names cost 66
cells. Shortening the three longest by a character or two each frees the
remaining margin at zero risk to VRAM or RAM.

# Tile verdict: 12 safe now, 4 more with a code change

User identified candidates visually by glyph (dakuten/handakuten composites,
kuten, touten, nakaguro) - evidence a symbol scan cannot produce. Cross-checked
each against: presence on either plane across 10 savestates, code immediates,
charset mapping, and what the referencing code actually does.

SAFE NOW (12), none seen on any plane in any state:

    $681  the first 'A'   codes 1-64 are served from the $7C0 copy, so this is
                          redundant.  VWFMENU_FIXED0/FIXEDN reserve it but
                          nothing reads VWFMenu_FixedArt/FixedMap - vestigial.
    $6D6  nakaguro        charset code $56; zero occurrences in every generated
                          name table, and a JP punctuation mark besides.
    $6EB $6EC             frame+dakuten composites, WRITTEN only by the JP
                          voicing path (loc_27DBD8/loc_27DBF4) and compared
                          nowhere.  That path fires on control codes $F0/$F1,
                          which appear zero times in any name table.
    $7EC $7ED $7EE $7EF   $7EE/$7EF are the standalone dakuten/handakuten, same
    $7F4 $7F5 $7F6 $7F7   dead path; the rest are unmapped by the charset.
                          $7F4's `move.w #$7F4, (a1)` after LoadBattleObject
                          writes an object TYPE field, not a tile - the false
                          positive menupool.py already warns about.

NEEDS A CODE CHANGE FIRST (4): `$6EF $6F0 $6F1 $6F2`

These are not merely written - they are READ BACK from the plane and matched:
`cmpi.w #$6F1, d7` after `andi.w #$7FF` (ps4.asm 140317, 140361) and
`cmpi.w #$E6EF, (a1)` in loc_27DC1E, which REWRITES matching cells to $E19B.
Hand them to the pool and an ordinary pool cell would match and be rewritten.
Neutralise those dead JP branches first, then they are free too: 92 total.

## Consequence

76 + 12 = 88, which clears the measured 87 with one to spare.

Two prerequisites, both understood:

  1. `poolslot.bin` holds a BYTE offset from $680, so $7EC-$7F7 are
     unreachable ($7EC-$680 = 364).  Widen `VWFMenu_SlotTile` to word offsets;
     six `move.b` lookup sites.
  2. At 88 slots the block needs 264 bytes more than at 76 and would top out
     past the $C40 ceiling.  The 972 bytes of internal padding covers it - a
     repack, not a relocation, and nothing leaves $140-$C40.

# Stages 1+2 landed: RAM repack and word-wide SlotTile

Build `2232743EA46B366FBE7230C5827C023B3A82BB8FEB44E81D0CA3646BDF2CBAA4`.
No behavioural change intended - `VWFMENU_SLOTS` is still 76 and no tile has
moved. This is the plumbing for stage 3.

## Repack

The block was carrying 972 bytes of padding. Relaid tightly from `$140`, sized
for 112 slots so a later slot bump needs no further moves:

    $140 Keys      $4C0 Refs      $530 StripNext   $5A0 StripOf
    $680 SaveStack $AE0 Scratch   $BE8 SaveTop     $BEA SaveMark
    $C0A..$C18 the eight small battle/strip words

Ends at `$C1A` against the `$C40` ceiling - 38 bytes spare, and nothing leaves
`$140-$C40`. The layout is computed in one pass rather than hand-placed, and
every field is word-aligned. `$100-$13F` (PoolTop, Marks, Peak and the flags)
is deliberately unchanged because `tools/poolpeak.py` addresses it directly.

## Word-wide SlotTile

`poolslot.bin` now holds a WORD offset from `$680` per slot (152 bytes for 76
slots), because `$7EC-$680` = 364 does not fit in a byte. All six lookups
became `move.w` on a doubled index.

`VWFMenu_TileSlot`, the reverse table, was guarded by `cmpi.w #128, d0`, which
would have made any tile above `$6FF` invisible to `VWFMenu_Sweep` and
`VWFMenu_SaveRegion` - reclaimed tiles would never have been marked live. Now
`VWFMENU_TILESPAN = 384`, asserted in `menupool.py` and checked against the
pool in `checkbuild.py`.

## Guards added

  * `no move.b reads VWFMenu_SlotTile` - a missed lookup site would read half
    an offset and point at the wrong tile, the same shape as the code-to-tile
    mapping that once lived in two routines and was fixed in only one.
    Mutation tested: reverting one site to `move.b` FAILS the build.
  * `TileSlot reach covers every pool tile`.
  * `pool size matches VWFMENU_SLOTS` now expects `SLOTS * 2` bytes.

Four tests failed on this change and all four were right to: `test_menupool`
(byte count), `test_reveal` (hardcoded SaveStack address), `test_strip` and
`test_itemtext` (byte-wide `poolslot` reads and a hardcoded `Refs`). All now
derive from `ps4.constants.asm`, so stage 3 moves them automatically.

All 11 test files pass, all checkbuild invariants hold.

## Correction: the VWF ceiling is $C00, not $C40

Build `2232743E` (stages 1+2, first attempt) caused severe artifacting when
paging back through the item list. Cause: the repack ran the last eight fields
from `$C0A` to `$C1A`, i.e. `$FFFF600A-$FFFF601A`, on top of the game's own
buffers.

`ps4.asm` names them literally - `lea ($FFFF6020).l`, `($FFFF6060).l`,
`($FFFF60A0).l`, `($FFFF60C0).l`, `($FFFF60E0).l`, `($FFFF6100).l` and more, all
on `$20` boundaries from `$FFFF6000`. So the wall is `VWF_RAM_Base+$C00`, which
is exactly where the original layout stopped (`$BF6`). `$6040`, the
`Win_Saved_Plane_Maps_End` seed, is 64 bytes ABOVE the real boundary - deriving
the ceiling from it was wrong twice over, once too generous at 4086 and once
still too generous at `$C40`.

Refitted at `$C00` with a 96-slot target: block ends `$ABA`, 326 bytes spare.

Two independent invariants now, because a ceiling is only as good as its
justification:

  * `RAM map fits below the game buffers at VWF+$C00`
  * `no VWF field collides with a literal address in ps4.asm` - scans every
    `$FFFFxxxx` literal in the source and intersects it with every VWF field.
    This one needs no knowledge of which buffer starts where.

Both mutation tested: moving a field back to `$C20` FAILS both.

Also widened `bmi.s VWFMenu_DrawString_Full` to `bmi.w`; the six lookup sites
each grew by an instruction and pushed it out of short-branch range.

Note the `moveq #0` restored at the six sites was hygiene, not the fix - every
one of the six results is consumed as a word, and
`LoadVRAMAddressFromTileNumber` uses only `d0.w`. Keeping it because the byte
form cleared the whole register for free and a future caller might rely on it.

Build `AFD5B48C4FA732DC9A199FC7C7B10FE061D6488C0423409BD0F45400A90195FB`,
all 11 test files pass, all invariants hold.

# Item-name budget: measured

A page shows 8 consecutive inventory entries and inventory order shifts with
acquisition, so the binding case is the 8 WIDEST names co-occurring, not the
average across all 156.

    worst page today                              77 cells
    worst page with every space closed up         75 cells
    budget at 92 slots (12 tiles + 4 voicing)     72   -> 3 cells still to find
    budget at 88 slots (12 tiles only)            68   -> 7 cells still to find

Party overhead confirmed at 19-20: the five widest character names
(Thray/Shess/Frena/Forren 4 each, Siam/Rudy 3) sum to 19.

Closing spaces saves 1 cell each on seven names (Zirconium Armor, Composite
Armor, Zirconium Gear, Titanium Slicer, Titanium Shield, Termi Pennant, Plasma
Dagger) but only moves the worst page by 2, because the top of the list is a
wall of 9s and 10s.

The three names that set the ceiling, none of which a space closure helps:

    StealthCanceler  10    (no space to remove)
    CarvedSandworm   10    (no space to remove)
    Plasma Launcher  10 -> PlasmaLauncher is still 10

Eighteen further names sit at exactly 9 after closure, so reaching 72 needs the
top 8 to average exactly 9 - the three 10s down to 9 and nothing else changed.
That is a budget with zero slack; trimming a few 9s to 8 buys margin for future
inventory.

Reaching 68 (without the voicing tiles) needs an average of 8.5 across the top
8, which would mean renaming well beyond the three. That is the argument for
doing the voicing-tile code change rather than stopping at 12 tiles.

## Party overhead is 17, not 20

The status panel shows five members, so the overhead is the widest party the
story permits - not the five widest names. Constraints supplied by the player:

    pairs   Laila|Forren, Shess|Pyke, Shess|Hahn, Shess|Frena, Frena|Hahn
    Siam    only ever travels with Fal, Thray, Forren, Rudy
    trios   Forren never with (Frena+Pyke), (Frena+Raja), or (Raja+Shess)

Name widths: Thray/Frena/Forren/Shess 4, Rudy/Laila/Hahn/Pyke/Raja/Siam 3,
Fal 2. Of 462 five-member combinations, 59 are legal and the widest is 17
cells, with 11 parties tied. No single further exclusion lowers it - no pair is
common to all 11 - so 17 is the floor from party composition.

Worth noting the naive figure was 19 and the pairwise-only figure 18; the trios
are what removed the last cell, and the Siam constraint changed nothing because
Raja substitutes at the same width.

## Resulting item budget, against a worst page of 75 after space closure

    88 slots (the 12 safe tiles)   budget 71   -> 4 cells to find
    92 slots (plus the 4 voicing)  budget 75   -> fits today, zero margin

Recommendation: 88 slots plus renaming. It avoids `$6EF-$6F2` entirely - the
four tiles that are read back off the plane and rewritten - and 4 cells is
within reach of the three 10-cell names alone. Trim further than 4 for margin;
92-with-no-renames fits only the current inventory and leaves nothing for a
later item.

# Stage 3 phase 1: 12 tiles, pool 76 -> 88

Build `6747870EF325751068FD4EDB5DC26F53D13D4257EE58FF3358BFEEB551D9E16F`.

    EXTRA = $681 $6D6 $6EB $6EC $7EC $7ED $7EE $7EF $7F4 $7F5 $7F6 $7F7

Appended after CONTIG and SCATTERED so the first 76 slots keep the tiles they
already had - this is an addition, not a remapping.

`$6EB`/`$6EC` are named by a code immediate and taken anyway, so the bypass is
gated rather than assumed: `menupool.py` asserts no name table carries a `$F0`
or `$F1` voicing control code, which is the only way that path is reached. If
one ever appears, generation fails instead of the playtest.

`$6EF-$6F2` are deliberately still excluded. Unlike `$6EB`/`$6EC` they are read
BACK off the plane and compared (`cmpi.w #$6F1, d7` after masking; `cmpi.w
#$E6EF, (a1)` in `loc_27DC1E`, which rewrites matches). A pool cell landing on
those numbers would be clobbered. They are phase 2, after the stale comparisons
are neutralised.

Invariants adjusted rather than relaxed:

  * chrome range narrowed to `$6C1-$6D5`, since `$6D6` is the nakaguro, not
    lowercase; a separate check requires that no name table emits charset `$56`
    while `$6D6` is in the pool.
  * `test_menupool` now asserts EXTRA is gated on the voicing path being
    unreachable, and that no EXTRA tile is one the code reads back.

## Expected effect

The reported failure was the field item page 2: eight items totalling 66 cells
plus a 17-cell party panel = 83, against 76 slots. `slot_1` confirms it -
saturated at 76 with the reclaim gate ALLOWED and nothing left to free.

88 covers 83 with 5 to spare, so Shadowblade should now paint and Ceramic Sword
should stop being intermittent. The intermittency was never a race: at 76 the
pool was exactly at its limit, and whether a name fitted depended on how much
the sweep could reclaim at that instant, which varies with what is still
visible on the plane.

All 11 test files pass, all invariants hold. Not verified in play.

# Stage 3 phase 2: pool 88 -> 92, all sixteen tiles

Build `36DCF01A44E7C0C6D83AF45516F9DB12373C5F7A74CAB211C273FE14F4904AC2`.

Phase 1 (88 slots) verified in play. Its savestate read SATURATED at 88, so the
extra four are not decorative - the field item list was still sitting exactly
on the ceiling.

## The four held-back tiles

`$6EF $6F0 $6F1 $6F2` were the frame+voicing composites the code READ BACK off
the plane. Three sites are now compiled out under `vwf_menu_strips`:

    ps4.asm ~140317   cmpi.w #$6F1, d7 / bne  -> bra, keeping the $6EA test
    ps4.asm ~140361   cmpi.w #$6F2, d7 / bne  -> bra, keeping the $6EA test
    loc_27DC1E        early rts; it scanned the previous row for $E6EF/$E6F0/
                      $E6F1/$E6F2 and REWROTE matches to $E19B-$E19E

The `$6EA` comparisons beside the first two are left alone: `$6EA` is a live
frame tile, not a voicing composite. `loc_27DC1E` returns before its `movem`,
so no register state changes and the caller is unaffected.

Nothing writes those tiles any more - the path that did fires only on control
codes `$F0`/`$F1`, which appear in no name table.

## Gated from both sides

`menupool.py` refuses to generate if any of the three neutralisation markers is
missing from `ps4.asm`, and `test_menupool.py` pins the same three from the
other direction. Mutation tested: deleting one marker fails generation with
"a voicing comparison is still live; $6EF-$6F2 are unsafe".

Exclusion set is now just `$6E0` (reached by `addi.w #$6E0`) and `$6FF` (the
battle skill separator).

## Budget

    pool                                92
    widest legal party                  17
    item budget                         75
    worst page today                    77   -> 2 cells over
    worst page with spaces closed       75   -> exactly fits

The seven space closures (Zirconium Armor, Composite Armor, Zirconium Gear,
Titanium Slicer, Titanium Shield, Termi Pennant, Plasma Dagger) change no
name's meaning and are what brings 77 to 75.

All 11 test files pass, all invariants hold. Not verified in play.

# Assessed: switching item names from strips to per-cell composition

Asked whether the larger tile budget makes per-cell replacement worth revisiting.
Assessment: real benefit, but NOT now.

## It is a flag, but `=0` is not a complete configuration

`vwf_menu_strips` (ps4.options.asm) already routes names either way:

    if vwf_menu_strips=1
    bcs.w VWFMenu_DrawStrip        ; a name: it has a prerendered strip
    else
    bcs.w VWFMenu_DrawString_Compose ; a name: it needs the pool

But there are 32 guards across vwfmenu.asm and ps4.asm and most have no `else`.
Setting `=0` today would silently drop `Battle_ItemPageRender` and restore the
voicing comparisons - while `menupool.py` keeps `$6EF-$6F2` in the pool, since
EXTRA does not consult the flag. So `=0` is a fallback that no longer builds a
correct ROM, not a maintained alternative.

LATENT TRAP worth fixing when convenient: the voicing neutralisation is guarded
by `vwf_menu_strips=1`, but the JP path is dead regardless of strips. It should
be unconditional. Harmless while the flag is 1; deliberately not changed today
because a playtest of `36DCF01A` was in progress.

## What it would buy

  * Dedup, measured on the reported pages: page 2 66 -> 55 cells, page 3
    57 -> 49, roughly 17%.  Savings concentrate on shared prefixes - Titanium,
    Ceramic, Graphite, Laconia, Guardian - i.e. exactly where the pressure is.
  * Removes whole-run pinning, the documented fragmentation amplifier: 18
    visible cells held 52 slots live, which is what starved Rudy's Skills page.
  * Deletes StripOf/StripNext/StripIdx/StripEnsure and the strip halves of
    Sweep, SaveRegion and RemapCell.
  * Would likely remove the need to shorten any item name.

## What it would cost

  * Strips are PRERENDERED - that is their stated rationale in the source.
    Drawing a name would become per-cell composition plus a dedup search at
    runtime instead of a bulk upload of prebuilt tiles.  Battle redraws these
    lists often and the frame cost is unmeasured; frame loss has been observed
    once already this session from an unrelated change.
  * Every path that has misfired this session is in scope.
  * The missing `else` branches would have to be written first.

## Verdict

No. The budget fits at 92 with space closures that change no name's meaning.
The decisive point is that per-cell was tried and abandoned before this session
and the reasons are not recorded anywhere in the tree - overriding a decision
whose rationale cannot be reconstructed is the same error that took `$6D9`,
`$6DA`, `$6DD`, `$6DE` and `$6E3` on weaker evidence than the sweep that had
already rejected them.

Revisit if the budget tightens again: dedup is the only lever that scales, and
it improves as names cluster. The cheap first step is a measurement, not a
commitment - write the missing `else` branches, build `=0`, and read PoolTop
off the same savestate.

# Seven space closures applied

Build `4E42AAEBDA8C6E22C7F721B07ED98895AD0764E4F0A60B0347C2FB6E956DB95E`.

    Zirconium Armor  10 -> ZirconiumArmor   9
    Composite Armor  10 -> CompositeArmor   9
    Zirconium Gear    9 -> ZirconiumGear    8
    Titanium Slicer   9 -> TitaniumSlicer   8
    Titanium Shield   9 -> TitaniumShield   8
    Termi Pennant     9 -> TermiPennant     8
    Plasma Dagger     9 -> PlasmaDagger     8

Each occurs exactly once and only in segment `00:001`, the menu item-name
table, so no prose was touched.

## Measured

    worst page (8 widest co-occurring)   75 cells
    widest legal party                   17
    92 slots -> budget 75                FITS, 0 spare
    88 slots -> budget 71                over by 4

    reported page 2   66 + 17 = 83   ->  9 spare
    reported page 3   56 + 17 = 73   -> 19 spare

The three names still at 10 cells set the ceiling: `StealthCanceler`,
`Plasma Launcher`, `CarvedSandworm`. Bringing any one of them to 9 buys the
first cell of margin; all three would give 3.

Zero spare at the theoretical worst page is safe only because the item set is
complete - no new item name can appear. It does mean any future rename that
lengthens a top-8 name breaks it, so `tools/` should keep the measurement handy:
the worst page is the sum of the 8 widest names by `menustrip.compose`, and the
budget is 92 minus 17.

All 11 test files pass, all invariants hold.

# Regression: $7EC/$7ED were the small 8 and 9

Reported: Rudy's HP rendered as garbage once it contained an 8 or 9.

The `$7C0` bank holds TWO complete digit runs - `$7DA-$7E3` (normal) and
`$7E4-$7ED` (the small/bold set used for HP and TP). The plane sweep found
`$7E4-$7EB` referenced, i.e. digits 0 through 7, and `$7EC`/`$7ED` unreferenced
across ten savestates simply because none of them showed an 8 or a 9 in a
small-numeral field. Those two were taken. The player had flagged the risk.

A contiguous glyph RUN is all-or-nothing. Siblings being referenced is proof the
whole run is live, whatever a sample shows - and "digits 0-7 are used, 8 and 9
are free" should have been self-evidently impossible. This is the third time
absence-from-savestates has misled this work, after `$6FF` and the `$6D9` group.

Removed `$7EC $7ED` and, on the same principle, `$7F6 $7F7` - rendering the bank
out of a pre-change savestate shows `$7F7` is the text-continue arrow. Kept only
the four the render positively identifies as Japanese punctuation: `$7EE`/`$7EF`
(dakuten/handakuten) and `$7F4`/`$7F5` (kuten/touten).

`menupool.py` now asserts EXTRA takes nothing from `$7DA-$7ED` or `$7F6/$7F7`,
with the reasoning inline, so the run cannot be broken into again.

Pool is 88. Build `D2C3C807A8BCC75D12641B592B8FBDB87F9C7E9B11775306B715DDAEF094FC79`,
all 11 test files pass.

## Consequence for the budget

    pool 88 - widest legal party 17 = 71
    worst page                       75   -> over by 4

The three 10-cell names plus one 9 would close it. There are no further tiles:
the window bank is full and the second bank's tail is now correctly off limits.

# Equip panel: strips accumulate because the redraw is border-only

Reported: equipping Frad Mantle left `Psi Robe` with the tail of the new name
drawn over it. Savestate: `live now 65, peak 92, VRAM holds 88` - the swap
transiently demands 4 cells more than exist, then settles back to 65. Marks
show window 8 created at PoolTop 69 and driving it to 92, so one redraw
allocated 23 cells.

Mechanism, from `Win_EquippedItems` (ps4.asm ~125272):

    bset #0, (Window_Init_Flag).w
    bne.w Win_EquippedItemsMain      ; already drawn -> incremental path
    ...
    bset #0, (Window_Render_Mode).w  ; <- render mode bit 0
    jsr  (Window_Draw).l

`Window_Draw` tests that bit: `bclr #0, (Window_Render_Mode).w / beq
loc_68690`. Bit SET takes `loc_68704`, which does `subq.w #2` on both
dimensions and writes frame tiles - a BORDER-only repaint. The window interior
is never cleared.

So on a redraw the previous draw's item names are still on the plane. The
window is not destroyed either, so `VWFMenu_Release` never rolls the mark back.
`VWFMenu_Sweep` derives liveness from the plane and therefore cannot reclaim
them - they are genuinely still displayed. The new names then allocate on top,
and the pool overflows by exactly the width of the names that could not fit.

The player's order-of-operations reading is right in substance: both sets of
names are live at once. The cause is not the equip/inventory sequencing though
- it is that a border-only repaint leaves the old text on the plane.

## Options

  a. Clear the panel interior before reprinting.  The existing sweep would then
     reclaim the old strips naturally under pressure, with no change to pool
     bookkeeping.  Needs care: `loc_68690` (bit 0 clear) is the full draw and
     may repaint more than wanted, so the likely form is an explicit blank of
     the text rows rather than a render-mode change.
  b. Rewind PoolTop to this window's own mark before reprinting, mirroring the
     verified `Battle_ItemPageRender` fix.  Precondition: the equipped-items
     window must be the innermost open window at that moment, or the rewind
     frees an ancestor's cells.  NOT yet verified - the marks show windows
     above it in some states.

Renaming items does NOT fix this: none of the three 10-cell names appears on an
equip screen.  It is a separate 4-cell problem that happens to be the same size
as the item-page shortfall.

# Equip overflow: it is capacity, not ordering - and duplicates are the cost

Retracted: the earlier "border-only repaint leaves old text on the plane"
explanation was wrong. `loc_68690` is the window OPEN ANIMATION, calling
`loc_68704` repeatedly at growing sizes; render-mode bit 0 selects
draw-at-full-size versus animate, not border versus interior.

What the equip path actually does: `Win_EquippedItemsMain` destroys its windows
in a loop (`move.b #1, (Window_Render_Mode).w / jsr (Window_Destroy).l / dbf`)
and rebuilds. `Window_Destroy` calls `VWFMenu_Release`, so the pool IS rolled
back - and the marks show it, `... 33 24 69 ...` with mark 7 DROPPING from 33
to 24, which only a release can do.

So the overflow is genuine demand, not stale cells:

    baseline through window 7   69
    window 8 needs              23
    available                   19  (88 - 69)
    short by                     4

## Duplicates are where strips cost most

The failing screen listed `Laser Barrier` TWICE. Strips do not dedupe, so that
is two full allocations of identical cells:

    equip list as strips            40 cells
    with duplicate names shared     32 cells   -> saves 8

Eight cells, against a four-cell shortfall - the duplicate alone is twice what
is needed. Duplicate stacks are ordinary (two Laser Barriers here, two Ceramic
Mails on an earlier page), so this is not a corner case.

This materially strengthens the case for per-cell composition that was assessed
and deferred earlier. That assessment measured only shared PREFIXES (Titanium,
Ceramic - about 17% on a page). It did not consider identical names, where the
saving is the entire second copy. Revisit the strips-vs-composition question
with this in the balance.

# Battle drop messages reworded

Build `17335F08D47882B621E13DF27DD29F90EC25D0D2B24A6B2F3CB101FB08658A60`.

## "Gave up <item>." -> "<item> was / given up."

The old form put a fixed prefix first, so a long VWF item name was squeezed
into what was left of the row. `loc_3688` built all three pieces on ONE row:

    lea ($FFFF0896).l, a1 ; st d1 ; draw "Gave up " ; loc_4640 ; draw name ;
    loc_4640 ; draw "."

`loc_4640` is the append mechanism - it scans forward for the blank tile
`$E680` and leaves a1 on it, so each piece lands after the last.

Restructured to mirror the two-row builder that already sits just above it at
`loc_3654` (the chest-swap message): name on row 1 at `$FFFF0896`, remainder on
row 2 at `$FFFF0996` with `clr.b d1`. Strings became `" was"` and
`"given up."`.

Worst case now: `StealthCanceler` 10 + `" was"` 3 = 13 cells on a 21-cell row
(`loc_464A` passes d1=$14), against `"given up."` at 5 on row 2. Any item name
in the game fits.

Note the `lea ($FFFF0996).l, a1` and `clr.b d1` that preceded `loc_464A` in the
original were dead - `loc_464A` opens with `lea ($FFFF3500).l, a1` and
`loc_4650` sets d1 itself.

## "<item> discarded <item2> is procured."

`loc_2AA7DA` was `" discarded "`; now `" discarded."`. Same 11 bytes, so
nothing downstream shifted.

## Not a new bug: the page marker

The reported wrong page marker is `$7F7`, the text-continue arrow, which the
88-slot build already excludes. The savestate confirms it is from the older
build: all eight of `$7EC $7ED $7EE $7EF $7F4 $7F5 $7F6 $7F7` differ from a
pristine reference, whereas the current build takes only the middle four.

# Laila's house: a Japanese-original bug, and why the fix is blocked

## The bug

`EventFlag_Zio` = `$42`, "Set when you fight Zio for the first time" - i.e. the
moment Laila is struck by the Black Wave and leaves the party. Thirteen
messages in the Aiedo tree gate on it:

    #0000 #0003 #0005 #0007 #0011 #0013 #0022 #0043 #0047 #0053 #0057 #0086
        -> jump to tree message $01, which is `dc.b $FF`, empty
    #0029 -> jump to $02

Every one is a line that mentions or involves Laila; when the flag is set they
divert and say nothing. `#0049` - the house rest scene, `{ctl.F4:02}Home at
last!` - is the ONE Laila message in the tree with no gate. The raw JP bytes
from `work/dialogue_full.bak.json` start `f4 02`, so it was never there: this is
an oversight in the original, not something the translation removed.

`$FA` semantics, from `TextCtrlCode_CheckEventFlag`: operand 1 is a flag,
operand 2 a message id; flag SET jumps to that message, flag CLEAR skips the
operand and keeps drawing. Note `tools/dialogue.py`'s comment - "$FA ends the
text and the two bytes after it are read by the event interpreter" - is WRONG;
it is a conditional branch, which is why `#0047` has text after it.

The US release fixed it differently: same scene, Chaz's portrait once Alys is
gone, keeping the free rest point. Player-confirmed in the bugfix ROM.

## The fix, and why it is not applied

Intended: gate `$31` with `$FA EventFlag_Zio, $68` and append `$68` as a copy
of `$31` carrying `$F4 $01` (Rudy). Appending at the end shifts no existing
message id. Under `if bugfixes=1`, where this tree already keeps such fixes.

Blocked by the dialogue pipeline, not by the engine:

  * `script/dialogue N.asm` is NOT source. `tools/treeport.py --write` rewrites
    message bodies from `work/dialogue_full.json`, and `sourcebuild.py` runs it
    as its FIRST step - so a hand edit to the asm is silently reverted before
    assembly. Verified: a marker line inserted into `$31` was gone after
    `treeport --write`.
  * Editing the JSON instead does not work either. treeport ports a message
    only while its engine-token count matches the US reference, and adding
    `{ctl.FA:...}` changes that count by definition, so the message is skipped
    and the old body is left in place. Verified the same way.

Landing this therefore needs a small treeport change - an override for
deliberate engine-code additions - which is a tooling decision rather than a
translation one. Nothing is half-applied: the JSON was restored and the ROM is
back to `17335F08`, byte-identical to before the attempt, with all tests green.

## CORRECTION: the missing gate is probably OURS, not the JP's

Earlier entry concluded "a Japanese-original oversight". The player pointed out
the disassembly base is the US ROM, which demonstrably HAS the conditional
(Chaz greets you post-death), and that the JP pairs these lines too - e.g.
`lz1D1256#0013` carries `{ctl.FA:4201}` and is the Laila-present variant while
`#0014` is the Rudy variant of the same NPC.

Re-examined. The JP text for `#0049` genuinely has no gate - the raw bytes are
`f4 02 ...`. But that is not the whole story, because the trees in `ps4disasm`
are the US structure and `treeport.py` writes our JP-derived English OVER the
US bodies.

`treeport` has an asymmetry:

  * it reports controls WE have that the US lacks ("dropped to match it" - 22
    rows, all `$F9`/`$F4`/`$F2`/`$F7`, never an `$FA`);
  * nothing reports controls the US HAS that we lack.  That case normally
    causes a skip, but only when a US counterpart exists to compare against.

`#0049` has `us: None` - `usimport` never paired it, because the US rewrote the
scene rather than translating it. So `theirs` was empty, the "portraits against
a blank US message" path accepted the port, and our ungated text was written
over the US slot. Any gate the US had there would be gone without a trace in
the dropped list.

That is consistent with everything observed: the US ROM gates the scene, our
build does not, and no tool reported a loss.

## What is needed to settle it

The US tree 10 message `$31` raw bytes. `compress_script.py` only compresses -
there is no decompressor in the tree, and `koschk.asm` references
`script/dialogue 10.bin.unc` files that do not exist. So this needs either a
decompressor for the tree format or a RAM read from the US ROM at the moment
the scene is displayed.

Until then, do NOT apply the speculative `$FA $42, $01` gate: its siblings
divert to the empty message and go silent, whereas the US keeps the scene with
Chaz. Guessing the target would trade a wrong portrait for a lost rest point.

## RESOLVED elsewhere: the Laila house gate (see work/plan-laila-house-gate.md)

Both conclusions recorded above were wrong. Not a JP oversight, and not a gate
`treeport` dropped: the US tree 10 `$31` begins `f4 02`, identical to the JP.
Neither text has a `$FA`.

The US gates it in CODE. `Event_ChazHouse` (ps4.asm, event `$3B`) checks
`EventFlag_Zio` and pokes `$01` into the `$F4` portrait operand of the message -
in the RAM copy of the tree. Our build sets `dialogue_uncompressed = 1`, so
`GetDialogueByID` returns a ROM pointer and that poke writes to ROM and
vanishes. A build-option consequence, not a text or pipeline bug. Fixed by
copying `$31`+`$32` into the unused `Dialogue_Trees` RAM buffer under that
option, patching the copy, and running it from there. Player-confirmed.

Two corrections to the model used above, both mine:

  * `$FA` and `$F5` targets are RELATIVE. `GetOffsetByID` counts `$FF`
    terminators forward from the current position, so `{ctl.FA:4201}` means
    "skip to the NEXT message", not "jump to message $01". That is why
    `#0013`/`#0014` pair, and it dissolves the `$F5` puzzle - yes continues
    inline, no jumps to the next message. `tools/dialogue.py` is corrected.
  * The "empty message $01" reading that drove the "do not apply" warning was
    therefore also wrong, though the warning itself stood for a different
    reason: the speculative gate would have jumped to `$32`.

`tools/kosdec.py` (new, from that work) decompresses the US `script/dialogue
N.bin` trees, so the "no decompressor exists" note above is stale.

# Strips vs composition: rationale found, `=0` built, measured (2026-09-10)

See `work/plan-strips-vs-composition.md`, section "Outcome".  In one line:
the reason per-cell was abandoned is in the imported 2026-08-29 transcript
(strips were meant to let the allocator/sweep/remap layer be DELETED, which
never happened; dedup loss was the acknowledged price), `vwf_menu_strips=0`
now really builds (`work/ps4en_compose.bin`; the ROM name tables hold US
text, so the composed build carries its own translated text table), and in
the harness composition fits every screen that saturates under strips - the
equip transient included, by per-cell use of dead slots rather than by the
duplicate - at 5-8x the per-name instruction count.  The LATENT TRAP above
(voicing comparisons guarded by the strips flag) is closed: they are under
`vwf_menu` now.  Decision pending the by-eye test of frame cost in battle.

# Message wording, batch 2

Build `B1B30DCF73F6A2B7851F03E21A54FA7C7FECD4FFA9980FA5CE3FFA0EF070E8DC`.

    loc_2AA84A   " cannot use" / "techniques here!"
              -> " does not know" / "any field techniques!"
    loc_2AAA06   " cannot use" / "skills here!"
              -> " does not know" / "any field skills!"
    loc_2AA7F0   " procured "  -> " procured."      (same 10 bytes)

The first two are the field tech/skill failure notices; the caller prefixes the
character name. Worst case "Forren does not know" is 20 cells and
"any field techniques!" is 21, against a 24-cell box. The third is the first
line of the "<item> procured / <item2> is used!" overflow message, which was
ending without punctuation like the discard one before it.

All 11 test files pass, invariants hold, pool untouched at 88.

CORRECTION (from the other instance): that build was NOT clean. `Win_MacroMessage`
copies the character name and then a blind 32 bytes of the message into
$FFFFE220 (`move.w #$1F,d7 / dbf`). The US texts fit; these are 37 and 33 bytes
with the $FE terminator, so it was never copied and `LoadWindowTiles` read on
into stale RAM ("Raja BB BBg edB"). Fixed by the other instance: under
`vwf_menu=1` the copy runs through the terminator (`bcs.s` on `cmpi.b #$FE`);
worst case Forren(6)+37 ends at $FFFFE24B, below the $FFFFE252 word the next
routine owns. Landed in `47B72BE3...` (both ps4built and ps4en), 12/12 tests.
The later paralysed->paralyzed build `0D447A2D` predates that fix.

# Blind 32-byte copy, the other two sites

Build `26583CE6351F01236FF97145E75DA4D45A7A64454826A19D2A19BCAE4A4E0788`
(ps4en.bin and ps4built.bin are the same bytes).

The `Win_MacroMessage` fix (47B72BE3, other instance) was one of three.
`Win_TechMessage` (`loc_60700`, table `loc_60772`) and the field-skill window
(`loc_61A54`, table `loc_61AC4`) use the same shape - name copied to
$FFFFE220 through $FE, then `move.w #$1F,d7 / dbf` copying the message blind -
and entry 0 of each table is `loc_2AA84A` / `loc_2AAA06`, the 37/33-byte
"does not know" texts. So picking a character with no field techniques from
the Tech menu (or no field skills from Skill) would still have shown the
stale-RAM tail. Both loops now copy through the terminator under `vwf_menu=1`,
same code as the macro fix (`1018 12C0 0C00 00FE 65F6`). The other table
entries (`loc_2AA866` paralyzed, `loc_2AA876` verge of death, `loc_2AAA26`
not enough charges) are all $FE-terminated, so the through-terminator copy
is correct for every index. Bound is unchanged: Forren(6)+37 ends $FFFFE24B.

Sweep for other `move.b (a0)+,(a1)+ / dbf` copies of message text found only
`loc_57A52` (` is on the verge / of death.`, 27 bytes, still under 32) - left
as is. All 12 tests pass, invariants hold, pool untouched at 88.

