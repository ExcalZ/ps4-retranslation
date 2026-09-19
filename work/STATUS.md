# PS4 Translation — Current Handoff

Updated: 2026-09-18

## Nested-status restore and final chrome corrections (2026-09-15)

The Status > Tech > Skills close corruption was a second, distinct saved-
region bug.  Mark's `slot_5.state` showed `VWFMenu_SaveMark` reaching 88 at
depths 12-13: per-window tile dedup had filled the 88-record save stack, so
later windows left raw pool references underneath them.  Those references
displayed unrelated names after their tiles were recycled.  In the composed
build, `VWFMenu_SaveRegion` now deduplicates all active records by their
immutable 8-byte glyph key (not the recyclable physical tile) and uses the
80-byte gap before `VWFMenu_Scratch` for eight additional compatible records.
`test_shared_cells.py` covers cross-pass key reuse.  The BlastEm harness closed
`work/field-slot3.state` twice with zero refused cells (pool 85 -> 37).

The same build restores the Save window to nine cells while retaining the
fixed Slot 3 cursor, moves the battle result's amount and `EXP` anchor together
(`$08A0..$08A6`, then `EXP` at `$08A8` in a direct BlastEm redraw), expands
`DYIN` to `DYING` and pads the other status abbreviations over the stale level
digit, changes Pyke's profession to `Berserker`, and restores `COMMAND`.  The
actual mixed-case face measures `COMMAND` at 38 px, so it fits the 40 px field
when the redundant leading space is omitted.

Both pre-effect and post-effect dynamic Field Tech/Skill `" is used!"`
sentences now use `VWFField_LoadWindowTiles`; their longest generated lines are
78 px (Tech) and 93 px (Skill) in the 192 px message field.

All 13 `tools/test_*.py` programs pass with hash/chrome enabled.  Canonical
experimental ROM: `work/ps4en_compose.bin`, SHA-256
`8E92167CC79E8E01B02F638B8B59FC520EF68ECC29DC2FAA8FEB8F9F580477B2`,
with matching `work/ps4en_compose.lst`.  Options were restored to 0/0; the
shipping ROM file remains unchanged at SHA-256
`D8372FE730EF3CEAC8C70E860C7404ABB1C80420E536CE6D7B8CF4422AF7E288`.

## Chrome bug-fix and profession checkpoint (2026-09-15)

The saved Equip/party corruption was real, not an expected consequence of
the fixed alphabet still being present.  Content-keyed pool slots can have
more than one visible plane reference, but `VWFMenu_Sweep` rebuilt every live
slot with a refcount of one.  Replacing either cell then freed and recycled
the tile under the other.  Chrome sweeps now count every plane reference
(saturating at `$FF`); `test_shared_cells.py` reproduces the two-reference
case, dereferences one cell, and verifies the other remains live.

The same experimental build fixes the four reported presentation issues:
the Save window is eight cells wide and all three slot glyphs use the same
column; the battle-results EXP value starts one cell after composed `Each
got`; status text replaces the complete `Level` label; and Miracle says
`Everybody's HP recovered!` at all seven result-pointer sites.  The corrected
Miracle string lives in the extension and uses explicit menu-charset bytes.

The earlier glue sketch is implemented for separately drawn name/tail runs,
including cached battle-party names (`Forren` + ` retreated!` and name +
`'s Level increased!`).  Cached replays take a distinct owned slot before
merging, so they do not mutate the cached name's shared final cell.

The next handoff item is also done: status professions are title-cased
(`Hunter`, `Scholar`, `Wizard`, `Motavian`, `Numan`, `Android`, `Priest`,
`Esper`) and the dynamic `$FFFFE220` profession buffer is drawn through the
forced VWF wrapper under `vwf_menu_chrome=1`.  Both duplicate translation
lists in `script_translated.json` use the same casing.

All 13 `tools/test_*.py` programs pass with hash/chrome enabled.  Canonical
experimental ROM: `work/ps4en_compose.bin`, SHA-256
`ED03A851D6EFBD7ED1AF2DF5C3C5638B181901C03FCD018218443403DA2C67DB`,
with matching `work/ps4en_compose.lst`.  Options were restored to 0/0 and the
shipping ROM remains byte-identical at SHA-256
`D8372FE730EF3CEAC8C70E860C7404ABB1C80420E536CE6D7B8CF4422AF7E288`.
An old savestate retains its already-corrupted pool/VRAM until the affected
windows are closed and redrawn (or the game is restarted); the fix prevents
the corruption from recurring.



















## Experimental build is now `work/ps4en_compose.bin`; all the chrome (2026-09-15)

Mark renamed the shipping copy to `work/ps4en_compose_stable.bin` (byte-
identical to `ps4en.bin`, listing `work/ps4en_compose_stable.lst`), so the
experimental build - `vwf_menu_hash=1`, `vwf_menu_chrome=1` - is written to
`work/ps4en_compose.bin` from now on and his BlastEm profile, saves and
states carry over.  `tools/field_drive.py`'s default ROM is that file.
Build it by setting both options to 1 and `python tools/sourcebuild.py
work/ps4en_compose.bin`; set them back to 0 for `ps4en.bin`.  13/13 on both.

**Second chrome pass.**  The gate now walks a table, `VWFMenu_ChromeTable`
in vwfmenu.asm - (lo, hi, kind) triples, kind 1 for the PAD rule - placed
before the ordered battle ranges, whose early exits to the label path had
hidden everything below `$27E5D2` from it.  The pad rule learned that a
lone space between two glyphs is a word space (only a space that starts a
run, sits in a run, or precedes a colon / graphic / control pads), so
prose like `Strength increased by` composes as prose and only the spaces
that hold a value pad.  Composed now, on top of the first pass: every
frame caption (`ITEM`, `EQUIP`, `WHO?`, `WHOSE?`, `MACRO`, `ORDER`,
`COMBAT`/`FIELD`, `TECH`, `SKILL`, `TO?`, `SYS`, `BUTTONS`), the title
menu, the SYS menu (`BTL SPD` -> `BATTLE SPEED`) and its speed selector
(`FST`/`SLW` -> `FAST`/`SLOW`, digits padded over the cursor tiles), the
button assignments (`CANCL` -> `CANCEL`, six permutations generated from
the face so each label lands on its stock column), the save-slot rows, the
chest `DSC`/`RET` -> `DISCARD`/`RETURN` (window 9 wide), `USE`/`LOOK`/
`DISCARD` (window 9 wide), `YES`/`NO`, shop `buy`/`sell`, every field
notice (the six drawn in typewriter mode go through
`VWFField_LoadWindowTiles`, a same-size jsr swap, and appear whole),
`Victory!`/`Each got`/`EXP`/`meseta!`, the battle item `Use`/`DSC`, and
the level-up sequence.

**Level up.**  `<name>'s Level increased!` and `<attribute> increased by
<n>!` / `Max HP increased by <n>!`.  The value is drawn by the results code
on the first blank cell it finds after the label; the stock labels had
blank cells inside them that the code skipped with `lea 2(a1)` + `jsr
loc_4640` pairs, and composed prose has none, so those pairs are `nop`s
under the flag (same bytes) and the strings carry exactly the pad cells
the value needs - two for an attribute, three for HP/TP - with the `!`
after them.  `test_paths` derives the pad counts from the face and asserts
the blank-cell count and the 18-cell fit.  Two things to look at in play:
the name's cell-boundary join (`Forren 's` can show up to 7 px of gap - a
"glue" mode that reopens the previous run's last cell would fix it, not
built yet) and the value's leading blank for one-digit rises (`by  5!`).
Not reproduced in the harness; the battle states here never level.

Still fixed: the class name on the status screen (`ANDROID`), the `HP`/
`TP` graphic pair, `2-HAND`, `DYIN`/`PARA`/`POIS`, the title screen's slot
summary (`Chaz:LV`/`M`), the debug check window, the map overlay labels,
and the LOOK description (pool-bound, see the 2026-09-14 note).  Seen
live on `field-slot0`: SYS menu and both speed selectors, button window,
item action, plus the first pass's screens.

## Experimental build: fast window close, composed chrome (2026-09-15)

Two new options in `ps4.options.asm`, both 0 in the shipping ROM.  Both 1
builds `work/ps4en_exp.bin` (its listing is `work/ps4en_exp.lst`; the
field harness takes `--rom work/ps4en_exp.bin`).  13/13 tests on both.

**`vwf_menu_hash = 1` - the window-close hitch, measured and fixed.**
The plan blamed the composer's linear key scan (290 lookups on a Status
back-out).  Hashing it - 128 buckets over `StripOf`, chains through
`StripNext`, both dead in the composed build, links as slot+1 so zeroed
RAM is an empty index, `VWFMenu_IndexRebuild` on every Mark and Release so
a savestate from another build heals itself - removed the 13,000 scan
steps and bought two frames.  The cost was next door: the reveal remap
called `VWFMenu_RemapCell` for every cell of every restored region, 5,760
calls to find the 290 markers, and each call pays a ten-register frame.
Testing for a marker in the region loop first is what closed the hitch:

    lag frames        compose   hash   hash + marker test
    Techs back           14      13         4
    Skills close         20      19         5
    Item list close      11      10         6
    Item page flip L     15      12         8

What remains is the two sweeps (about a frame each) and stock's own
redraw.  The hash keeps the index exact - on a fresh menu the taken /
refused counts match the linear scan's to the cell - and it is what makes
the chrome below affordable, so it is the part of this build I would ship
first.  `tools/emu68k.py` learned `eor.l`/`eor.b Dn,Dm` for it.

**`vwf_menu_chrome = 1` - the fixed-width labels compose.**  Two kinds of
range in the gate.  CHROME ranges compose plainly: the field menu (both
tables; the window is back to 9 wide, `STATUS`/`MUMBLE` fit), the
`TALK`/`MUMBLE` caption, `USE`/`LOOK`/`DISCARD`, `YES`/`NO`,
`STATUS`/`ORDER`, and `Exp :`/`Next:` (composed colons: both end before
the number at column 4).  PAD ranges are the labels that position
themselves with spaces against numbers the numeric path draws at fixed
columns - `Meseta`, `Level` on the party bar, `Level`/`Age`/`HP`/`TP`,
the six attributes, the equip comparison's `Attack`/`Defense`/`Agility`/
`Mental`.  There a space advances the pixel cursor to the next cell
boundary and a colon is the stock tile from the `$7C0` copy in one cell
(`VWFMenu_PadMode`, `VWFMenu_DrawString_Pad`), so `"Strength   :"` puts
its colon on column 7 exactly as `"STRNGTH:"` did and the digits do not
move.  The pad counts are derived from the face and asserted by
`test_paths` (every colon and `$F8` control on its stock column, every
label ending before the field to its right).  The two meseta windows are
14 wide instead of 13 for `Meseta` from column 9.  Seen live on
`field-slot0`: menu, party bar, status screen, equip comparison.

Still fixed-width on those screens: the class name (`ANDROID`), the
frame captions (`ITEM`, `EQUIP`, `WHO?`, `WHOSE?`, `STATUS`), the `HP`/
`TP` graphic pair, `2-HAND`, `DYIN`/`PARA`/`POIS`, and everything drawn in
typewriter mode (item notices), which composes only when forced.  None of
the `$7C0` letters are freed until the last of those goes.

One pool note: `$681` is a pool slot (`menupool.py` reclaims it), so
`VWFMENU_FIXED0`'s "the colon" comment is history; the label path and now
the pad colon both use `$7F3` from the `$7C0` copy.

## Battle menus and flow messages compose; field menu one cell wider (2026-09-14)

One new composer range, `VWFMENU_FLOW_LO/HI` = `loc_27E6E8..loc_27E76E`,
covers everything the gate used to leave fixed between the status-effect
messages and the result tails: the battle command menu (` COMD/ MACRO/
RUN`), `Surprise Attack!`, `DEFENSE`, ` retreated!`, `Cannot escape!`,
` defeated...!`, ` recovered!`, `ATTACK`, and the vehicle menu.  The name
in front of the four tails already composed, so `Forren defeated...!`
was a light proportional name followed by bold 8x8 text; ATTACK/DEFENSE
sit in the macro window beside composed technique names; the two menus
are vertical lists whose cursor is the `$67` tile at a fixed column,
which the composer already lets through as a width-0 graphic before
composing the label - the same mechanism as the `$78$79` HP/TP labels.

Renamed under composition: `COMD` -> `ORDERS`, `MACR` -> `MACRO`, and
the vehicle menu `ATTAC/OPTIN` -> `ATTACK/OPTION` (seven-byte entries,
`addq.w #7`).  The command menu's entries are nine and eight bytes: the
draw's `addq.w #7,a0` + `clr.w d1` became `lea 9(a0),a0` (same four
bytes; d1 only matters to loc_27DB92 for the $F0/$F1 codes, which these
labels never carry) and the second step is `addq.w #8`.  `COMMAND`
would need a ten-byte first entry, which no two-byte step reaches.
` defeated...!` -> ` was defeated...!` (13 of 18 cells after Forren).
`test_paths` now reads both tables back at the stepped offsets, checks
each entry carries its terminator, and measures every label and every
flow message against its window (widest party or enemy name in front).

Field main menu (`WinGroup_Menu` entry 0) is 10 cells wide instead of 9,
and `STATE` -> `STATUS`, `MUMBL` -> `MUMBLE` in `WinTiles_MainOptions` /
`..Alone`.  Those labels still draw fixed-width; any six-letter label
fits now.

Only data symbols moved (the strings grew by a few bytes), no branch
target below `$300000` changed address, and the 4th-MB composer shifted
by -18 bytes, which only matters to a state saved mid-composition.
`test_paths` addressed its chrome cases by stale literal addresses from
the 3 MB layout; they are symbols now.  13/13 tests.  Seen live: the
field menu at 10 wide with STATUS, the battle menu composed with MACRO,
the item list and party bar (previous entry).  `Cannot escape!` and
`retreated` were not reproduced in the harness - the boss state never
reached a run attempt and the giresta states reset the driver - but
they take the path ` has slept!` has used since the effect range.

## Menu face: small caps replaced by a mixed-case alphabet (2026-09-14)

The menu VWF now draws `tools/vwfmixed.py` - one proportional alphabet on
the stock 8x8 font's own vertical metrics - instead of the small caps
(`vwffont.G`, rows 3-7) with true capitals over them (`vwfcase.CAPS`).
Chosen from three candidates measured over every name table and set into
saved screens; the evaluation page with the switchable mock-ups is at
https://claude.ai/artifact/VgJMZfZuiFLsbLEd7DWQPN.

    capitals    rows 0-6, 4 px wide (M N V W X Y 5)     was rows 2-7, 5 px
    lowercase   x-height rows 2-6, ascenders from 0,     was small caps
                one descender row (7) on g j p q y
    digits      rows 0-6                                  were rows 3-7
    baseline    row 6 - the stock font's                 was row 7

Why these metrics and not the lowercase already in `vwfcase.LOW`: its
4-row x-height is cramped at 8 px, and it has no descenders.  Five rows
is what makes e/a/s read; the 1-px descender is stock's own.  Baseline 6
puts composed text level with the fixed `HP`/`TP`/`LV` labels from `$7C0`
and with stock lowercase in battle messages (`Forren defeated...!`), and
one row above the digits exactly as stock is - the old face sat a row low
beside all three.

Width, over the tables as translated: lowercase 4.65 px mean advance
(4.51 weighted by use) against 5.08; capitals 5.12 against 6.08; items
average 51 px against 56 and the widest is 9 cells against 10; every
other table's max is unchanged or lower and nothing crosses a stock
budget.  Party names go from 31 of 32 px to 27; the widest enemy name
from 80 of 80 to 75.  Cells over items + techniques + skills: 1485
against 1632, so the pool is under less pressure, not more.

Files: `tools/vwfmixed.py` (new), `tools/menuvwf.py` (draws it; the old
modules stay for `vwfpatch`'s JP pipeline).  `menufont.bin` and
`menuwidth.bin` keep their sizes, so only the font data, the width table
and the `$57` u-diaeresis tile in `Font.bin` differ from the previous
ROM - no code address moved and savestates load.  Three tests had the
old face's cell counts baked in (`Resta` four cells, `Gifoie` four,
`Hunter Knife` eight); they now read the counts from
`menustrip.compose` / the strip index.  13/13 on both builds.

Verified live with `tools/field_drive.py` on `work/field-slot0.state`:
close everything, reopen the menu with `A`, open Items, flip pages - every
list page and the party bar compose cleanly in the new face, no leftover
cells when a shorter name replaces a longer one.  One caveat for the
player's existing BlastEm states: a state saved under the old face keeps
the old keys in RAM and old tiles in VRAM, so until its windows are closed
and reopened a redraw can show a hybrid (a page flip on the old state
left `Moon Atomizer ie`).  Not a bug; close and reopen the menu once.

Locations and class names are all-caps in the script (`BIRTH VALLEY`,
`HUNTER`), which is now the widest form; title-casing those two tables
would buy ~4 px per name.  Script edit, separate decision.

Previous ROM kept as `work/ps4en_smallcaps.bin`.  To revert: point
`menuvwf.spec` back at `vwfcase.CAPS` / `vwffont.G` and rebuild.

## `lz1DB036#0078`: the US dropped the portrait (2026-09-14)

Tree 30 `$4E`, the bookshelf line in the redecorated house.  The JP opens
with `{ctl.F4:01}` like `$4D` and `$4F` either side of it, but the US
build's message carries no controls at all, and treeport emits every
message under the US controls - so the row ported (one dropped control is
within the pairing rule) and drew with no speaker.  Now the second
sanctioned deviation in `treeport.OVERRIDES`, `(30, 0x4E): ('lz1DB036#0078',
'jp')`, alongside Zio's death cry: the message is written with the Japanese
controls, which differ from the US by exactly the portrait its neighbours
already show.  `test_treeport_controls`: 2 sanctioned deviation(s).

## Field menus: where the hitches are, measured (2026-09-13)

Four states saved on the composed build (`work/field-slot0..3.state`: Item
page 2 with the pool at 87/88, Equip list, Status > Techs, Status > Skills,
all Rudy), costed per keypress with `tools/field_drive.py` (lag = VInts the
main loop was not ready for; 60 = one second):

    Items   page flip    15-20 lag frames, 8-9 full-plane sweeps each
            close        26, 5 sweeps + 5 region remaps + 103 stock redraws
    Equip   equip / back  5 / 7
    Techs   back         19  (290 remap lookups)
    Skills  close status 36  (9 sweeps)

The battle fixes above do not reach any of this: nothing in the field
composes per frame.  What costs here is (a) `VWFMenu_Sweep`, a walk of all
2048 plane cells, close to a frame each, and (b) the reveal remap's per-cell
key lookups.  The strips build closes menus just as slowly (33 frames on the
same state) and flips pages a little faster (4-11).

Two changes, both builds:

1. The composer's pressure sweep used to fire on EVERY string once PoolTop
   had touched the cap, because a sweep frees slots without moving PoolTop.
   It now fires only when the zero-count slots the last sweep left (any
   slot - the free scan takes those below the frontier, growth steps onto
   those above) cannot cover the run plus `VWFMENU_SWEEP_RESERVE` (4).  The
   reserve is for the window-close animation, whose remap may not sweep:
   with no reserve, flips that left the pool with nothing free made it
   blank 22 cells.  Item page flips: 7 / 2 / 8 / 13 lag, 1-3 sweeps.
2. The reveal remap sweeps per region only when the free slots could not
   cover the whole region.  In practice large regions always exceed the
   pool, so this rarely skips; kept because it is cheap and correct.  One
   sweep for the whole reveal queue was tried and is wrong - each region's
   remap overwrites its restored cells and the stale slots those pointed at
   are only reclaimable after a sweep has seen them gone.

Two traps from this pass: `VWFMenu_FreeSlots` returns in d0, and the remap
entry needs d0 intact for `_Ready` - `test_shared_cells` caught the clobber
(the harness measurements had not: the wrong region was being remapped);
and a reserve must be added to the demand, never subtracted from the free
count, which can be zero and wraps.  The menu-close cost that remains is
the remap's lookups (290 on a Status back-out) and the stock redraw; the
lever for the lookups is the first-byte bucket over the key table that the
strips-vs-composition plan named, which would fit in `StripOf`/`StripNext`
(unused when `vwf_menu_strips=0`) since the VWF RAM block is otherwise full.

## Battle slowdown and the holes in "Recover": the HUD composed every frame (2026-09-13)

Reported on the composed build in the Profound Darkness fight: low frame
rate throughout, and Forren's "Recover" drawn as `RE  R` on the second skill
page after paging through the Item window.  `work/pd-slot7.state` (BlastEm
ps4en_compose slot_7, the first form, COMD menu up) is the state it was
worked from.

**Cause, measured rather than guessed.**  Stock code redraws the party
status bar every frame, and with the menu VWF that composed all five names
sixty times a second: 5 `VWFMenu_DrawString` calls and 16 `VWFMenu_Alloc`
hits per frame, each hit a linear scan of the key table.  At the battle
menu that alone put the main loop over the frame on 15 of 45 VInts; across a
round with lists open it was 740 lag frames in 1698 (44%), i.e. the 30-40 fps
the player saw.  Every hit also did `addq.b` on a byte refcount that battle
never decrements, so the HUD's sixteen counts wrapped to zero every 256
frames (4.3 s) - the saved states show them at 33 and 216, which is only
"frames since the last wrap".  A list composed on a wrap frame finds those
slots free, takes them, the HUD reallocates sixteen new slots on the next
frame, the next rewind hands those to the next window, and so on; the pool
fills, `VWFMenu_Alloc_FullReally` starts refusing cells, and a name is drawn
with holes where its cells were refused and its neighbours were found
resident.  That is the `RE  R`.  On top of that the Item window pre-rendered
all four pages at open: 237 grows and 151 refused cells per open (the pool
hits 88 every time), and each page is rebuilt by `Battle_ItemPageRender` on
its way in anyway.

**Fixes, both builds.**

1. `VWFMenu_PartyCache` (constants): one entry per Character_Stats record -
   the pool generation it was composed under, its cell count and up to six
   tile offsets.  In battle the party-name path of `VWFMenu_DrawString`
   replays the entry when `VWFMenu_TakeGen` (bumped by every `Alloc_Take` and
   by `Reset`) still matches, and recomposes and records otherwise.  A
   zero-cell entry counts as never composed, so a state saved before the
   cache existed still draws its HUD.  Field menus never use it: sweeps move
   slots there and the field has no per-frame party bar.
2. `VWFMenu_Alloc_Hit` saturates the refcount at 255 instead of wrapping.
3. `VWFMenu_SkipNames`: set by `VWFMenu_BattleOpenItems` for the whole
   pre-render (names draw as stock-length blanks, nothing allocated), cleared
   by `VWFMenu_BattleItemPageOpen` just before the visible page is rendered.
   Both are reached through six-byte `jsr`s padded to the size of the code
   they replace, so no ps4.asm address moved and the player's savestates
   still load.

Same round, same inputs, after: 91 lag frames in 1091, and those are the
Nemesis decompressor loading attack art (vanilla); idle at the battle menu,
1 in 300.  Item open: 26 grows, 0 refused cells, peak 76 instead of 88.
Every list page and the HUD drawn whole in the screenshots; 13/13 tests on
both builds; invariants clean.

**How it was measured: `tools/blastem_drive.py`.**  BlastEm 0.6.2 run with
`-D` and driven over its GDB stub: breakpoints, register and RAM reads and
writes, the pad injected at `ReadJoypad` by overwriting d0, one frame per
pad read, lag frames counted as VInts that arrived with `VInt_Flag` clear
(the interrupted PC is kept as a profile sample).  `-s` takes the native
`.state` files directly, but 0.6.2 leaves `reset_cycle` at zero and resets
the machine on the first sync after any load; the driver patches the ROM
copy's entry point to `move.w #$100,(Z80_Reset)` + `jmp` back to the state's
PC before the JIT sees it, restores the registers when that lands, and stubs
the sound driver (the YM was reset and its busy wait would spin).  No sound,
otherwise the game continues from the state.  `tools/battle_drive.py` sits
on top: `comd`, `attack`, `skill:page.index`, `item:...`, `browse:item.3`,
`enemy`, with every store to PoolTop or a battle mark logged with its frame
(`tools/battlepool_trace.py` finds them in the listing), and screenshots via
`tools/winshot.py` (BitBlt from the window DC, which works while the
emulator is stopped).  `python tools/battle_drive.py work/pd-slot7.state
--rounds 2 --shots out/` is a full regression on this fight.

**Ending narration (`lz1E1316#0018`/`#0019`).**  RunText2 ends a message at
the first control code (`loc_6AA44` sends all of `$F0-$FE` to the flush),
so a `{BR}` in a narration line drops everything after it: the player saw
"The millennium of light and darkness" / "and now the curtain rises on" and
nothing else.  Both are single lines now, measured against the 256px wrap
with `tools/narration.py`: "The millennium of light and darkness ends,"
(253px) and "and now the curtain rises on a new age..." (245px).  Two lines,
as the JP has.  Not seen in play yet - the saved state is past the draw.

## Treasure chest wording: "Item pack", "give this up" (2026-09-13)

Two hand-maintained chest strings (WinGroup_TreasureChest, not in the
JSON): `loc_2AA748` "Itempack is full!" -> "Item pack is full!" (drawn by
VWFField_LoadWindowTiles in the 25-wide generic window, so the space costs
nothing), and `loc_2AA7FC` "Are you sure you want / to give up?" -> "to give
this up?" (fixed-width, row 2 of the same 23-inside window; 16 columns).
The battle-side "Want to give up?" (`loc_27E798`) is a different prompt in
the 18-inside result box and is unchanged.  Both builds; ps4disasm/ holds
the strips build.

## Aeroprism field-use message; Phonon Maser aligned (2026-09-13)

`loc_2AA25C`, the special-case field message for using the Aeroprism where
nothing happens, still carried the US "AERO-PRISM is raised up!".  Now
"Aeroprism is held aloft!" / "But nothing happened..." (JP
エアロプリズムを かざした！ / しかし なにも おこらなかった・・・).  It is a
hand-maintained window string like the other item-use notices at
`loc_2AA1D2..`, not ported from the JSON; drawn fixed-width, mixed case is
fine there.

The build gate then caught a JSON edit from 2026-09-12: the enemy action
`r02s002#031` had become "Phonon Maser" while the skill `r00s003#016` was
still the space-closed "PhononMaser".  Both compose to 8 cells, which is
the skill field's budget, so the closure is no longer needed: the skill now
reads "Phonon Maser" too.  Both builds.

## Soldier Fiend's Giresta left its name window behind: a US-only omission (2026-09-13)

`work/giresta-slot1..3.state` (BlastEm ps4en_compose): the "Giresta" window
opens at the top left, closes with the usual shrinking frame, and the full
window is still there afterwards - the "duplicate".  Mechanism, all in
vanilla code: the Soldier Fiend Giresta object (`loc_22FC0`, battle object
`$378`) snapshots the whole of Plane A into `$FFFF2400` with `loc_24A08`
twice, at the cast (`loc_2301A`) and at the end (`loc_231D0`), while the
action-name window is still open; `loc_B54A` then "closes" the window by
restoring rows 1-3 FROM that snapshot, so whatever the snapshot holds comes
back.  The JP calls a clearing subroutine after both snapshots.  The US
inlined it after the first and dropped it after the second (checked in
`work/ps4us_bugfix.bin` and the Bugfix v1.5 ROM: same bytes, so retail US
has this too).  The clearing loop itself is also off: 7 longs then `+$38`
is a `$54` stride over a `$50`-byte row, so even the JP leaves the left
edge of rows 2-3 (`tools/blastem_screen.py` + the replay showed
`6F3 69A` / `6E9 6EA 6EA 6EA` surviving).

Fix: `SoldierFiend_ClearSkillWindowSnapshot` (rows 0-3, columns 0-15, real
stride) replaces the inline loop and is called after both snapshots.
`test_giresta_window` replays open / snapshot / erase from slot 3 against
the built ROM: 0 tiles left; 36 on the US path.  Both builds.

Playtested: the Giresta window now closes cleanly.

**Second half, same object (2026-09-13):** with the Soldier Fiend under
Sealis the cast is refused at frame `$E` (`btst #4,$16(a1)` at
`loc_23094`) and the object takes the `loc_230EE`/`loc_230FE` tail
instead - and the enemy stays in its arms-up cast pose for the rest of
the battle (`work/giresta-sealed-slot4.state`, and the live screen after
it).  Enemies are Plane A tiles, not sprites: `loc_2301A` draws the cast
pose into the plane (tiles `$342-$349` at rows 8-9) and snapshots it;
`loc_230FE` redraws the idle pose with `loc_254F4` but, in the US, never
re-snapshots, so the next window restore (rows 4-15 from `$FFFF2540`)
puts the cast pose back.  The JP's sealed tail is `loc_254F4` +
snapshot + clear (the `jsr $24960` at JP `$23064`), exactly like its
unsealed end.  Restored: `loc_230FE` now calls `loc_24A08` and
`SoldierFiend_ClearSkillWindowSnapshot`.  `test_giresta_window` runs the
built object from slot 4 (frame `$E`) to `Battle_Routine $16` with
`loc_254F4` stubbed and a marker tile on the plane, and checks the
marker reached the snapshot.  Both builds.

Playtested: the Soldier Fiend returns to its idle pose.

**Are there more?**  `tools/objdiff.py` pairs all 577 battle objects
between the JP ROM and the US build through the dispatch tables,
disassembles both with BlastEm's `dis.exe` (following the `jmp
(d8,pc,d0.w)` phase tables it stops at), normalises addresses and diffs.
15 objects differ.  Of the 36 enemy tech objects that carry the
tech-sealed check, only `$378` (this one) and `$2F8` (`BattleObj_EnemyRimit`,
a sound-effect call moved past a branch - harmless) differ from the JP.
The other 13 are not enemy attacks: `$0FC/$140/$160/$354/$398` call a
low-ROM helper at a shifted address, `$1E4-$1F8` drop a `clr.b $FFFFEE80`,
`$2E0` reorders a VDP setup, `$734` drops a `$FFFFEE69` flag; none
touches the plane snapshot or a window restore.  So the Sealis refusal
path is JP-identical for every other enemy, and `loc_24A08` has no other
callers.

Tooling that came out of this: `tools/blastem_screen.py` renders a BlastEm
native `.state` to PNG (planes, sprites, scroll, priority) - the VDP section
follows the VRAM at a fixed layout, and VRAM is found by matching the Plane
A buffer in RAM.  `emu68k` gained trap/rte, pc-relative jsr/jmp, signed branches, and
generic move/tst/clr/addq/subq/add/sub/cmp/immediate/bit-op forms, so battle-window code runs
in the harness.  BlastEm 0.6.2 itself crashes on loading these native states
from its menu here, so the render + replay path is the one that works.

Also today: `restore_unused_enemies = 1` (Arcacia and Shade Mirage in the
formation table; only `Battle_FormationIndexes` and the pointers behind it
change).  Both builds.

## Battle result tails compose: "received!", "discarded." (2026-09-11)

The drop/use/discard panel wrote "<item> found!" / "<item> got!" and
"<item> discard" / "<item2> got!".  Now " received!" and " discarded.";
the tails that follow an item name (`VWFMENU_RESULT_LO/HI` and
`RESULT2_LO/HI`: found, received, was / given up., discarded., used!)
compose, so the 18-cell box takes the widest item name plus an
unabbreviated tail ("Plasma Launcher discarded." is 16).  The Yes/No
prompts and "But pack is full!" between the two ranges stay fixed - they
are cursor targets or already fit.  `test_paths` checks the dispatch and
every tail against the widest item.  Both builds.

## Status-effect messages unabbreviated; window 20 wide (2026-09-11)

    Attack Power is UP/DOWN!   Defense Power is UP/DOWN!   Agility is UP/DOWN!
    Dexterity is UP/DOWN!      Mental Power is UP!         (rest unchanged)

Composed, the widest is still "GrassSlaughterer is paralyzed!" at 18
cells, so `BATTLE_EFFECT_W` is 20 (was 22): the box is full at the worst
case and the common lines (11-14 cells) no longer sit in a field of blank.
Both builds.

## SaveRegion matched other windows' records (2026-09-11)

`work/compose8-swifthelm.state`: Rudy's Swift Helm with its second and
third cells pointing at slots holding Force Cane[1] and a party-name glyph
- the keys of save-stack records 1 and 7, which belong to the base windows
over the field HUD.  `VWFMenu_SaveRegion` dedups records by TILE and
searched every record from 0, not just this pass's: a slot recorded by an
older window, freed while covered and reassigned to Swift Helm, matched the
older record when the Tech window covered Swift Helm, so the marker
resolved to Force Cane's cell on reveal.  Latent on both builds (a strip
record would resolve to the wrong strip the same way); composition
reassigns slots more often, which is why it surfaced now.  The dedup scan
now starts at `VWFMenu_SavePassBase`, the SaveTop when the pass began.
`test_shared_cells` reproduces it and the check fails on a mutant ROM with
the old scan.  Both builds: `ps4en.bin` `5F75223A...`, composed
`6D388962...`.

## Reveals are deferred to the next plane DMA (2026-09-11)

`work/compose7-status-tech.state`: Rudy's status Tech page after backing
out of Skills, Procedan drawn with two holes.  Not capacity - the finished
screen needs 71 slots - but a transient: leaving Skills destroys two
windows in a row, and the FIRST destroy's reveal remapped its region while
the second window's content was still on the plane, so the pool held both
pages, Alloc ran out, and RemapCell wrote blanks that nothing repairs.
Neither window reaches the screen between the two destroys, so
`Window_Destroy` now queues its region (`VWFMenu_DeferReveal`, up to 8) and
`VWFMenu_FlushReveal` remaps the queue just before `DMA_PlaneA` (every
Plane A send goes through it) and at `Window_Create`'s entry (SaveRegion
would otherwise capture markers, and the old window group must still be
current).  `test_shared_cells` covers a two-window reveal under pressure:
13 of 13 names whole after the flush.  Both builds.

## Sleep messages were never shown: the US table is off by one slot (2026-09-11)

`loc_2B3A` walks `id-1` terminators, so entry N is message id N+1.  The
start-of-round wake check (`loc_67CE`, identical bytes in the JP) emits
id `$E`, and the per-fighter loop shows ids 7, `$E`, `$1B`, `$1C` - which in
the JP are {F2}fainted, {F2}came-to, {F2}poisoned, {F2}paralyzed, exactly
the four `$F2` lines.  The US left entry 6 (id 7, fell asleep) EMPTY and put
" has slept!" in entry 12 (id 13), which is the JP's Mental UP - so the US
never announced sleep and would have said "has slept" for a mental boost.
Restored: id 7 `$F2 " fell asleep!"`, id 13 "MTL POW is UP!", id 14 `$F2
" woke up!"`.  `test_paths` asserts the layout.  Ids 7/$E are suppressed for
enemies by `loc_2B0E`; `$1B`/`$1C` are not, so a poisoned or paralysed enemy
does get a named line - the widened window and the enemy-record name
resolution cover that.

## Status-effect messages: names hooked, grammar tidied (2026-09-11)

The `$F2` prefix IS the name hook: `loc_2B44` draws the fighter's record
name first when a message starts with `$F2`, and the JP uses it on the
poisoned / paralyzed / fainted / came-to lines.  The US dropped the byte
but kept the leading space.  Restored, with wording:

    $F2 " is poisoned!"   $F2 " is paralyzed!"   $F2 " fell asleep!"
    $F2 " woke up!"       "Techs are sealed!"    "DEXTERITY is DOWN!"

Party names compose through CharNameData as before.  Enemy records hold a
blind 14-byte copy of the name (no terminator past 13 letters), so the
composer resolves an `Enemy_Stats` record by the id at `$68` into the
translated `EnemyNames` entry instead.  The window (`BATTLE_EFFECT_W`) is
22 wide now, 18 inside: nothing sits right of it on rows 18-20 / 12-14 and
the teardown restores all 40 columns; "GrassSlaughterer is paralyzed!" is
18 cells.  `test_paths` checks every message against the widest enemy name.
The US " has slept!" slot (id 14) is where the JP has Mental UP and the JP
fainted line is at id 8, which the US left empty - the effect ids the
engine emits were not audited here.

## Battle status-effect messages compose (2026-09-11)

"All status UP!" -> "All stats UP!", "NRG Barrier UP!" -> "Energy Barrier
UP!" (JP エネルギーバリアをはった！).  The abbreviations came from the 18x3
message window's 16 fixed cells; the block `loc_27E5D2..BattleEffectText_End`
now composes (`VWFMENU_EFFECT_LO/HI`), where the widest message is 11 cells
and a party name in front of the `$F2` ones still fits.  Battle never
sweeps, so `Battle_OpenTechEffectMsg` records `VWFMenu_BattleEffectMark`
and every per-fighter rebuild of the window and its teardown rewind to it.
`test_paths` checks the dispatch and that every message (with the widest
name) fits 16.  Lesson recorded in the dispatch: the address ranges are not
in ascending order, so each `bcs` on a LO must fall through to the NEXT
range's test, not to the label path - the EFFECT range sits below SPACE and
was skipped until that was fixed.

Worth a translation pass while here: the US block does not line up with the
JP one (`$27DE20`) - JP has せいしんりょくアップ (Mental UP) where the US
has " has slept!", and the US repeats "DFS POW is DOWN!" in two slots.

## Field skill "is used!" read the US skill table (2026-09-11)

`Win_SkillMessage` (both entry points) copied the skill name from the US
`SkillNames` table - "MEDICE is used!" - where the Tech message already used
the translated `VWFField_TechNames`.  `tools/fieldstrings.py` now emits
`fieldskillnames.bin` (segment 00:003, 54 rows, checked against the 24-cell
field window: widest is "Positron Bolt is used!" at 22) and both sites read
`VWFField_SkillNames`.  Surveyed every other reader of the five name tables:
the rest draw straight from the table (strips/compose) or are the shop and
inventory item paths already on `VWFField_ItemNames`.

## Party Talk is trees 31 AND 32 (2026-09-11)

`lz1DB6F6#0028` printed "hray was Lutz all along" with no portrait.  The
three-byte `$F4` rule (2026-09-06) was applied to tree 31 only, but the
stream spans trees 31 and 32 - the "173 of 173" evidence was 84 + 89 across
both.  Tree 32's 89 messages went out at the two-byte width, so the engine
took the first letter of the text as the mode-4 operand.  `f4_width` now
covers both trees; `treeport --write` re-emits tree 32 with the US operands
(`$F4 $01 $00` ahead of the Thray line).  No row needed retranslating.

## Six-letter party names have no terminator in the record (2026-09-11)

Not a regression of the blind-copy fix: character-dependent.  The
`Character_Stats` name field is six bytes INCLUDING its `$FE` (profession
is the word at +6), so "Forren" has no terminator and the three RAM message
builders that copy the name out of the record (`Win_TechMessage`,
`Win_SkillMessage`, `Win_MacroMessage`) ran 132 bytes into the next record
before finding one - "Forren does not know any field techniques!"
overflowed while Rudy's skills message was fine.  They now call
`VWFMenu_CopyCharName`, which takes the name from `CharNameData` as the VWF
party branch does.  Builds `5341BC7C...` (strips) / `9FC5DF3B...` (composed).

## Vehicle battles never took a pool base (2026-09-11)

`work/compose6-defeat.state`, saved after a vehicle-battle defeat message:
`BattleBase 0`, peak 88, the enemy action mark at 6 with the party HUD's
cells at 10-21 above it (refcounts 46-47: the HUD redraws every frame).
Vehicles bypass `Battle_OpenCharComd`, so nothing captured a base, the
vehicle skill list never rewound (the pool filled to 88), and every
action-window rollback dropped below cells still on screen - the shape of
the "FalThr defeated" flash, which the state itself did not reproduce.
`Battle_VehOpenMainOptions` now captures the base and `Battle_VehOpenSkills`
/`Battle_VehExitSkills` rewind to it, mirroring the character path, on both
builds.  Untested in play.

## Location banner: no stock-length padding (2026-09-11)

The banner sizes and centres a name on its composed width, but the draw
padded it out to the stock entry's character count like every menu name -
"SPACEPORT" -> "AIRPORT" is five cells drawn as nine, four blanks through
the right frame.  Both builds.  `VWFMenu_NoPad` (RAM byte) is set around
the banner's `LoadWindowTiles` and honoured by `DrawStrip` and `DrawName`;
`test_strip.py` checks a padded draw against a banner draw.  Build
`534E9C89...` (strips) / `556A873D...` (composed).

## Status Tech pages: six-cell columns (2026-09-11)

`Win_StatusTechBattle`/`Win_StatusTechCamp` laid two five-cell fixed
columns at x+1 and x+7 in 12-wide windows ($CE/$CF); a composed technique
runs to six cells (Reverser) and the second column's sixth cell was the
frame.  Both windows are 14 wide now, the second column at x+8, FIELD
stepped right two (x=25): COMBAT 10..23, FIELD 25..38 - the screen's last
column.  Seven-cell columns do not fit: that needs 16-wide windows and the
FIELD window would run three columns off screen.  Under `vwf_menu=1`.
Build `D471A493...` (strips) / `D1323A48...` (composed); untested in play.

## Field tech/skill "does not know" message overflowed (2026-09-10)

`Win_MacroMessage` copied a blind 32 bytes of the message after the name;
the batch-2 wording (" does not know{FC}any field techniques!") is 37 bytes
with its terminator, so the window read on into stale RAM.  The copy now
runs through the terminator.  Build `47B72BE3...`.
Same copy in `Win_TechMessage` and the field-skill window (index 0 of their
tables is the same text - the Tech/Skill menu "no field techniques/skills"
case) fixed the same way.  Build `26583CE6...`, 12/12, invariants hold.

## Spaceship destination menu exported and composed (2026-09-10)

Segment `00:008` in `work/script_translated.json`: the "where to?" prompt,
the confirmation tail (" will be{FC}the destination." - the chosen name is
put IN FRONT of it by code, so keep the tail's leading space), and the six
destination names, JP originals from `$2ABC88` in `work/rom.bin`.  The US
had abbreviated the names to seven fixed cells (`A.CASTL`); they compose
now (`VWFMENU_SPACE_LO/HI`, and `VWFField_LoadWindowTiles` for the
RAM-built confirmation), so "AIR CASTLE" fits its 7-cell field and the prompt
has 24 cells to play with.  `tools/spacemenu.py --write` ports them
(sourcebuild runs it); `trpatch8` links `#007` to the place name `AIR CASTLE`
in `00:004`, so rename both together.  Build `5CCFB040...`, 12/12, invariants
hold.  Untested in play.

## Strips vs composition: measured, decision pending (2026-09-10)

`vwf_menu_strips=0` is a real configuration now and `work/ps4en_compose.bin`
is the build to playtest; `ps4en.bin` (`77BE3D86...`) is unchanged.  The
history behind strips, the corrections to the earlier arithmetic (strips
already share identical resident names; "peak 92" came from the 92-slot
build), the harness numbers and what to test are all in
`work/plan-strips-vs-composition.md`, "Outcome".

## Build

- Build command: `python tools/sourcebuild.py ps4en.bin`
- Test ROM: `ps4en.bin` (= `work/ps4en_compose_stable.bin`); experimental `work/ps4en_compose.bin` (`vwf_menu_hash=1`, `vwf_menu_chrome=1`; see 2026-09-15)
- SHA-256: `D8372FE730EF3CEAC8C70E860C7404ABB1C80420E536CE6D7B8CF4422AF7E288` (mixed-case face, composed battle menus, 10-wide field menu, 2026-09-14; the small-caps build `F5565EDC...` is `work/ps4en_smallcaps.bin`)
- **Composition is the shipping configuration (2026-09-14)**: `vwf_menu_strips = 0`
  is the default in `ps4.options.asm`, so `ps4en.bin` IS the composed build
  (`work/ps4en_compose.bin` is kept as a copy of it, so the BlastEm profile the
  savestates in `work/` belong to keeps working).  Decided after the battle and field
  passes above: the equip screen only fits under composition, and its cost
  is now a few frames per list open.  `vwf_menu_strips = 1` still builds
  (last: `27A72499...`) as the fallback.
- Source build only. Do not run the old absolute-address JP-ROM patchers.
- Assembly: zero errors and zero warnings.

## The override table, and why the US invented message slots (2026-09-07)

The last few messages were never missing source: **the US created extra message
slots to hold English that would not fit the JP's message count**, and those
slots cannot appear in a JSON built from the JP.

The ending proves it. The Japanese is two rows -- `lz1E1316#0018`
「光と闇の千年紀は終わりを告げ、」 and `#0019` 「今 新たな時代の幕がひらく…」 --
which the US split across FOUR messages, `$12`-`$15` of tree 42, each with no
engine codes. Our two translations filled `$12` and `$13`, so `$14` and `$15`
still held the US wording: **the player read the closing line twice.** Nobody
would have found that by looking for untranslated text, because the text was
translated; the duplicate was the bug.

`treeport.OVERRIDES` is the honest home for cases no rule should infer. A
heuristic loose enough to reach them would be loose enough to misplace other
rows, and a row written into the wrong message is worse than a message left in
English. Each entry carries the reason it exists:

    (12, 0x5E): 'lz1D2426#0043'   Rocky relocates, so the US carries the scene
                                  once per town; lz1D2426 has 82 rows and this
                                  copy sits at index 94
    (42, 0x14): None              blank: US overflow slots holding a duplicate
    (42, 0x15): None              of our own closing line

`lz1D4FB6#0064` is now `blank: true`. Its `jp` field is EMPTY -- it is
foreshadowing the US invented, with no Japanese behind it, and inconsistent
with the source. Blanking erases it rather than shipping someone else's
addition.

    ported 1569 -> 1573, skipped 3

**Resolved: the blanks stay.** The US's larger row count had already thrown the
prologue's music sync off, so its four beats are not a target worth preserving;
two beats is what the JP does, and it should sync closer. Unverified in play --
nobody has finished this build yet.

**Two corrections to earlier notes in this file about `dlg02`.** It was recorded
that nothing consumes those rows and that their literal `
` characters would
need to become `{BR}`. Both are wrong. The prologue narration reaches the ROM
translated -- "Woven from beyond the reaches of time" sits at `$2C2B94` -- and
the `
` is the CORRECT convention there: it becomes `$FF`, the entry
separator, so "Long ago," and "upon its worlds," are two narration entries like
every other line. Write `
` in that block, not `{BR}`.

**Tree 36 was the last tree in no group**, and it holds two of the biggest
scenes left: `$0` is Zio's death and Frena connecting herself to Nurvus, `$B`
is Zio's speech before the fight. It resolves ONE row of `lz1DDD96`, on a
single `{ctl.F4}`, and tree 33 matches that row just as weakly -- the ambiguity
the group bars exist to reject. The evidence is content instead, checked by
hand, and the indices line up: row `#0000` to message `$0`, `#0011` to `$B`.
`$B` is now an override and reaches the ROM for the first time.

**`$0` is the one message written with OUR controls**, the first sanctioned
deviation from the US build's engine data. The whole divergence is three
controls:

    JP   F9:13 F9:13 F9:13           F2:03B9 F9:27
    US   F2:03B9 F9:09 F2:03B9 F9:09 F2:03B9 F9:27

The US turned Zio's single death cry into three for drama. Mark confirmed it on
video both ways, and the other 38 controls of the message -- operands included
-- are byte-identical between JP and US. So nothing that dispatches, selects a
portrait or ends a scene was ever in dispute, only a sound effect and its
delays; and the usual objection to writing our own controls, that JP operands
may be wrong for this ROM, is answered by every other operand already matching.

`test_treeport_controls` was not weakened to allow it. It reads `OVERRIDES` and
asserts the message against the JAPANESE row's controls instead of the US
build's, so a deviation is only permitted to be the one that was signed off,
and it reports the count: `1 sanctioned deviation(s)`. First attempt skipped
the message and quietly dropped panel loads from 165 to 160 -- the five
`{F2:00}` loads in that very message -- so it now falls through to the
panel-load check rather than short-circuiting.

**Final state: zero messages show US wording.**

The last one was `tree 12 $5D`, and it was never missing either -- I searched
for ワン, the ordinary Japanese bark, and concluded the line did not exist.
PSIV writes Rocky's bark as **ばう わう**, a transliteration of English "bow
wow", so the search was wrong rather than the data. `lz1D2426#0076` had been
sitting translated the whole time.

Nothing automatic could place it. `twins()` compares the SAME index in sibling
trees, and this copy is at `$5D` (93) at the very end of tree 12 -- appended
past eight empty slots, the way quest text is -- while the row targets index 76
in tree 13. Same fingerprint `F4 F7 F4`, same 64 text bytes, different index.
An override, and the entry says so.

Tree 12 is Monsen, and the shape of the tree is the point: townsfolk dialogue
runs to about `$4D`, then blanks, then Rocky's two messages at the end. His
scene is not part of any town's dialogue; a copy is appended to whichever town
he has fled to, which is why the pair turns up four times across three streams.

    ported 1576, skipped 3, messages with text that no row targets: 0

    ported 1574, skipped 3

## The missing Japanese was never missing (2026-09-07)

Went looking for unextracted JP dialogue and did not find any, because there is
none. The 26 streams run contiguously and cover all 43 trees through groups; a
30-entry pointer table at `$10060C` into `$1C00D0`-`$1CAFCC` is something else
entirely (it does not decompress as dialogue). Every message that still showed
US wording had a translated row already -- three separate faults kept them
apart, each found by measuring rather than guessing.

**1. `tree_group`'s bar counted rows instead of weighing them.** A candidate
tree had to resolve three rows to join a group. Tree 6 resolves exactly TWO of
`lz1CE546` -- `#0044` at nine codes and `#0045`, the Alys death scene, at
fifty-eight. Fifty-eight codes cannot agree by chance; the three-row bar exists
to reject coincidence on rows carrying a single `{ctl.F4}`. Now a tree is also
admitted on a distinctive match (>= 4 codes), and tree 6 joined, taking ten
Tonoe messages with it -- Hahn's homecoming and Alys's collapse among them.
Trees in no group at all: 3 -> 1.

**2. Twins.** The US carries some messages in two trees of a group, byte for
byte. A row is assigned once, so every copy but the winner kept its US wording:
rows `#047`-`#054` of `lz1CE546` have identical codes AND identical text in
trees 5 and 6. `twins()` now writes the same translation into each identical
copy. The bar is exact equality of codes and text bytes -- "similar" is not
good enough, because a row written into the wrong message is worse than a
message left in English.

**3.** The portrait and blank-slot fixes recorded above.

    ported 1543 -> 1569, skipped 15 -> 3, untargeted messages 22 -> 7

The last three skips are correct refusals: `lz1D02D6#0056`/`#0087` where the US
has MORE controls than we do, and `lz1DEC96#0043`, nine portraits against a
blank US message and over the two-portrait cap.

The seven that remain have no row anywhere, confirmed by matching their US text
against all 1093 rows that carry one: two dog lines in tree 12, one fragment in
tree 17, two in tree 36 (the only tree still in no group), and the two closing
lines of tree 42 -- "and now the curtain / rises on a new age...".

## Portraits against a blank US message (2026-09-07)

Second pass over what the target_tree fix left behind. Eleven rows were skipped
as "engine tokens 1 vs US 0": our text carries the JP's `{ctl.F4}` portrait and
the US message at that index has no engine codes at all, so `emit` had nothing
to place it against and the US wording stayed on screen. Seven of them are one
NPC group in tree 7.

`drop_portraits_for_blank` drops them. That is what the US already does -- with
no portrait control the line displays under whatever portrait is showing -- so
the trade is the JP's choice of speaker portrait for the translated words, and
`test_treeport_controls` still passes because zero controls are written where
the US has zero.

**Capped at two portraits**, which matters more than the rule. Uncapped it also
fired on `lz1DEC96#0043` (9 portraits) and `lz1E05B6#0000` (19) -- two of the
rows long recorded here as unplaceable. Flattening those would put every
speaker's lines under one portrait, and a US message with no controls facing a
19-speaker JP scene is good evidence the US split that scene across several
messages, so writing the whole row into one is a different operation with a
different risk. Both stay skipped.

    ported 1543 -> 1554, skipped 15 -> 6

The six that remain are all correct refusals: `lz1CE546#0044`/`#0045` (the Alys
death scene: 42 `$F4` plus ten `$F7` scene breaks and six `$F2` events against
a blank US message -- dropping those would cost the cutscene, not a portrait),
the two capped scenes above, and `lz1D02D6#0056`/`#0087`, where the US has MORE
controls than we do, which is a different problem entirely.

**153 -> 27 messages still in US wording**, across the two fixes today.

## 123 messages were being written into blank slots (2026-09-07)

An NPC in Mile still spoke US English -- "the wells and fields have all
withered away" -- while her translation, `lz1CD2E6#0002`, sat finished in the
JSON. Scanning every tree source after a build found **153 such messages across
20 trees**.

The cause is one tiebreak. The US resolved the JP's `{ctl.FA}` branches into
PARALLEL TREES, and `tree_group` already discovers them: `lz1CD2E6` correctly
yields the group `[4, 3]`. Trees 3 and 4 turn out to be complementary halves of
that one stream -- of ~110 indices only 2 hold text in both, and at `$1`-`$3`
tree 3 holds the message while tree 4 is blank. But `target_tree` routed on
engine fingerprints alone, and a row whose fingerprint is **empty** matches
every tree equally, so the tie always fell through to `group[0]`, the base. The
translation was aimed at tree 4's empty slot and written there, where nothing
displays it, while tree 3 kept its US line. Rows carrying a code (`$FA`) routed
correctly all along, which is why the failure looked random.

`tree_group`'s own docstring says empty fingerprints "carry no signal" -- true
for discovering the group, but `target_tree` inherited the same blind spot for
routing. The missing signal is whether a message HAS WORDS at that index, which
`canonical_textlen()` now reads from the untouched `.bin` and `target_tree`
uses as its tiebreak: an exact fingerprint match on a populated message beats
an exact match on a blank one.

Result: **153 -> 30 messages still in US wording.** The porter's totals do not
move (1542 ported, 13 skipped, before and after) because the same rows are
written -- only the destination changes: tree 1 82->54, tree 2 15->43, tree 3
14->33, tree 8 4->24, tree 10 16->45, tree 13 13->28. `test_treeport_controls`
passes, which is what proves the assembled controls still equal the US ones.

The remaining 30 are listed in `work/us_text_remaining.md`; most look like rows
we never translated rather than rows that failed to land.

## Enemy names never reached the ROM (2026-09-07)

The game showed HELEX and PROTECTBIT while `script_translated.json` said Herex
and Protector Bit. `trpatch8` validated those tables and `test_paths` checked
their address, but **nothing wrote them**: the ROM kept the US build's own
list. They render through the menu VWF at runtime, so they LOOKED like our
text -- the face was ours, the words were not. Same failure as the item
descriptions before `itemdesc.py`.

`tools/enemynames.py` ports both tables and runs from `sourcebuild.py`.
Verified after: 150 of 152 enemy names and 111 of 112 skill names now appear in
the ROM (the misses are short strings the search filter skips), and the table
decodes as Herex / Monster Fly / Gunner Bit / Protector Bit.

Two details it has to respect: seven slots carry a trailing comment naming the
boss they belong to (`dc.b "NOTHING", $FF  ; Dark Force (1)`), which is the only
record of which blank slot is which; and `EnemyNames` has 153 slots against 152
JSON rows, so the last is left alone rather than guessed at.

## Monster naming pass (2026-09-07)

Applied: ゴルダイン Goldine -> **Goldyne** and ワイヤーダイン Wire Dyne ->
**Wiredyne** (one suffix, ダイン = dyne, previously spelled two ways, and the
JP has no separator); ゲロトラックス Gerotrax -> **Gerothrax** (アントラックス =
anthrax attests トラックス = -thrax); ゾランバルト Zoranbalt -> **Zoranbult**.

Zoranbult is the interesting one. Dutch *bult* "bump, hump" is /bʊlt/, which
would give ビュルト -- but read as ENGLISH spelling, /bʌlt/, Japanese gives バルト
exactly. Then `ps4built.prev.bin`, the last build before the porter ran, turned
out to still hold the US table: it says **ZORAN BULT**. Two readers a world and
thirty years apart landing on the same word is worth more than either alone.

Method notes from the same pass, both mine to learn:

- I proposed name families from ORTHOGRAPHY -- "-farg", "-balt" -- without
  checking what the creatures are. Gi-Le-Farg is a sorcerer and Silvalt is
  mechanical, so neither family existed. Creature identity decides these; the
  user has it and this repo does not.
- エイブフロッグ stays **Ape Frog**. I argued エイブ cannot be "ape" because ape
  needs エイプ -- true, but under the mis-transcription model that explains
  Xenophage and Zoranbult, a mis-voiced "ape" is exactly what it looks like,
  and "Abe" means nothing for a frog.
- A sprite sheet's labels are usually the US names copied off a wiki, not
  independent evidence. Do not count them twice.

Settled: ゼナファーグ ships as **Xenophage** and ガイスファーグ as **Gaisphage** --
restore the morpheme we understand, transliterate the one we do not, and keep
the palette swap looking like one species. ガイス itself stays unsolved: the blue
one additionally poisons, but no poison word reaches ガイス, so the trait is
probably not in the name. The rules are in `work/glossary.md`.

## Automated playtest harness (2026-09-07)

BizHawk 2.11 installed via winget (`TASEmulators.BizHawk`); it is a .NET
Framework build, so the absent dotnet CLI does not matter.

    python tools/playtest.py            # runs ps4en.bin, writes work/playtest/

- `tools/bizhawk_ram.py` generates `tools/bizhawk/ram.lua` from
  `ps4.constants.asm`, so the addresses the harness reads cannot drift from the
  ROM they are read out of.
- `tools/bizhawk/harness.lua` drives the pad, waits on STATE rather than frame
  counts, screenshots, and writes `log.txt` with a RAM line beside every shot.
- `tools/playtest.py` launches EmuHawk, then prints the log and lists the PNGs.

Three things cost a run each, all worth writing down:

- **`.bin` hangs it.** BizHawk cannot infer a platform from that extension and
  puts up a picker dialog; with nobody at the keyboard the first run sat on it
  for the full timeout and produced nothing. `playtest.py` now stages the ROM
  as `rom.md` beside the screenshots.
- **The buttons are not the obvious ones.** From the game's own equates,
  `ButtonCancel = $10 = B`, `ButtonSpeak = $20 = C`, `ButtonCamp = $40 = A`.
  Advancing dialogue with B and opening the menu with C left the walk sitting
  on the START screen for forty taps.
- **Timing the title press drops into the attract demo.** It reaches field
  control looking perfectly healthy with `Current_Money` still 0, which is the
  tell. Press Start until a window appears, confirm until money is non-zero.

Not finished: the walk still does not reach the camp menu. "Mode 12 with no
windows open" holds for a moment between two message boxes, so it reads the gap
in the Hunters Guild opening as field control and the later taps just advance
more dialogue. It needs a stronger in-control test -- a settled dialogue tree,
or probing that a direction press moves the party. Until that lands, **the
meseta row fix has not been verified in game.**

What the shots do prove: translated dialogue renders correctly through the VWF
("This is your first job as a registered hunter. Put your back into it!"), and
a run costs about 30 seconds start to finish.

## The row fold fired twice: "00" one line above the "5" (2026-09-07)

500 Meseta on the party screen drew its last two digits one row high. The cause
is two folds where there should be one.

A plane row is $80 bytes -- 64 cells -- and wraps onto ITSELF: passing column 63
returns to column 0 of the same row. `LoadWindowTiles` enforces that after every
character at `loc_69ACA`, testing `a1 & $7F == 0`. `VWFMenu_DrawString` writes a
whole run at once, so it enforces the same rule per cell through
`VWFMenu_RowWrap` -- **including after the last cell**. But a fold leaves `a1`
at column 0, which is exactly the condition `loc_69ACA` tests, so a run whose
final cell sat in column 63 was folded again the instant it returned, and every
cell after it went a row up.

It is value-dependent, which is why it took this long to see: the run has to
END on the boundary. `Win_MenuMeseta` draws ten cells -- seven blanks then
"500" -- and at that field's geometry the boundary falls right after the "5".

Fixed at `VWFMenu_DrawString_Exit`: if the wrap flag is set and `a1` came to
rest on a boundary, add `$80` back and let the caller's single fold stand. A
zero-length run starting at column 0 is unaffected, the +$80 and -$80 cancel.

`test_wrap.py` grew the case. The invariant is not "never return on a boundary"
-- the un-folded state IS a boundary, and that is what stock's per-character
loop would leave -- but **model the caller: fold at most once, then check the
column**. With the fix disabled the new case reports `ROW+-128`, one row up,
which is the bug exactly.

## What the naming policy actually is (2026-09-06)

Stated by the user after I had drifted into treating any printed English as
authority: **an accurate transliteration of the Japanese ROM's katakana,
informed by etymological research, juxtaposed against modern official
material.** Three inputs, in that order of standing.

The 1995 US localisation is explicitly **not** an input. It is what this
project replaces, and its names were clipped to about five characters by a
menu window the VWF has removed. So "official" here means the roman-letter
FOIE in the Japanese guide art and the forms Sega has maintained from PSO
through NGS -- not Foi, Wat, Gra, Hinas-as-a-US-name.

ヒーナス -> **Hinas** on that basis. Not because the US release printed it, but
because the German reconstruction was wrong and a plain transliteration is
right: *hinaus* is [hɪˈnaʊs] and would give ヒナウス, so the long ヒー and the
absent ウ both contradicted it, and it stood only on a pairing with Rückkehr
that is now Ryuker. ヒーナス clips to Hinas under the same convention that gives
Megid from メギド and Drunk from ドランク.

Two glossary corrections went with it:

- "**Kept**, because Sega has never printed an English form" was false and I
  could not have checked it -- there is no US ROM in this repo, every image
  here is either the JP original or our own build. The US release named all
  forty techniques. The claim carries no weight under the policy above, but it
  should not have been written.
- The etymology table still listed Feuer / Water / Glanz / Geron / Ruckkehr in
  its EN column after the rename, which would have led a later pass to
  "restore" them. It now has separate `origin` and `ships as` columns and says
  in its header that it is research, not an instruction.

## Party Talk eats the first letter: the real cause (2026-09-06)

Reported twice and "fixed" once wrongly. `TextCtrlCode_Portrait` reads a
**second** operand byte when `Game_Mode_Routine == 4`:

    move.b  (a0)+, d0               ; portrait id
    cmpi.w  #4, (Game_Mode_Routine).w
    bne.s   loc_6A19E
    move.b  (a0)+, ($FFFFEC9D).w    ; mode 4 only

Party Talk is mode 4, so `$F4` is three bytes wide there and two everywhere
else -- a width that depends on the mode the message is dispatched in, not on
anything in the bytes. Every parser here read it at the usual width, so the
second byte decoded as a leading kana on the next line ( , い, あ). It looks
like noise, a translator deletes it, and at run time the engine consumes the
first letter of the English as that operand instead: "Both the principal and
Hahn..." printed as "oth the principal and Hahn...".

`lz1DB6F6` / tree 31 is the Party Talk stream and demonstrably the only one:
the byte after `$F4 xx` is below `$10` in **173 of 173** cases there, where
every other stream is a mix of real text.

The earlier diagnosis -- `treeport`'s `.strip()` eating a leading space -- was
wrong, and looked right for one message only by luck: that message's extra byte
happens to be `$00`, which decodes as a space, so preserving the space
preserved the operand. Every message whose byte is `$01`/`$02` still broke.

Fixed at the source rather than in the text: `treeport.f4_width()` returns 2
for tree 31 / `lz1DB6F6`, and both `canonical_engine` (US side) and
`jp_engine_codes` (JP side) use it, so the operand now comes from the US tree
as engine data like any portrait id. **No row needed retranslating** -- the
emitter writes `$F4 $02 $00` ahead of "Both the principal...". One leftover was
cleaned up: `lz1DB6F6#0000` still carried the old `$00` as a literal space.

`test_treeport_controls` caught the half-done version immediately -- it parsed
the source at the old width and reported tree 31 message $0 as
`[(244, (1,))]` against canonical `[(244, (1, 0))]`. It now shares the rule.

## A name change cost two builds, twice (2026-09-06)

`sourcebuild.py` never ran the 8x8 generators. `menustrip.py` and
`fieldstrings.py` both read `work/script_translated.json`, so changing a single
name left `ps4disasm/vwf/*.bin` stale. The only thing that ran them was
`checkbuild.py`, which regenerates them in order to compare against what is on
disk -- so it reported the change as **FAIL** and, as a side effect of the
comparison, wrote the fresh files. That is why the next build always passed and
the failure looked transient. It is not: it fires on any name edit, and it hit
twice in one day (a hand edit to the script JSON, then Rebirther -> Reverser).

The generators now run in `sourcebuild.py` before `checkbuild`, in checkbuild's
own order. That also retires the bug checkbuild was watching for -- "edited a
generator without re-running it" is now impossible rather than merely detected.

Proof it changes no output: with `Rebirther` restored, the build reproduces
`236C5641...` exactly, the hash from before the rename, first try.

## Rever: `Reverser`, not `Rebirther` (2026-09-06)

`r00s002#035`, JP リバーサー. Renamed on the balance of three arguments, none
of them conclusive on its own and no primary source found:

- Sega's own English for the identical katakana is **Reverser** (PSO), and PSO
  carries PSIV's technique vocabulary across wholesale.
- The US "Rever" is the first five letters of *Reverser*; it is not a prefix of
  *Rebirther*. PSII already used リバーサー, so "Rever" truncates that name.
- The PSIV manual describes the target as 瀕死状態 -- near death, not 死亡 --
  a state being reversed rather than a death being undone.

Against: the PS1-era ancestor spell in *Out Side Saga* is リーバス, defined as
reviving a dead person, which is rebirth-flavoured -- and リーバス is neither
English word (both give リバース, long vowel on the second mora, not the first).
It is likely a series coinage on which both readings are folk etymology. That
does not change the call: when Sega had to write it in English they wrote
Reverser. Confidence ~85%, not settled. What would settle it is an official
Japanese source printing the name in roman letters; the Compendium has no
technique list at all, so it is not that source.

## The ending farewells, and two collisions (2026-09-06)

`lz1E1316#0011`, 1200 JP bytes: the goodbyes on Motavia -- Raja and Shess back
to Dezolis, Frena to Zelan, Forren's charge to Fal, Pyke to Tonoe, Hahn to the
Academy, and Thray's parting. Pairs with tree 42 message 11. Eleven surplus
tokens, all `$F9` delays, so `drop_extra_delays` places it with no new rule.

Raja's last pun, キカイ as 機械 (machine) and 機会 (chance): "no spaceship, which
is to say no kikai". Rendered "We've no SHIP -- and that SHIP has sailed!"

Two rows had drifted while this was being written, both from hand editing, and
both would have shipped silently:

- `lz1DDD96#0008` had Rudy's departure line written under the `{ctl.F4:01}`
  that was deliberately left empty. The US tree has no slot for a line there,
  so the whole 789-byte scene was skipped and would have shown US text in game.
  The words are kept -- moved into Rudy's previous page, where he has a slot --
  and the token is empty again. **If a line has to be added at that point, it
  has to go in a page that exists.**
- `lz1DEC96#0018` and `#0019` had picked up `#0017`'s `{ctl.FA:9B02}
  {ctl.FA:9801}` panel loads along with its shared opening quotation. Their own
  JP rows have no tokens and the US messages have no controls, so both were
  skipped. Tokens stripped.

The lesson is the same as the earlier hand-editing pass: `trpatch.py check`
catches the second kind (tokens the JP does not have) but not the first, which
only shows up as `treeport` skipping the row. **After hand editing, read
`treeport`'s ported/skipped counts, not just the check.** 1542 ported, 13
skipped is the current baseline.

## `lz1DDD96#0008`: carrying a line the US cut (2026-09-06)

Zelan after Kuran: the systems are restored, the Dezolis blizzard is not, Raja
gets to say he told them so, and Forren produces the Ice Decker. 789 JP bytes,
paired with tree 35 message 8.

One token more than the US: an `{ctl.F4:01}`. The US build cut Rudy's "Right!
Then we set out as soon as we're ready!!" between Forren loading the Ice Decker
and Thray's closing line, so the tree has no slot for those words. The row
keeps the JP's portrait token with **nothing written under it**, which is the
honest record -- the token mirrors the JP, and the line the US dropped stays
dropped rather than being silently reattributed to Forren.

Two narrow changes to `drop_extra_control` to carry that:

- an `$F4` may be dropped when it governs no words, not only when it re-sets
  the portrait already showing. The guard exists so no line ends up under the
  wrong portrait; a portrait change with no line cannot do that.
- a candidate that fails a guard is now **skipped** rather than ending the
  search. The tail of this message is an alternating run of `$F4`s, so nine
  positions align by code sequence alone and the first of them is Raja's real
  portrait change. Every position still returned has passed both guards, so
  searching further cannot widen what is accepted.

Measured, not assumed: the "ported with a control the US does not have" list
goes from 6 rows to 7, the new one being this row's `{ctl.F4:01}`, and the
other 6 are unchanged. `test_treeport_controls` still passes, which is what
proves the assembled controls still equal the canonical US ones.

Also: `paralyses` -> `paralyzes` in `lz1DDD96#0010`, the only British spelling
a scan of the whole file turns up. The vehicle is the **Ice Decker**, which is
what `script_translated.json` calls the item; the US script says Ice Digger.

## The Lutz revelation and the Elsydeon send-off (2026-09-06)

`lz1D6816#0047` (1511 JP bytes: Shess learns Lutz is dead, Thray is the fifth
Lutz) and `lz1D6816#0048` (Thray sends Rudy in to meet Elsydeon). Both had no
`us` field, and both pair with tree 20 messages 47 and 48. The engine tokens
agree exactly as multisets; the only difference is that the US moved three
`$F2` event codes (and one in `#0048`) to the far side of the adjoining `$F4`.
`match_us_order` accepts that swap when nothing but the two tokens lie between
them, so the only constraint on the English was to keep `{ctl.F2:000100}`
against its `{ctl.F4:04}` rather than mid-sentence where the JP fires it -- and
the front of the line is where the US fires it anyway. Both port with no drop
rule: `ported 1538 -> 1540`, skipped unchanged at 13.

Terms taken from what the file already uses, not re-coined: Lord Lutz,
telepathy ball, Black Wave, Dark Falz, Profound Darkness, Gungbius Grand
Temple, Gallberg Tower, Eclipse Torch, Thray Walsh.

`lz1D4446#0015`/`#0017`: the Gyuna pun, reworked twice. 事情通 (well-informed)
misheard as 2の自乗 (two squared) works because the praise word IS the sum when
you mishear it. Two attempts failed for the same underlying reason:

    FOUR-warned                     bends *forewarned*, a different word
    "Two squared is four...         the sum comes from nowhere -- nothing in
     and he's well-inFOURmed!"      the villager's line sounds like a sum

    "Well-inFOURmed, is he?          the sum is now motivated but redundant:
     Two squared, no less!"          it only restates the FOUR just found

    "Just the man I've been              FOUR is only the sound *for*, twice.
     looking FOUR!"                      Remove the capitals and the line is
                                         unchanged: the number is decoration

What the Japanese does that none of those did: 2の自乗 consumes every syllable
of 事情通, and it stays a NUMBER once extracted -- a compliment that turns out
to be arithmetic. So the hidden number has to behave numerically, and the
place to spend it is the villager's own word "best":

    best informed man for miles
    -> "Best-inFOURmed? Then there are three men ahead of him! Hoho!"

Four is read as fourth, which contradicts "best" -- one bent word, and the
number does the work of deflating the praise.

Three lessons worth keeping. For a mishearing joke, check the thing misheard is
actually present in the English setup -- a punchline can be built correctly on
a setup that was never translated into place. When a pun needs a clause to
explain why it is a pun, it is not finished. And test a capitalised word by
lowercasing it: if the line reads the same, the marking is decoration and the
pun is not there.

## Pun pass: reworked, then reverted (2026-09-05)

Raja's hidden-word puns -- HORN-est, FOUR-warned, ICY-nough, en-TYLER-ly, "I
can't BEER to pass it by" -- were rewritten onto single double-meaning words
(SPIRITS, STANDING, SUM, COMPANY, COLD, CHILLS, GRAVE) on the argument that a
bent spelling reads as a typo in English where katakana does not in Japanese.

**Rejected, and the originals are restored.** The device reads fine in play and
carries Raja's voice; the replacements read as ordinary lines with a word
shouted in the middle. `work/glossary.md` now records the whole set as kept on
purpose, so a later pass does not sand them down again. The two-meanings test
still applies to the other kind of pun -- one word used twice -- which is what
"unBEARable ... but they BEAR it" failed.

Not reverted, because they were not part of that argument: the American English
fixes from the same pass (`aught` x3, `the lot of you`, `by all accounts` x3,
`that's old nonsense, that is`, `an odd lot`, `mind you` x2, `haven't the
money`, `ought to`, `got to` x2, `fairly spinning`, `how splendid`), and three
pun rows outside the table -- `lz1D4446#0020` (TAILOR-made -- TYLER-made),
`lz1D5A26#0093` (WOEful -- since replaced, see below), `lz1D5A26#0095` (PAIN of it / REFRAIN from it).

`lz1D5A26#0093` redone 2026-09-11: JP is a groan (うーん) that is also the word
for luck (ウンが悪かった). "Oh, woe... woe... And WOEful luck it was" kept the
shape but not the mechanism -- woe is not a noise and woeful is an ordinary
word, so nothing was hidden. Now "Augh... augh... What AUGH-ful luck...":
a real pain groan bent into *awful luck*, which is the JP sense.

The other two bedside lines were sound gags that only track the Japanese --
`#0094` くくくく (a groan) into くく81 (the 9x9 times table), rendered as "Five OWs
-- and five fives are twenty-five"; `#0095` クルシー/ユルシー (it hurts / let me off),
rendered as "The PAIN of it / REFRAIN from it". Neither read as a joke in English,
so both are rebuilt from the situation instead (Raja feverish in the Meese inn
that the innkeeper has grudgingly turned into a ward, and itching to get up --
`#0096`): "an inn for a sickroom... That makes me an INN-patient -- and an
impatient one at that!" and "the nurse says I'm running a fever... Running! I
can't even sit up!" Each has two real meanings that are both true of the scene.

`lz1D5A26#0098`, same pass: Fal's 死んじゃう (he'll die) is answered by Rudy's
ハハハ…信じらんない (I can't believe it) -- a sound echo, which is why he laughs and
why Fal says it is no laughing matter. "Haha... I can't believe it" kept the
words and lost the reason for the laugh. Now "Haha... I thought he was just
dying for a laugh...": *dying for* (craving) against *die*, and it is what Rudy
actually believed at the top of the row ("cut it out, that's a sick joke").

## `lz1D38E6#0008`: the Raja scene, and a third drop rule (2026-09-05)

The crash landing on Dezolis and the party's first meeting with Raja, 1138 JP
bytes and the largest untranslated row left. It had no `us` field, which made
it look unpaired; it is not. Tree 14 message 8, read out of the untouched
`ps4disasm/script/dialogue 14.bin`, is the same scene, and rows 0-7 and 9-12 of
the stream sit on messages 0-7 and 9-12 either side of it. `usimport` never
wrote the field because its matcher wants the control sequences to agree, and
the US build dropped four tokens here:

    {ctl.F2:08} {ctl.F9:59} {ctl.F2:09}   the sound gag after Raja's pun
    {ctl.F9:1D}                           one delay

The `us` text is now recorded on the row, decoded from that `.bin`, so the
pairing is in the data rather than in this file.

`treeport` still could not place it: `drop_extra_control` takes exactly one
surplus and `drop_extra_delays` takes `$F9` only, so four surpluses of two
codes fell through both and the scene was skipped. **`drop_surplus`** is a
third rule, tried last, that drops `$F9` delays and `$F2` events -- `$F2` only
under `drop_extra_control`'s adjacency guard (no prose on both sides), and
`$F4` never, because losing a portrait change loses who is speaking.

Its blast radius was measured rather than assumed: with the rule stubbed out,
`ported 1537, skipped 14`; with it, `ported 1538, skipped 13`, and the extra
row is this one. `test_treeport_controls` still passes, which is the thing that
matters -- adding a control the US lacks breaks that invariant, taking one away
leaves the assembled controls exactly as the US build has them.

The JSON keeps all 58 JP tokens. That is deliberate: `trpatch.py check` proves
`en` carries the JP's engine sequence, and that check is what catches an
accidentally deleted portrait. The build adapts; the record does not.

## Editing `dialogue_full.json` by hand drops tokens (2026-09-04)

A hand-editing pass over the JSON lost four control tokens and introduced one
overlong line. None of them are visible while reading the English -- the text
looks finished -- and only two of the four are caught by the existing check.
Run **both** audits after any manual editing session:

    python tools/trpatch.py check work/dialogue_full.json

catches engine-token drift against the JP (`$F4` portraits, `$F9` delays, `$F2`
events) and characters outside the English charset. It does **not** see `{BR}`,
because `{BR}` is layout rather than an engine token.

    # rendered-line width, using the real VWF advance table
    python - <<'PY'
    import io, json, re, sys; sys.path.insert(0, 'tools')
    import dialogue_reflow as R
    d = json.load(io.open('work/dialogue_full.json', encoding='utf-8'))
    for e in d['entries']:
        for p in re.split(r'\{BR\}|\{ctl\.F[D57]\}', e.get('en') or ''):
            t = re.sub(r'\{[^}]*\}', '', p)
            if R.px(t) > R.LIMIT: print(R.px(t), e['id'], t)
    PY

catches a lost `{BR}`, which shows up as a line past the 255px window.

What was found and repaired:

| row | lost | symptom |
|---|---|---|
| `lz1E1F06#0004` | leading `{ctl.F4:08}` | no portrait on the opening line -- the Party Talk failure again |
| `lz1E1F06#0004` | a `{BR}` | 366px line, more than a window and a third |
| `lz1E1F06#0005` | one `{ctl.F9:27}` | the third beat of Daughter's dying "Fo...rre...n" |
| `lz1E1316#0009` | a `{BR}` | 379px, and "dimensionover Motavia" with the space eaten |
| `lz1CE546#0045` | a `{BR}` | 319px, "leave it to me!We have the Land Master!" |

Three U+2026 ellipsis characters also arrived in `lz1E1F06#0004`, presumably by
paste. They have no slot in the English font and they stop the build outright,
which is the one failure mode here that cannot ship by accident.

## Item descriptions and the sound test now reach the ROM

`sourcebuild.py` generated the name tables from `script_translated.json` but
nothing carried the **item descriptions** (`01:003`) or the **sound-test track
titles** (`01:004`) into the disassembly, so both still shipped the text the
source build already had. Editing those segments in the JSON changed the ROM
not at all -- the first build after 158 new descriptions was byte-identical.

Two porters now run from `sourcebuild.py`:

- `tools/itemdesc.py` rewrites `InventoryDescriptions` and its `$FE`-terminated
  twin `InventoryDescriptions2` as plain `dc.b` strings. They assemble through
  `script/charset.asm`, which already carries `.` `'` `,` `-` `!` `?` `:`, so
  nothing needs new glyphs. The block boundary is the *next label*, not the
  next table: two short unrelated strings sit between the two copies and
  overwriting them would take the shop's "equip" with them.
- `tools/soundtest.py` rewrites the raw byte table at `loc_2AFA28`. That one is
  in the high bank -- capitals at `$80`, digits at `$9A`, and only the four
  punctuation glyphs a Japanese font happens to have, `$B0 -` `$B1 !` `$B2 ?`
  `$B4 .`. No apostrophe exists there, which is why `JIJY NO RAG` keeps the
  composer's own romaji rather than becoming "The Old Man's Rag".

### Two encodings, not one

Worth writing down, because it cost time twice. The 8x8 bank has **two**
unrelated code layouts:

| | capitals | lowercase | used by |
|---|---|---|---|
| `script/charset.asm` | `$01`+ | `$1B`+ | the source build's `dc.b` strings |
| `tools/slotmap.py` | `$80`+ | `$01`+ | the legacy JP-ROM patch path, and `trpatch8 check` |

`ps4built.bin` is the **US reference build**; the playable ROM is `ps4en.bin`.
Both tables were derived from real data -- slotmap's `$80` capitals are exactly
what the JP sound-test bytes use -- so neither is wrong, they are just
different fonts. Check which one a table belongs to before trusting a code.

`slotmap` gained `!` `?` `-` (the ROM's own high-bank glyphs, `$B1 $B2 $B0`)
and drew `.` `'` `,` into `$53 $54 $55`, matching `wincharset.asm`'s own
numbering so the two encoders agree. `english8.encode` now passes `{XX}` tokens
through as raw bytes, which item descriptions need for `$FC`. This is what lets
`trpatch8 check` accept the descriptions; the bytes that actually ship come
from `charset.asm`.

## Translation status

- `dialogue_full.json`: 1565/2170 (72.1%). **Every portable row is translated**
  -- `tools/wave.py` reports 0 remaining across 0 streams. What is left is rows
  whose JP fingerprint has no unambiguous US counterpart, plus blank slots and
  bare `{ctl.F6}` event markers.
- `script_translated.json`: 820/827 (99.2%). The 7 remaining are genuinely
  blank slots; `fieldstrings.py` supplies a `NOTHING` sentinel for the unused
  item IDs.
- treeport: 1534 ported, **18 banked but not placed**, 2 surplus controls
  dropped to match the US build (`lz1CF6D6#0003`, `lz1CF6D6#0038`).

## Investigated: can the banked rows be placed? (2026-09-03)

Attempted, working, reverted. Recorded because the reasoning is worth keeping.

**The operand fear was unfounded.** Comparing JP operands against US operands
in every message both builds kept:

| control | identical | differ |
|---|---|---|
| `$F4` portrait | 1819 | 2 |
| `$FA` flag/branch | 513 | 0 |
| `$F2` event/panel | 181 | 0 |
| `$F7` scene step | 74 | 0 |
| `$F9` delay | 39 | 1 |
| `$F6` event return | 0 | 64 |

The three non-`$F6` disagreements are US *content* edits, not id remapping --
`lz1D02D6#0071` swaps a portrait, `lz1D6816#0049` retimes a delay. The id
namespaces are identical. `$F6` is the real exception: it is a tree-only
control and the JP messages carry no operand for it at all -- but no banked row
uses `$F6`.

**So operands are not the blocker.** A rule was added: when the US message is
completely empty -- no controls *and* no text -- it cannot be the wrong message,
because there is nothing there to displace; if our own controls are all
self-contained (`$F3 $F4 $F7 $F9`, which cannot dispatch anywhere) take their
operands from the JP. That placed **12 of the 18** banked rows, including Le
Roof's first scene on Rykros (19 controls), Zio's warning, the Dark Falz
encounter, Saya's introduction at Krupp, and the seven Molcum/Tonoe examine
lines. `ported` went 1534 -> 1546.

**`test_treeport_controls` rejected it**, correctly. That test asserts a tree's
assembled controls equal the canonical US controls read from the untouched
`.bin`; writing a control where the US had none breaks the invariant. It is the
same guard that caught the `$00F2` panel lock. There is no evidence the engine
ever dispatches to those empty messages, so the payoff is unproven while the
downside is a hard lock -- the guard wins.

The change was reverted and the 12 polluted `.asm` messages restored to bare
`dc.b $FF`. The rebuild is bit-identical to the pre-attempt ROM
(`A57E79EB...`), which is what proves the revert was complete.

### Traced: the engine does not dispatch to any of them

The missing evidence was whether the engine ever reaches those message indices.
It does not. A message index *is* the dialogue ID -- `GetDialogueByID` walks
`$FF` terminators from the current tree's base `id` times -- so an index is
live only if something supplies that ID. There are three suppliers, and all
three come up empty:

1. **`$FA` branches.** A dialogue can redirect to another ID (`$FA` carries
   `[event flag, target id]`). No `$FA` in any tree targets any of the 12.
2. **Map objects.** Byte 4 of a 10-byte object record is the dialogue index,
   and each map names its tree with a `dc.l DialogueTreeN`. Across 361 map
   blocks, none of the 12 is referenced. The one apparent hit -- tree 41 `$00`
   in the Courage and Strength towers -- is the *unset* value, not a pointer:
   294 of 927 objects (32%) carry `$00`, in 56% of maps.
3. **Event code.** Events load dialogue with `move.b #id,d0; jsr
   GetDialogueByID`. Of the 12, only ids that also exist in *other* trees ever
   appear, and every such site resolves against a different tree: `$0F $10 $11
   $13` under DialogueTree26/27 (the Guild windows), `$12`-`$15` under
   DialogueTree42. Ids `$2C`, `$16`, `$0C`, `$0B`, `$2B` are never loaded by any
   event at all.

**Where the Tonoe bazaar text actually lives.** Those tree-7 rows read like
searchable scenery because they *are* -- the bazaar stalls are examinable like
a bookshelf or a sign, with no shop flow. But searchable scenery is dispatched
by an Interaction Area calling `InteractionRoutines` entry 0,
`Interaction_DisplayDialogue`, and that routine does not use the map's tree at
all: it loads a per-**world** examine tree from the table at `loc_58934`
(DialogueTree28 for Motavia, 30, 29 for the rest) and then resolves byte 10 of
the record against it. `Map_Tonoe` calls routine 0 with ids `$74`-`$7A`, and
tree 28 `$75`-`$7A` holds precisely that text -- "Looks like they're closed for
the day...", "The shopkeeper's asleep..." -- already translated and live as
`lz1DA026#0117`-`#0122`. The JP kept these lines in the town stream; the US
consolidated them into the shared examine tree and left the town-stream copies
empty. (It kept two of the set, tree 7 `$E` and `$12`, which duplicate tree 28
`$74`/`$78`.) So the scenery is searchable and the text is in the game -- the
tree-7 copies are stranded duplicates.

So the US build cannot reach these messages, which is presumably why the
localizers emptied them. Filling them would be dead data. That is a second and
independent reason the revert was right: the change broke a load-bearing
invariant *and* bought nothing.

Two traps for anyone re-treading this. `canonical_engine` returns `[]` for a
message with text but no controls, so "empty" must test the *text* too. And an
object list must be parsed as strict 4-line records -- a loose `dc.b x, y`
regex matches treasure-chest coordinates and invents reachability that is not
there (it briefly showed 4 of the 12 as reached).

## Why 10 translated rows do not reach the ROM

18 untranslated rows target a US message slot that **exists but is empty** --
the localizers dropped the line. Nothing would be displaced by writing there,
so these looked restorable, and 10 of the smaller ones were translated to test
it. treeport skipped all 10.

The reason is the guard that fixed the `$00F2` panel lock: **control operands
come from the untouched compressed US tree, never from the translated
assembly.** An empty slot carries no operands, so there is nothing to source
and the row cannot be emitted safely. Synthesizing operands from the JP hex is
exactly the shortcut that produced the earlier hard lock, so it was not taken.

Those translations are banked in `dialogue_full.json` and will land the moment
a safe operand source exists. By decision, the large cutscenes were translated
too, on the same banked terms:

- **Laila's death at Krupp** -- `lz1CE546#0044`, `#0045`, `#0046`. `#0046` is
  the longest row in the project: her death, Rudy's grief, Thray's counsel,
  Fal's speech on leaving the Bio-plant, and Hahn's departure.
- **Le Roof on Rykros** -- `lz1E05B6#0000` (the fourth planet and the rite),
  `#0011` (the whole creation of Algol: the Great Light, the Profound Darkness,
  the seal of three worlds, Dark Falz as its escaped hatred, and Rudy's refusal
  of the whole idea of a destiny), `#0012` (Thray: "truth is not one thing").

- **Zio's fall and Frena's sacrifice** -- `lz1DDD96#0000`: Zio abandoned by his
  god, Pyke's cry, Frena linking herself into Nurvus to force an override, and
  Pyke leaving the party for his little sister. `#0011` is Zio's warning before
  the final fight.

**Every row with translatable text is now translated.** What remains untranslated
is empty slots, bare `{ctl.F6}` event markers, and the `dlg*` shop/inn strings
that have no safe porting route (above).

Banked rows cost nothing at build time -- treeport names them and moves on, and
every check still passes.

## Playtest fixes (2026-09-03)

**Save confirmation drew a garbage tile for the file number.** The code builds
the message with `move.b (Window_Option_Index_2),d0 / addi.b #$9B,d0`, and $9B
is the *system font's* digit '1'. But the string is assembled under
`wincharset` (`31`=`-`, `06`=`F`, `41`=`i`, `53`=`.`) and
`VWFMenu_DrawString` sends any code >= $80 down the graphic path instead of the
font, so it drew an arbitrary tile. wincharset digits start at $1B, so slot 0
is `$1C`. Fixed at both save-message sites. This is a VWF-menu regression, not
inherited: with the stock font `$9B` really was '1'. The slot list at line
87110 uses the same `$9B` idiom and renders correctly, so those two windows
take different draw paths -- worth remembering if another number turns up wrong.

**The first Party Talk loses its portrait and its leading "I" -- OPEN.** An
early "fixed" reading was a false positive; it recurs from a battery save.

`treeport` was calling `.strip()` on the English before emitting, so a fix
that restored the byte the US carries between the portrait control and the
first letter never reached the ROM at all -- the experiment was never actually
run. That strip is removed; it silently ate leading spaces from every row (15
rows had one, none had a trailing one). `lz1DB6F6#0000` now assembles to
`f4 01 00 09 00 31 ...`, **byte-identical to the US original**. If the symptom
survives that, the cause is not our text: look at the portrait/panel load or
the VWF tile pool, not the script.

Savestates remain a hazard for the whole playtest: the game keeps ROM pointers in work RAM (`Current_Dialogue_Tree` is a
longword ROM address) and our data moves between builds, so a savestate made on
one build is not valid on another. Battery saves are.

Two dead ends worth not repeating. `$F4` does **not** take two operand bytes:
across all 2237 of them in the trees, the byte after the operand is $09 I,
$17 W, $14 T, $01 A, $08 H -- the frequency profile of English sentence-initial
capitals. And restoring the leading space the JP and US both carry after the
portrait control (33 rows drop it) changes nothing structural; it was applied to
`lz1DB6F6#0000` for parity only.

**Four menu strings reworded** -- these live in `ps4.asm`, not in any JSON, and
sit outside every porter's block:

    Can't have any items!            -> You have no items!
    <name> cannot use / the special skill! -> <name> cannot use / skills here!
    <name> cannot use / the Technique!     -> <name> cannot use / techniques here!
    No equippable item.              -> Nothing to equip.

`" cannot use"` is deliberately kept on the first row of the two name-prefixed
messages, so the width cannot regress; only the second row, which is where the
odd article sat, changed.

## The two item-description tables

Both are already ours; the JP's kanji copy in `dlg00 #0222-#0326` is dead data.
Worth recording because the two tables look like a duplicate and are not:

| table | reached by | renderer | charset |
|---|---|---|---|
| `InventoryDescriptions` | `loc_65BCC`, the shop | `RunText`, dialogue font | `script/charset.asm` |
| `InventoryDescriptions2` | `Win_ItemActionLook`, the menu | window renderer, menu font | `tables/wincharset.asm` |

Same text, two encodings -- capitals agree but lowercase does not (`a` at $1B
against $39), so reading one with the other's table yields plausible-looking
rubbish. `itemdesc.py` writes both from `01:003` and the assembler applies
whichever `charset` is active around each block, so both come out right. Decode
each with its own table and they are byte-identical.

The blank `dlg*` rows now carry a `note` saying why they are blank, so they
stop reading as unfinished work.

## Porter idempotence

`itemdesc` and `shoptext` each added a blank line to `ps4.asm` on every run.
Harmless to the ROM -- blank lines assemble to nothing, and the build hash is
unchanged across the fix -- but it meant the source drifted on every build,
which makes a real diff impossible to see. Both splice a rendered block back
in, so the seams are now normalised: blanks trimmed from the head and from the
block, then joined with exactly one. All six porters are idempotent, verified
by running each twice and comparing.

## Surplus $F9 delays: three more scenes recovered (2026-09-03)

`treeport.drop_extra_control` handled exactly ONE surplus control, and
`wave.py` reported a row as portable only on an exact fingerprint. Between
them those two rules hid three rows that port perfectly well -- the US build
strips `$F9` delays wholesale, so a JP row can differ from its US counterpart
by nothing but pauses:

    lz1E1F06#0005   19 controls vs 12   seven surplus $F9
    lz1D5A26#0089                       three surplus $F9
    lz1E1F06#0004                       one surplus $F9

`drop_extra_delays` now drops any number of surplus `$F9`, aligning our tokens
against the US sequence rather than counting them, so the result is the US
order by construction. `$F9` is a pause and nothing else -- it names no
speaker, holds no event id and dispatches nowhere -- so dropping one costs
pacing and cannot cost meaning. There is deliberately no "words on both sides"
guard, unlike a dropped control: a delay sits mid-phrase on purpose and closing
`Ru{F9}...dy` back up to `Ru...dy` is the right result. Every dropped token is
still named in the build output.

`wave.py` counts these as portable now. It had been the second time that tool
under-reported what was left.

The recovered scenes are substantial: **Daughter** (ドウター) at the weapons
plant -- her introduction as "Guardian of Algol", Forren proving she is an
abandoned prototype, and Forren shutting her down -- plus Raja on Gallberg
Tower being the source of the Meese plague.

## Space-travel banners: done (2026-09-03)

`tools/spacenames.py` ports the six destination banners shown when travelling
between worlds. Two are corrections the JP asks for, not preferences:

    RYKROS               -> RYUCROSS            リュクロス, per the glossary
    ARTIFICIAL SATELLITE -> ARTIFICIAL PLANET   人工惑星

Motavia has no `dlg02` row -- region 2's extraction began after it, the same
boundary problem as `dlg01#0000` -- and its US text already matches the
glossary, so it is left alone.

The leading spaces centre the line and are load-bearing; they survive
assembly (see the corrected note below).

## What is left in dlg*

- `dlg00 #0222-#0326` are the JP's **kanji** copy of the item descriptions. The
  US equivalent is `InventoryDescriptions2`, which `itemdesc.py` already
  rewrites alongside the main table, so there is nothing to do.
- `dlg00 #0000-#0154` duplicate the item name table, already ported.
- The found-item strings (" Found an item!", " found some meseta!",
  "00 meseta procured!") sit in a different charset region beside the
  space-travel place list. They are already correct English and say what the
  JP says; left alone deliberately.

## Examine text and credits: done (2026-09-03)

`tools/examinecredits.py` covers the block from `WinTiles_PlayerNothingMsg` to
the `charset` reset -- 156 strings, of which the first 28 are the party's
"nothing here" lines and the scenery examines, and the rest are the staff
credits.

    US 0        no JP row (below)
    US 1-27  -> dlg01 #0000-#0026
    US 28+      the credits, deliberately left as the US build has them

The credits are people's names and role titles; the US list is already right
and there is nothing to gain from retranslating a name.

**The porter only rewrites entries that have a translation.** Everything else --
labels, blank lines, `dc.b "x", $FF` written on one line -- is left untouched,
which makes an untranslated run byte-identical by construction rather than by
luck. That matters here: an earlier parse-and-re-emit design reproduced the
text correctly but moved every string, because this block separates entries
with a bare blank line while the shop block uses `even`. Adding alignment
padded six odd-length entries and shifted the whole block, which showed up as
every pointer in the table at `$05910B` moving six bytes.

### A data repair, not a workaround

`trpatch check` rejected `dlg01#0000` for gaining an engine token, and it was
right to: the row was wrong in `work/`. Region 1's extraction began three bytes
late, so the row had lost its `$F4 02` portrait control *and* the `$E0` lead
byte of its first kanji, which left 物 decoding as a bare ひ. The JP ROM has
the true bytes, so the row was repaired rather than the check worked around:

    ひ欲しそうに...            -> {ctl.F4:02}物欲しそうに...
    offset 1976942, 25 bytes   -> offset 1976939, 28 bytes

The message *before* it, `$F4 01`, was never captured at all. It is quoted in
the porter and translated from there, and is the one string in the project
whose source lives in a tool rather than in `work/`.

Also worth knowing: AS cannot take a double quote inside `dc.b "..."`. The US
build used single quotes in the two strings that needed them (the epitaph, and
Laila's grave marker), and ours do the same.

## Shop and inn text: done (2026-09-03)

`tools/shoptext.py` ports the 65 inn and shop strings between `loc_2AC0DE` and
`InventoryDescriptions`, and runs from `sourcebuild.py`. All 65 are translated.

The earlier "cannot be ported" conclusion was based on a bad measurement: the
walk that reported 65 US strings against 172 JP had counted the JP side wrong.
`dlg00` is a mixed region -- item names at #0000-#0154, the shop/inn block at
**#0155-#0221**, then kanji item descriptions from #0222. That is 67 JP strings
against 65 US slots, and the groups line up exactly:

    #0155-#0204 -> US 0-49      two inn voices of 6, two shop voices of 17,
    #0205-#0206 -> dropped       the three shop-type nouns, Naura
    #0207-#0221 -> US 50-64      Bayamare and the rough "eh?" voice

Both ends and every group boundary agree, which is what makes the two dropped
strings (a confirmation and a thank-you for the Naura cake shop) identifiable
rather than guessed.

### Three traps, all of which produced wrong output first

1. **Every control must round trip, not just `$FC`.** Two strings open with
   `$FD`; dropping it shifted the block by a byte. The porter now writes any
   control back verbatim.
2. **A leading space was being lost -- but AS was not the culprit.** The first
   diagnosis here was that AS drops a space after the opening quote. That is
   **wrong**: `SpaceTravelName_Motavia` keeps all five of its centring spaces,
   and the shop block round-tripped bit-identically while still using plain
   `dc.b " store."`. The space was lost to trap 3 below, in our own code. Edge
   spaces are now emitted as explicit `dc.b $00`, which assembles to the same
   byte a quoted space does and so is byte-equivalent either way -- kept
   because it makes the intent visible in the generated source.
3. **These are fragments, so `.strip()` is wrong.** `main()` stripped the text
   out of the JSON, which is what actually ate the separator in front of
   " meseta." and " shop." -- and it would have rendered `theWeaponsshop.`
   This, not the assembler, was the bug.

Verification: with zero translations the porter rewrites the block to a
**bit-identical ROM** (`A57E79EB...`), which is what proves it reads and writes
losslessly. Fragments are then checked by decoding each from its own label
address -- a sequential decode cannot tell a real leading space from `even`
padding, which is what made the first two attempts look correct when they were
not.

## Superseded: shop and inn text cannot be ported by position

The `dlg00`/`dlg01`/`dlg02` rows (466 untranslated, of which 149 merely
duplicate an already-translated table entry) carry absolute **JP ROM** offsets,
not stream ids, so treeport never sees them. 317 are their own text: inn and
shop dialogue, examine lines, planet banners, staff credits.

Porting them the way `itemdesc.py` does was tried and rejected. The US run of
`$FF`-terminated strings from `loc_2AC0DE` holds **65** strings where the JP
region has **172**, and the correspondence visibly drifts by `dlg00#0212` --
US "Will you buy something else, eh?" against JP "手持ちがいっぱいかい？". A
positional porter would scatter shop text into the wrong slots. It needs a real
JP-to-US pairing, not an ordinal walk.

Item descriptions are two lines of at most 28 cells -- the widest the JP itself
uses; the US never exceeds 25. Ours stay within 26.

### Spelling

STATUS fixes the convention as natural American English, and 17 rows had
drifted to British forms (`rumour`, `honour`, `storey`, `defence`,
`travelling`, `marvellous`...). All normalized; no row changed width enough to
matter and every check still passes.

### New names this pass

`LaSheek`, `Shess Tierney`, `Rudy Ashley`, `Eileen` (Guild clerk), `Gyuna`
(Ryuon's innkeeper), `Aiedo Hernandez`, `Gaira`, `Le Roof`, `High Priest`,
`Tower of Courage` / `Tower of Strength`. All recorded in `work/glossary.md`.

Gyuna is the one to watch: he ends every sentence in `ズラ`, and a bystander says
outright that his old country accent is thick, so the tic has to be *audible*
in English. Rendered as broad rustic dialect plus a recurring "I reckon" rather
than flattened out the way the US build did.

## Mid-page portrait changes

`work/midpage.md` regenerated against the full translation, with quoted setup
lines. Section A is **0**: no mid-page portrait swap is live in our English.
Section B lists 147 changes across 108 messages where the JP runs on and we
break the page first -- consistent with the ruling that `{ctl.FD}` is intended
to come first. Section C is the 13 untranslated rows.

## Current decisions

- Translation uses natural American English and etymology-first proper-name
  transliteration. Record new naming decisions in `work/glossary.md`.
- Attract narration uses the restored “Woven from beyond the reaches of
  time...” poem. `Title_ScrollDelay` is `$25`; the current timing was approved.
- Party names use the standard menu VWF, resolved through `CharNameData` even
  for old saves containing US names. They are dynamically composed in 2-4
  cells. Fixed 32x8 party strips were rejected because four cells per name
  increase VRAM demand and provide no savings.
- Items, Techniques, Skills, and locations use prerendered VWF menu strips.
- Dialogue and narration use the separate dialogue VWF face.

## Resolved regression

- Builds `8DADE4F...` and `58AFDF95...` hard-locked after selecting START.
- `loc_6881E` called `VWFMenu_RemapRegion_NoSweep` as a subroutine, but that
  entry skipped the routine's register save and reached its common register
  restore. The restore consumed the caller's return stack and eventually
  returned to address zero.
- `VWFMenu_RemapRegion_NoSweep` now has a matching register save. Build
  `FBF1CE3F...` was confirmed in BlastEm to leave the title menu, initialize a
  new game, dispatch event `$9F`, and display the opening dialogue.
- The prologue translation and approved timing were preserved unchanged.

## Resolved principal-cutscene lock

- Build `FBF1CE3F...` hard-locked on the first principal cutscene. The saved
  state showed `Panel_Index = $00F2` and `NemDecomp` reading ROM `$000000`.
- `treeport.py` had read `$F2,$00` plus `dc.w $0000` as only the two bytes
  `$F2,$00,$00`. The first panel load therefore consumed the next `$F2` as the
  low byte of panel id `$00F2`; that invalid panel record was all zeroes.
- Tree control operands now come from each untouched compressed US tree binary,
  not from mutable translated assembly. Principal panel ids are restored to
  `$0000` through `$0003`.
- `test_treeport_controls.py` compares all 2,738 source messages with their
  canonical engine controls and validates all 165 action-$00 panel loads. It is
  run automatically by `sourcebuild.py`.

## Environment rebuild (2026-09-02)

After the Windows reinstall the toolchain needed three fixes:

- `python` on PATH resolved to the Microsoft Store stub in
  `%LOCALAPPDATA%\Microsoft\WindowsApps`, shadowing the real interpreter at
  `C:\Python314\python.exe` (3.14.6) — which was not in the persistent PATH at
  all. Fixed: `C:\Python314` and `C:\Python314\Scripts` are now prepended to the
  User PATH, verified in a fresh-environment process. Old value backed up at
  `.user-path-backup-20260902.txt`. `python tools/sourcebuild.py` works as
  documented in any terminal opened since.
- `NoDefaultCurrentDirectoryInExePath=1` is now set, so `cmd` no longer resolves
  a bare command name from the working directory. `sourcebuild.py` invoked
  `cmd /c build.bat` and `build.bat` invoked bare `fixheader`; both failed —
  the second one silently, producing a ROM with an unfixed header. Both now use
  explicit paths (`str(DISASM / "build.bat")` and `"%~dp0fixheader.exe"`), so
  the build no longer depends on that setting either way.
  Previous `build.bat` kept as `build.bat.bak`.
- `work/dialogue_full.json` held one pending edit that dropped a control token:
  `lz1DC4E6#0024` had lost its leading `{ctl.F4:0E}`, which failed
  `trpatch.py check` and blocked the build. Token restored; pre-fix copy kept as
  `work/dialogue_full.json.bak-resume` and can be deleted.

All nine checks pass. The tree rebuilds clean: 0 errors, 0 warnings, ~10 s
assembly.

`ps4en.bin` is unchanged and still the last emulator-verified ROM
(`28990E17...`). A rebuild from the current JSONs produces
`FE1E8D2BBEF2B69FAF9FAB0F0F457622F1E15BA44476F849F9D90289CCF0A42B`, differing in
the checksum word and ~56 KB across the compressed script arena (banks `$20-$21`)
plus a few hundred bytes of uncompressed streams — the pending edits of
2026-09-01. That build has not been run in an emulator yet.

## Translation progress (2026-09-02)

- Compressed dialogue (`work/dialogue_full.json`): 273 / 2170 (12.6%).
  Complete or near: `lz1CC476` 97/111, `lz1CD2E6` 105/111, `dlg02` 31/39.
  Started: `lz1D4FB6` 28/67, `lz1DC4E6` 5/26, `lz1CF6D6` 4/45, `lz1DB6F6` 3/52.
  Untouched: the remaining 21 streams, largest being `lz1DA026` (232),
  `dlg00` (327) and `dlg01` (132).
- Uncompressed dialogue (`work/script_translated.json`): 348 / 827.

## Menu strip space width (2026-09-02)

`menuwidth.bin` gives the space a full 8px cell deliberately, because the
runtime draws space-padded fixed strings (`WinTiles_Meseta` is `"        MST"`,
and about fifteen others centre or right-align the same way) that would all
slide left if the advance shrank. That argument does not reach the prerendered
strips: no strip name has a leading or trailing space, and a strip may be
shorter than its budget but never longer.

`menustrip.SPACE_ADV` is now 3px for strip composition only, matching the 3px
the dialogue face has always used (`vwffont.SPACE`). 164 of 468 strip names
lose a cell; none go over budget; `menustrips.bin` drops to 62,240 bytes.
`proofsync.py` mirrors the override into the page so the editor's cell preview
cannot disagree with the prerenderer.

Still on the wide space: runtime-composed field text (`fieldstrings.py`, the
"X is procured!" sentence) and the padded window strings. Narrowing those means
converting ~15 padded literals to explicit positioning — not attempted.

## Control cue declutter (2026-09-02)

`controlCue` in `proofread.html` emitted one chip per token, so `{BR}` and
`{ctl.FD}` — 60% of 9,737 chips, and 216 on the worst entry — buried the
portrait changes. Both are drawn by the preview directly below as rows and as
separate pages, so they are now skipped (`CUE_SKIP`) and the JP/EN label is
emitted once per run rather than once per chip. Verified in a browser: no
console errors, and a nine-token line now cues three chips, all portraits.

## Dialogue control-token invariants

- `{ctl.FD}` is a button prompt; `{ctl.F4:xx}` is a portrait/speaker change.
  A button prompt must come before a speaker change, or the outgoing line is
  overwritten before the player can read it.
- This cannot regress by hand. `trpatch.engine_tokens` returns engine tokens
  **in order** and `trpatch check` compares the EN list against the JP list
  exactly, so every FD/F4 relationship is the original game's. Only `{BR}` and
  `{Kxxx}` may be moved by a translator. Audited 2026-09-02: 273 translated
  entries, 0 with an engine-token order differing from JP.
- Strict adjacency is *not* the rule and never was: the JP itself has 1,051
  F4s that are not immediately preceded by FD — a message may open on a
  portrait, and `{ctl.FD}{ctl.F2:xxxx}{ctl.F4:yy}` is a normal run.

## Open: pool refs are flattened by the sweep (2026-09-02, unverified)

Found by reading `vwf/vwfmenu.asm` while looking into the unresponsive build.
Not reproduced in an emulator, and **not fixed** — it touches the allocator, and
an untested change there is what hard-locked `8DADE4F...`.

`VWFMenu_Refs` is used with two different meanings:

- `VWFMenu_Alloc_Hit` does `addq.b #1` — a count.
- `VWFMenu_Deref` does `subq.b #1`, guarded by `tst.b`/`beq` — a count.
- `VWFMenu_Sweep` clears every entry and then does `move.b #1` per plane cell
  that refers to a slot — a flag. Its own comment says "the count itself does
  not matter".

So a slot referenced by N nametable cells is left at 1, not N, by a sweep. The
first of those N cells to be overwritten derefs it to 0; the remaining N-1 hit
the `beq` guard and change nothing. The slot is now free while N-1 cells still
display it, and the next `VWFMenu_Alloc` free-slot scan hands it out and
overwrites the tile under live text — which is what a box of unrelated glyphs
on the field map looks like.

Candidate fix: make the sweep count rather than flag — `addq.b #1` with an
`$FF` saturation guard, since a plane walk can in principle see a slot 2,048
times. That restores the invariant the allocator's own comments assume
("anything the plane still refers to is marked live") without changing the
allocator.

Separately, `PoolTop` is never lowered by the sweep, only by `VWFMenu_Rollback`
on window destroy. Once it saturates at `VWFMENU_SLOTS` (83), the
`cmpi.w/bcs` in `VWFMenu_DrawString_Composed` is false forever, so every later
string sweeps all 2,048 plane cells. That is a real per-string cost worth
removing, but it is paid only when a string is drawn.

**This does not explain an idle freeze, and I was wrong to suggest it might.**
Both mechanisms are allocation-driven, and nothing allocates while the game
sits at a dialogue box:

- `VWFMenu_DrawString` has exactly one call site in the entire ROM
  (`ps4.asm:308053`, inside the window tile painter). It runs when a window
  paints, not per frame.
- The dialogue engine has no pool at all: `Alloc` and `Pool` appear zero times
  in `vwf/vwfdia.asm`. The box in the field screenshot is drawn by an engine
  that has no allocator, no sweep and no slots to exhaust.

So the sweep findings above are a **corruption** bug — wrong glyphs under live
text while menus draw — not a hang, and not reachable from idling.

## Retracted: the dialogue RAM ceiling does not apply to this build

Two earlier revisions of this section treated the `$FF6000-$FF8000` decompression
buffer, and `Plane_A_Buffer` at `$FF8000` immediately above it, as a live
constraint on how long a translated message may be — first at 23 bytes of
margin, then at 1,000. **Both were wrong, in kind rather than in degree. The
buffer is never written in this build.**

`ps4.options.asm` sets `dialogue_uncompressed = 1`, and both load sites branch
on it:

    DialogueTreesToRAM:                  GetDialogueByID:
      if dialogue_uncompressed = 1         if dialogue_uncompressed = 1
        move.l d0,(Current_Dialogue_Tree)      movea.l (Current_Dialogue_Tree),a0
      else                                 else
        lea (Dialogue_Trees).l,a1              lea (Dialogue_Trees).l,a0
        jsr (KosDecomp).l                  endif
      endif

Under this option the tree is never copied: a ROM pointer is stored, and the
message scanner walks ROM. `KosDecomp` into `Dialogue_Trees` is in the `else`
branch only. The constants say the same thing — `Saved_Dialogue_Addr` is a
**dword** when uncompressed "since we must point at correct ROM address", a
word when compressed "since it's in RAM".

Confirmed in two savestates:

    Current_Dialogue_Tree  $00208FE2 / $001E1872   both ROM
    Saved_Dialogue_Addr    $002099F5 / $002C4439   both ROM, dword form

and $00208FE2 decodes as dialogue — `{FD}` `{F4}` `{FC}` `{FF}`, with a run of
ten `{FA}` branches at $2099F5.

The three empirical points (6,582 works / 7,534 works / 8,691 hangs) are real,
but they were measured on the compressed JP-ROM patch path, which
`sourcebuild.py` explicitly refuses to run over a source build.

**So do not add per-region byte headers, and do not impose a length limit.**
There is no mechanism for a long message to corrupt anything. The limits that
do bind are already enforced:

- **ROM space** — last used byte `$325C99`, **873 KiB free** of 4 MB, against
  roughly 250 KiB of total dialogue. Not close.
- **Per-page layout** — 2 rows per page, 32 cells per row, checked by
  `trpatch.check_line` on every build.
- **Engine token order** — checked against the JP on every build.

`trpatch.py`'s `STREAM_MAX` is kept so the compressed path stays checkable, and
its comment and build line now say plainly that it is not a budget here.

**This leaves the original screenshot unexplained.** The stray tile box,
discoloured panel face and white wash were real, but the dialogue buffer is not
the mechanism and neither is the menu VWF pool (savestate: 9 of 83 slots in
use, Plane A clean). It has not recurred. Next time it does, the thing to
capture is a savestate — CRAM and the VDP registers will say directly whether
the palette or the DMA went wrong.

## Silent drop: 106 translations never reached the ROM (2026-09-02)

`lz1CC476#0086` showed the US line in game despite being translated.

`treeport.main` collects rows with no `us` field into `unverified` and
`continue`s — and then **never printed the list**. The guard itself is right
(usimport could not establish which US message the row pairs with, and porting
on index alone mispaired 73 rows on the first attempt), but a finished
translation silently not reaching the ROM is indistinguishable in game from not
having translated it yet.

`treeport.py` now reports them, grouped by stream. Current state:

    75 rows dropped for a missing `us` pairing
      lz1CC476:  44   lz1CD2E6:  29   lz1CF6D6:   2
    31 more rows are in streams that map to no tree at all

Recovering those 75 means establishing the US pairing, not relaxing the guard.

## Translation waves (2026-09-02)

`tools/wave.py` drives these. A row only reaches the ROM if treeport can port
it, so the tool lists exactly the rows whose JP engine fingerprint already
matches the US message at the same index, excluding empty messages and bare
`{ctl.F6}` event markers -- both look untranslated for ever and neither carries
text.

    python tools/wave.py            what remains, by stream
    python tools/wave.py 1DA026     dump one stream for translation

Completed streams:

| stream | tree | content | rows |
|---|---|---|---|
| `$1DB6F6` | 31 | Party Talk | 24 |
| `$1DC4E6` | 33 | Academy, the crash-screenshot scene | 16 |
| `$1DEC96` | 38 | Gungbius Grand Temple, Dezolis | 43 |
| `$1CE546` | 5 | Krupp village, Saya and Hahn's family | 51 |
| `$1CF6D6` | 7 | Molcum and Tonoe, Pyke and Pana | 28 |
| `$1D02D6` | 9 | Nalya, and Kadary under Zio's church | 75 |
| `$1D38E6` | 14 | Tyler and Raja, the Landeel | 34 |
| `$1D4446` | 15 | Ryuon -- the Raja stream, seven puns | 40 |
| `$1D4FB6` | 17 | Meese penguin, Valley of Wonders, weather-system trap | 34 |
| `$1D6816` | 20 | Esper Mansion, Lutz's chamber, Elsydeon | 32 |
| `$1D5A26` | 18 | Richelle rebuilt, Meese plague ward | 88 |
| `$1DA026` | 28 | Motavia examine-text: books, notices, picture books | 127 |
| `$1D1256` | 11 | Aiedo -- market, Guild, gaol, the Rocky job | 80 |
| `$1DB036` | 30 | Dezolis examine-text, Zelan and Kuran checks | 81 |
| `$1D2426` | 12 | Monsen and Termi, the Plate System, Tallas | 58 |
| `$1D76C6` | 23 | Jut, and the loss of the Grand Temple | 55 |
| `$1D85A6` | 24 | Uzo and Torinco, the sick boy and the bird boss | 50 |
| `$1D9436` | 27 | Hunters Guild -- every job posting and payout | 42 |
| `$1DFCB6` | 39 | Choosing the last companion; finding Ryucross | 20 |
| `$1E1316` | 42 | **The ending** -- Siam, Dark Falz, the closing poem | 18 |
| `$1E05B6` | 41 | Rykros towers, Laila's illusion, Megiddo | 10 |
| `$1E1F06` | 43 | The weapons plant, Forren's units | 13 |
| `$1DD086` | 34 | Bio-plant, Seed, the Psycho Wand, Ladea Tower | 11 |
| `$1DDD96` | 35 | Zelan, Kuran, Dark Falz, the crash landing | 10 |

    297 -> 1312 rows translated (13.7% -> 60.5%)
    233 -> 1281 messages ported
    **0 portable rows remain** -- every row that treeport can port and that
    carries text is translated

`$1CC476` and `$1CD2E6` are **finished**: every row still counted as
untranslated in them is an empty message in both the JP and the US build.

### Notes from these waves

- `{ctl.FD}` is a LAYOUT token, so unlike `{ctl.F4}` its placement is **ours**.
  Two rows failed `check_line` for exactly the reason the FD-before-F4 rule
  exists: text ran straight into a speaker change, and the page overflowed two
  rows. Put an explicit `{ctl.FD}` before every `{ctl.F4}` that follows text.
- Raja's puns carry: タイラー in ほったらかし became "Left TYLER-ly to himself",
  ランディール in 空を飛んでいく became "a ship for LANDEEL-ing in the sky", and
  カン/患者 became "a hunch / a HUNCH-back".
- Glossary applied against the US where they differ: Gungbius not Gumbious,
  Dezolian not Dezolisian, Landeel not Landale, Pyke not Gryz, Frena not Demi,
  Forren not Wren, Laila not Alys, Rudy not Chaz, Alshulin not Alshline.
  考古学者 is *archaeologist*, not the US "historian".
- Corrected in earlier waves: **Alshulin** (had been "Alshline") and
  **climate control system** (had been "environmental control system").

### Portrait ids identified

    F4:00 the Elsydeon voices     F4:08 Forren      F4:17 esper gatekeeper
    F4:01 Rudy                    F4:09 Raja        F4:19 esper elder
    F4:02 Laila                   F4:0A Shess       F4:21 Gallberg envoy
    F4:03 Hahn                    F4:0C Saya        F4:24 the lost Piata girl
    F4:04 Thray                   F4:0D academy elder
    F4:05 Pyke                    F4:0E the Principal
    F4:06 **Fal**                 F4:10 Pana
    F4:07 Frena                   F4:0F Dorin

`F4:06` is **Fal**, not Frena -- settled by `lz1D5A26#0098`, where Thray
addresses her by name, and corroborated by `lz1DB6F6#0011`, where Rudy speaks
of rescuing "the android Frena" while `F4:06` is in the party.

### `{ctl.FD}` goes before `{ctl.F4}`, and the US proves it

Measured across the shipped US build: **2,236 portrait changes, of which only 8
land mid-page (0.36%)**, confined to trees 19, 29, 39 and 41. The JP has 186
across 121 messages. So the US localisation systematically converted mid-page
portrait swaps into page breaks.

Mark's ruling matches that: put the button prompt first everywhere. Applied --
`lz1CD2E6#0103` and `lz1E1316#0009` were the last two, and **our English now has
zero mid-page portrait changes**. `tools/midpage.py` reports and quotes them if
any ever reappear.

### The US resolved JP branches into PARALLEL TREES

32 translated rows were refused by treeport because our JP engine fingerprint
did not match the US message. 30 had a US engine-code count of **zero** against
our 1-31 `{ctl.FA}` conditional branches, and the US message at that index was
**entirely blank**.

The content was not cut, it was moved. The JP branches inside one message with
`{ctl.FA}`; the US resolved those branches into **parallel trees**, leaving the
base tree's slot empty and putting each variant at the *same index* in another
tree:

    lz1CC476#0064   tree 1 msg $40  blank
                    tree 2 msg $40  "My parents live in Mile... my allowance"
    lz1CD2E6#0003   tree 4 msg $03  blank
                    tree 3 msg $03  "You're looking for Birth Valley? ..."

So the pairing is recoverable **structurally**, with no back-translation needed.

**`tree_map` cannot be trusted to find the variant.** It records one tree per
stream, and the variant is not reliably the next one up: `$1CD2E6` is named as
tree 4 and its variant is tree **3**, *below* the base. `treeport.tree_group()`
therefore measures the group instead. Two scoring methods were tried and
rejected before the third worked:

1. *Fraction of rows a tree matches.* Useless -- most messages carry no engine
   codes at all, empty matches empty everywhere, and 19 unrelated trees scored
   above the floor for one stream. Routing on that would have put rows into
   whichever tree happened to agree at that index.
2. *The same, counting only rows that carry codes.* Too strict -- it collapsed
   every group to the base alone, because the variants hold **different
   subsets** of the branches, so a variant always scores poorly against its base.
3. **Coverage.** A tree joins the group when it resolves rows the group so far
   cannot, at least 3 of them, and only rows carrying engine codes count.

That found every group as `base` plus one **adjacent** tree, except a single
candidate 21 trees away that was chance agreement on rows carrying one
`{ctl.F4}`. Requiring `abs(n - base) <= 2` drops that and nothing else.

    ported  1248 -> **1281**    unverified  28 -> **0**    skipped  5 -> **0**

### A relocated message, found from the US text

`lz1CC476#0086` matched nothing at its own index in either group tree. Mark
supplied the US line -- *"I think there's more to it than that." / "Things are
starting to get interesting!"* -- and it turned up at **tree 1 msg `$6E`**,
carrying our exact `[F4, F4, F4]` fingerprint.

Indices otherwise align one for one. The US simply **moved this message**: it
left `$56` blank and appended the message at `$6E`, the end of the tree, where
our source has no row at all.

`treeport.relocated()` recovers that, in a second pass so the evidence is
strongest. Pass 1 assigns every row that matches at its own index and marks
those slots claimed; pass 2 then accepts a relocation only when the fingerprint
is distinctive (two or more codes) and exactly one message in the group carries
it unclaimed. For `#0086` two messages in tree 1 have `[F4, F4, F4]` -- `$29`
and `$6E` -- but `$29` belongs to row `#0041` at its own index, leaving `$6E` as
the single unclaimed candidate.

Verified in the built source: `dialogue 1.asm` message `$6E` now holds
"Something smells off. That principal is / too edgy."

### A transposed control pair, found from the US text

`lz1CD2E6#0102` matched no tree exactly. Mark supplied Laila's US line -- *"An
ancient curse?"* -- placing it at **tree 3 msg `$66`**, our own index. Aligning
the two control sequences, 21 of 23 codes agree exactly and only positions 20
and 21 are swapped:

    ours   ... F4:03  F2:00000F  F9:3B
    tree 3 ... F2:00000F  F4:03   F9:3B

`emit` writes the US code **and operands** for each of our tokens in sequence
and ignores what our token said, so a count-only match would attach our text to
the wrong controls -- our `{ctl.F4}` would fire their `{ctl.F2}` event and a
line would land under the wrong portrait. Exact-fingerprint routing is what
prevents that, and it should stay.

Here the two controls are **adjacent with nothing between them** in both
versions:

    {ctl.FD}{ctl.F4:03}{ctl.F2:00000F}............Monster.{ctl.F9:3B}

so the order is a difference without a distinction. `match_us_order()` accepts
exactly that case -- a swap of two neighbouring tokens with no text between
them -- and refuses everything else, so no dialogue can move under the wrong
portrait. Routing accepts a tree whose controls are a **permutation** of ours
and leaves the safety decision to that gate.

Verified in `dialogue 3.asm` message `$66`: the event fires, the portrait
becomes Hahn, then his line "............Monster." Our JSON is untouched and
stays JP-faithful, so `trpatch`'s EN-equals-JP rule still holds.

### Every translated row now ports

The last two were controls the US build simply does not have.
`drop_extra_control()` removes one surplus control when doing so makes the
sequences identical, and **prints what it dropped on every build** -- a silent
loss is how a portrait change goes missing without anyone noticing.

    2 row(s) ported with a control the US build does not have, dropped to match it:
      lz1CF6D6#0003: {ctl.F9:13}
      lz1CF6D6#0038: {ctl.F4:04}

Both are provably lossless, and the gates say so rather than trusting the
coincidence:

- **`#0003`** drops a timed delay with no words beside it. Located from Mark's
  quote of Laila's "your company", which put the message at tree 7 `$03` -- our
  own index, so only the control ever differed. The first attempt refused this,
  because the test for "words beside it" counted a `{BR}` token as a word; it
  now strips layout tokens before looking.
- **`#0038`** drops a `{ctl.F4:04}` that **re-sets the portrait already
  showing**: Thray is set by an earlier `{ctl.F4:04}`, with only a `{ctl.F7}`
  between, so the second is a no-op and the US removed it. A `{ctl.F4}` is only
  ever dropped when the last portrait actually set is the same one -- checked by
  scanning back past intervening controls, not just the previous token, which
  the first attempt got wrong.

Any other surplus control is still refused.

    ported  1248 -> 1281      unverified  28 -> 0      skipped  5 -> 0

Every translated row reaches the ROM. The three recovery mechanisms, in the
order they are tried: the right tree (`tree_group`), the right index
(`relocated`), the right order (`match_us_order`), then one dropped control
(`drop_extra_control`).

### Pre-VWF translations are too terse, and can be found

Mark noticed the Birth Valley cutscene `lz1CD2E6#0102` reading abruptly and
guessed it had been written for the FIXED-WIDTH renderer, before the VWF. The
measurement agrees. `work/dialogue_full.json.bak-resume`, the backup taken at
the start of this session, separates translations written before it from those
written after:

    translated before this session   273 rows   EN/JP chars, median 1.86
    translated during this session  1039 rows   EN/JP chars, median 2.13

Japanese is dense, so a faithful English line needs roughly twice the character
count. The pre-VWF rows sit about 13% below that, and the worst are far below:
`#0102` was at **1.26**.

The symptom is telegraphese -- text trimmed to fit 32 fixed cells, where the VWF
now fits about fifty proportional characters:

    JP  前にモタビアンの村で聞いたんだ…でも、ずいぶん昔の話だよ？
    was "A Motavian village, long ago."          <- a stage direction
    now "I heard of it in a Motavian village once...
         though that was a long while back."

**All 80 have been retranslated.** The pre-session median has moved from 1.86
to **2.14**, level with the 2.13 of work written after the VWF landed, and only
two rows still measure under 1.75x -- both correctly, because the JP is itself
terse:

    lz1CC476#0005  1.72  "Oh, you've done it for us! / Thank you, truly!"
    lz1CD2E6#0072  1.52  "Mama says I'm not to go outside...... / tch."

Growth ran from +11% to +125%, median about +50%. The work was concentrated in
Piata, the Academy and the Birth Valley arc -- the game's first hour, and what a
player sees most.

The ratio is a **finder, not a verdict**. Every row was re-read against the JP
and several were left nearly as they were; padding a line to hit a number would
be the same mistake as clipping it to fit a cell.

To find them again:

    ratio = len(TOK.sub('', en)) / len(TOK.sub('', jp))

against `dialogue_full.json.bak-resume` for provenance. Anything under ~1.75
with a JP body of 25 characters or more is worth re-reading.

### Enemy and battle-action names (2026-09-02)

`02:001` 152 enemy names and `02:002` 112 enemy skills / battle actions, both
rendered by the menu VWF at a **10-cell** cap and measured with
`menustrip.compose`.

Player-facing names already fixed in `00:002` and `00:003` are reused verbatim:
the same string must appear whether a move is used by the party or against them.
That table's scheme is etymology-first and leans German -- フォイエ is **Feuer**,
シュネラ is **Schneller**, リューカー is **Rueckkehr**, グランツ is **Glanz** --
so the shared moves here follow it: Gifeuer, Giwater, Gizan, Gigravt, Giresta,
Gisaresta, Saresta, Megiddo, Shifta, Deband, Sealis, Limiter, Geron, Tonndre,
Flaeli, Bindwa, Legeon, Corrosion, Death Spell, Hyune, Mind Blast, Barrier
Field, Shadow Bind, PhononMaser, Air Slash, Flare Shot, Spark, Burst Lock.
ダブルアタック is **Double Slash**, as the skill table has it, not "Double Attack".

**Consistency bug caught:** the skill table gives バーストロック as **Burst Lock**,
but the Zelan dialogue had it as "Burst Rocket" -- an error introduced when the
weapons-plant scene was translated. Dialogue corrected to match the table, which
is authoritative for anything that also appears in a menu.

Only three names needed shortening for the cap, and the 3px space is why so few
did:

    グラススロータラ    Grass Slaughterer -> Grass Slaughter
    キャタピラインセクト  Caterpillar Insect -> Caterpillar
    あおじそラッピー    Green Shiso Rappy -> Aojiso Rappy

しそラッピー / あおじそラッピー are kept as **Shiso Rappy** / **Aojiso Rappy**
rather than translating the herb, matching how the series keeps Rappy.

`script_translated.json`: 348 -> **612 of 827**.

### What is actually left (2026-09-02, corrected)

An earlier revision of this section claimed the portable set was complete.
**It was not.** `wave.py` still routed by the base tree alone, so once treeport
learned about parallel trees, relocations and reorderings, the tool went on
reporting zero while 253 rows had in fact become portable. `wave.py` now shares
treeport's routing, which is the only way it can be trusted.

`work/dialogue_full.json` -- 2170 rows, 1312 translated

    253  portable and untranslated  <- real work
     32  still unportable
    466  stream maps to no tree (the dlg00/dlg01/dlg02 item-name rows)
     62  bare {ctl.F6} event markers
     45  empty in the JP itself

The 253 by stream:

    $1DA026 104   $1DB6F6 24   $1D4446 22   $1D9436 17   $1D1256 16
    $1D6816  16   $1D2426 13   $1D5A26 11   $1DEC96 10   $1D76C6  9
    $1D85A6   7   $1D02D6  4

`$1DA026` is the bulk: its variant tree 29 opened up another 104 examine-text
rows that the base tree alone never offered.

`work/script_translated.json` -- 827 rows, 348 translated. **This file has
barely been touched and is a whole second body of work:**

| segment | rows | what it is |
|---|---|---|
| `01:003` | 160 | **item descriptions** -- "おおぶりな ナイフ。" / "A large knife." |
| `02:001` | 152 | **enemy names** -- へレックス, モンスターフライ, ガンナービット |
| `02:002` | 112 | **battle commands and techniques** -- ぼうぎょ, フレイムボルト, レールガン |
| `01:004` | 49 | scenario/map titles, already Latin: "THE END OF THE MILLENNIUM", "MOTABIA TOWN" |
| `01:001`, `01:002` | 2 | shop prompts |

`01:004` needs review rather than translation -- "MOTABIA TOWN" should almost
certainly be MOTAVIA, matching the glossary.

So the remaining work is **253 dialogue rows + 479 script rows**, not zero.

## `MAX_ROWS = 2` is right, and the US agrees

Mark asked whether the ending could carry a third row, citing "The force
holding / this dimensional hole open / is gone!". Measured across all 43 US
trees: **25 of 7,173 pages exceed two rows (0.3%), and none at all in tree 42**,
the ending. The US split that message into **11 pages**, giving "is gone!" a
page of its own.

So the official localisation solved this exactly the way we are: by inserting
page breaks. Our breaks in `$1E1316` match their approach rather than diverging
from it.

Where the run-on genuinely had to survive -- `lz1E1316#0009`, the dimensional
collapse, which plays unattended -- the English was tightened to fit two rows
instead ("The force holding us is gone!" / "Space-time is warping. Danger!")
rather than a prompt being inserted into an auto-playing scene.

### The portrait-before-prompt bug, and the ending stream

Mark reported the Academy Principal speaking with Laila's portrait showing.
The cause was mechanical, not editorial: seven rows had `{ctl.F4}{ctl.FD}`
**adjacent** -- the portrait changed and *then* the game waited, so the outgoing
line sat on screen under the incoming speaker's face for as long as the player
took to press the button.

**The JP has that adjacency in none of them.** It was introduced in an earlier
translation pass, in every case. Reordered to `{ctl.FD}{ctl.F4}` in
`lz1CC476#0009`, `#0017`, `#0025`, `#0086`, `lz1CD2E6#0103` (x2),
`lz1DC4E6#0018`, `#0019`. `lz1CC476#0009` shows the effect plainly: the player
read "Ditch the kid, come with me" under Laila's face, before she snaps back.

**`tools/midpage.py`** lists every remaining mid-page portrait change for
case-by-case review (`--ours` limits it to translated rows). Mark's ruling: hold
the report until the translation is complete, and give each entry a quoted setup
line so the scene is recognisable -- an id alone is not enough to place it.

**The ending stream is `$1E1316` (tree 42)**, found from the US text
"The Elsydeon... It's protecting us" at `lz1E1316#0009`. Its dialogue runs on
automatically with no button prompts, so mid-page portrait changes there are
intended and must be preserved. `$1E05B6` and `$1E1F06` are the adjacent
late-game streams and get the same treatment. Everywhere else the default is to
break the page.

### `trpatch` now checks mid-page speaker changes

`{ctl.FD}` is a LAYOUT token, so its placement is **ours**. Putting text
straight into a `{ctl.F4}` overwrites the outgoing line before the player can
read it -- and nothing in the data prevented it, because the engine tokens
still matched. It slipped through three times in these waves and was only
caught incidentally, when the resulting page happened to overflow two rows.

The obvious rule -- "always break before a speaker change" -- is **wrong**. The
original does it deliberately in seven messages (`lz1CC476#0009`, `#0017`,
`#0025`, `#0086`, `lz1CD2E6#0103`, `lz1DC4E6#0018`, `#0019`), where the portrait
swaps for a reaction shot and the text is meant to run on. The earlier
translator matched the JP in all seven, correctly.

So `check_line` now counts mid-page speaker changes on both sides and flags
only a count **higher than the JP's** -- that is, one we introduced:

    N speaker change(s) land mid-page that the JP breaks first
    - add {ctl.FD} before the {ctl.F4}

A page ends at `{ctl.FD}`, `{ctl.F5}`, `{ctl.F7}` or `{ctl.FC}`. All 1084
translated rows pass.

### Names used without a glossary ruling

Chosen while translating; all easy to revise.

| JP | used | note |
|---|---|---|
| 八ッ裂きのライラ | "Laila the Dismemberer" | ruled by Mark: 八つ裂き is dismemberment. She calls the name tasteless, which the mouthful serves |
| テルミ | Termi | statue town referenced from Dezolis |
| ウーゾ | Uzo | home of the two gaoled sisters |
| みと | Mito | the Aiedo fortune-teller |
| ドクタールベノ | Doctor Luveno | ruled by Mark; US had "Lubetz" |
| ろっきい | Rocky | the lost dog, written in kana as a child would |
| グレグスン / ホプキンス | Gregson / Hopkins | class monitors on a blackboard |

Restored where the US softened or erred: 錬金術 is **alchemy** (US "metal
polishing"), ウィルスセクション is the **Virus Section** (US "West Section"),
安っぽいお酒 is **cheap-looking liquor** -- っぽい is about appearance, and it is Rudy, a youth, sizing it up by eye (US "orange soda").

`lz1DA026#0001` keeps **31.4 degrees** rather than converting to Fahrenheit --
the number is a pi joke.

The children's picture books in `$1DA026` are parodies and are translated as
such: 「きんのおの・だい3かん」 is *The Golden Axe, Volume 3*, 「はしれ！
ハリネズミ！！」 is *Run! Hedgehog, run!!*, 「はだかのじょおうさま」 is *The
Queen's New Clothes*, and 「モタビアンしっかく」 is *No Longer Motavian*, after
Dazai's 人間失格.

### Glossary decisions (settled 2026-09-02)

Ruled on by Mark and applied to both JSONs and `work/glossary.md`:

| JP | English | note |
|---|---|---|
| アルシュリン | **Alsulin** | after the real medicine *Arsulin* -- not Alshulin/Alshline |
| ミース | **Meese** | the glossary row reading "Mile" was a slip |
| マイル | **Mile** | a different town; only `lz1D38E6#0025` was ミース |
| リシェル | **Richelle** | |
| ペロリーメイト | **PelorieMate** | corruption of the real product *CalorieMate* |
| 戦士の神殿 | **Warriors' Temple** | matches `script_translated.json` |
| ナルヤ / サーヤ | Nalya / Saya | confirmed |

The `script_translated.json` tables already carried Alsulin, MILE, MEESE and
RICHELLE; the dialogue now agrees with them.

### Raja's puns must work as English

A pun that only tracks the Japanese reads as a typo in play. Each has to be a
real English phrase whose meaning **also fits the scene** -- a joke that
contradicts the game is worse than no joke. Every Raja line is logged here.

| JP | technique | shipped |
|---|---|---|
| ほっ**タイラー**かし | Tyler into *hottarakashi* (left neglected) | "He's been left en-TYLER-ly alone" -- *entirely alone*, also the JP sense |
| そラをと**ンディー**く船 | Landeel into "a sky-going ship" | "We've LANDed ourselves a fine DEAL there!" -- both halves of the name, and true: they just found a starship |
| **カン**じゃ / **カンジャ** | hunch / patient | "A hunch!! ...I get those in my back as well." |
| **サケ**て通れない | sake into *sakete tōrenai* (can't pass by) | "I can't BEER to pass it by" -- *can't bear to* |
| ふ**ツーノ**人 | horn into *futsū no hito* (ordinary people) | "To HORN-est folk they do look like horns" -- *honest folk* |
| **オトモ**だちがい | otomo (retinue) hidden in *tomodachi-gai ga nai* (some friend you are) | "Saying such a thing! Like a KICK in my SIDE!" -- the villager's noun is *sidekick*, so the hurt comes from the sidekicks themselves. ("we'd RETINUE as friends" -- *continue* -- was the other candidate, not taken) |
| 2の自乗 / 事情**ツー** | "two squared" / well-informed | "Then he knows two squared is FOUR-warned!" -- *forewarned*, and 2² = 4 |
| み**タイラー** | Tyler into *mitai* (seems like) | "TYLER-made for the journey" -- *tailor-made* |
| こ**タエル**けど**タエル** | kotaeru / taeru (tells on / endures) | "Hard to BEAR -- but BEAR it they do!" |
| **コオリ**ゴリ | ice into *korigori* (had enough) | "I've had ICE-nough of them!" |
| 君を**アイス** | aisu (love) as *ice* | "I've ICE only for you!" -- *eyes only for you* |

**Rejected, and why:** "And I thought we were COMPANION-able" (companionable is
an ordinary word, so nothing is hidden and nothing is bent -- it read as a plain
line with a word shouted in it, 2026-09-11); "Left TYLER-ly to himself" (not a word); "a ship for
LANDEEL-ing in the sky" (ships do not land in the sky, and the Landeel is the
party's interplanetary transport -- it lands constantly); "a sick man has a
HUNCH-back" (strained).

## Savestate: what the party-menu state proves (2026-09-02)

`work/rebuilt-status.exs` is a zip of full RAM, VRAM, CRAM, VSRAM and a
screenshot. Read at the party menu with HP/TP offset by one row:

    VWFMenu_PoolTop  = 9    (cap 83)
    VWFMenu_Peak     = 53
    Refs non-zero    = 9 / 83
    Refs             = 36, 34, 28, 22, 22, 16, 22, 22, 16, 0 ...
    Plane A          = 9 pool tiles, 2039 other, palette-select {0, 2}

This **rules out** pool exhaustion (9 of 83 in use) and nametable corruption
(Plane A is clean, palette select is normal) as causes of the row offset.

It also settles the direction of the `VWFMenu_Refs` defect. Nine slots are
referenced nine times by the plane, yet carry counts of 36, 34, 28, 22. The
counts **climb**, exactly as the source's own comment predicts ("decrements go
missing and the counts only ever climb") — so the live fault is a ref *leak*
driving `Peak` to 53, not the premature free the sweep-flattening analysis
predicted. Both are reachable in the code; only the leak is evidenced.

The row offset itself is still undiagnosed. It is transient and a battle clears
it, which points at draw-time state rather than at the tables.

## Pairings recovered: 47 of 75 (2026-09-02)

`usimport` pairs a JP row with a US tree message on the **engine control-code
fingerprint**, and records the strongest case as `exact`: same index, identical
fingerprint. But it only ever wrote the `us` field when the paired US message
had **text**:

    if i in t0 and t0[i][0] == fp:   hit = t0[i][1]      # pairing established
    ...
    elif hit.strip():                e['us'] = hit       # recorded only if non-empty

Where the localisers left a message blank, the pairing was established and then
discarded. `treeport` read the absent `us` as "no pairing" and dropped the row.
47 of the 75 were that: all with `us` text length 0.

`treeport` no longer infers the pairing from whether the US line happened to
carry text. It tests the fingerprint directly, against the immutable
`dialogue N.bin` it already reads for `canonical_engine`, via a new
`jp_engine_codes()` that walks our JP bytes by control width (so an operand
falling in `$F0-$FE` is not miscounted as a control). `us` text remains a valid
shortcut; a blank US message now pairs on the same evidence.

    ported 186 -> 233        unverified 75 -> 28

The remaining 28 are genuine structural differences, not lost provenance: we
carry `{ctl.FA}` conditional branches the US build removed, or a different
`{ctl.F7}`/`{ctl.F9}` order. `emit()` would refuse them anyway, since our token
count cannot map onto the US engine codes. Porting them means writing engine
bytes as well as text, which this design deliberately does not do.

    lz1CC476: 16   lz1CD2E6: 10   lz1CF6D6: 2

## Glossary updates applied (2026-09-02)

シェス → **Shess**, ガルベルク → **Gallberg**, アイスデッカー → **Ice Decker**.
Applied to `lz1DB6F6#0024`/`#0025` and to the `GALLBERG` place strip
(`r00s004#039`); locations still fit at widest 8 of 10 cells. Note the glossary
tables at lines 46 and 368 still read `Garuberk` and `ICEDECKER` while the
etymology section reads Gallberg — worth reconciling.

## Known limitations

- `treeport.py` deliberately skips four JSON rows with unresolved engine-token
  mismatches: `lz1CD2E6#0017`, `#0024`, `#0028`, and `#0100`.
- Maximum decompressed dialogue stream is 8169 bytes against an 8192-byte RAM
  ceiling.
- A late-game VWF pool stress state is still desirable.

## Combination names (segment 00:005)

`ComboNames` was never extracted and never written: it sits at $29F69C, in a
bank outside every segment the extraction covered and outside both ranges the
menu composer recognised, so all fourteen drew fixed-width out of the US
table.  The JP table is at **$285474** in `work/rom.bin`, found through the
five-way dispatch that selects the battle name tables -- the JP ROM has the
same five `lea`/`bra.s` pairs at the same eight-byte stride, and three of the
five targets match segments the extraction already carried.  The vehicle
attack names are the next entry down, at **$285556**, still unextracted.

The US names are ten-cell abbreviations, so several were unrecoverable
without the JP: TRIBLASTER is トリニティブラスター, CONDCTTHND is
コンダクトサンダー.

The combo field is ten cells / 80px: the name is drawn one cell into a region
`loc_27DD04` copies twelve wide, and ten of the fourteen US names are exactly
ten characters, which puts the frame's right border at cell 11.  The vehicle
field is eight: `Battle_VehOpenSkills` frames fourteen cells, writes its
cursor at column 1 and the two state icons at columns 11 and 12, and starts
the name at column 3.  `tools/combonames.py` refuses anything wider rather
than writing over the frame.

`ナパームミサイル` is the one name the field cannot hold with its space: 9
cells open, 8 closed up, so it ships as **NapalmMissile**.  Slots with no JP
counterpart (vehicle slot 8, and slot 6 which is empty in the JP table) keep
`NOTHING`.

## The word space is one number now, 3px

There were two.  `menuwidth.bin` gave the space a full 8px cell and
`menustrip.py` overrode it to 3 for strips, each with a comment justifying
itself.  The runtime composer reads the first; `trpatch8` previews the second
in the JSON.  So the width shown beside a name while editing it was not the
width the runtime would give that name: `Cathode Ray Tube` previewed at 10
cells and composed at 11.

The 8px was defended on the grounds that strings like `WinTiles_Meseta`
(`"        MST"`) pad with spaces to position themselves.  That does not
survive the fixed-label path: the width table is read in exactly one place,
the composer, and every padded string is chrome that never reaches it.  All
four name tables, the 160 item descriptions and every string reachable through
`ForceCompose` were checked and carry single spaces only.

`menuvwf.py` now writes 3, matching `vwffont.SPACE` in the dialogue face, and
`menustrip.py` reads `width[0]` instead of carrying its own copy, so the two
cannot drift again.  **134 names across the tables lost a cell.**

Measure cells with `menustrip.compose`, never by summing `menuwidth.bin`.
Both the preview and the runtime compute ceil(advances / 8); a pixel sum
over-measures by the last glyph's trailing gap, which no cell has to hold.
`combonames.py` got this wrong once and rejected a name that fits.

## The composer must not yield

`VWFMenu_DrawWindowRun` composes in LoadWindowTiles' slow mode when the caller
has forced composition.  It first paid the stock per-character delay inside
the cell loop, so the line still typed itself out.  **That crashed Item >
LOOK.**

A delay is `DMAPlane_A_VInt`, which queues a DMA and then spins in
`VInt_Prepare` until the VInt clears `VInt_Flag`.  The exact mechanism is NOT
established.  What is known:

  * the draw itself terminates and composes both lines correctly -- driving
    the real Leather Shield description through `VWFField_LoadWindowTiles` in
    menuharness with `DMAPlane_A_VInt` stubbed to an `rts` returns cleanly,
    15 pool tiles on one row and 11 on the next;
  * on screen the description window was empty and the game stopped, which is
    what a hang inside the first `VInt_Prepare` looks like: the queued DMA
    never runs, so nothing the composer wrote reaches VRAM;
  * the window code does not mask interrupts, so "the VInt cannot fire" is
    ruled out;
  * `Window_Create` records a pool mark and `Window_Destroy` calls
    `VWFMenu_Release`, which rolls the pool back, so a yield mid-run can in
    principle let a window free the tiles that run just allocated -- but there
    is no evidence this is what happened.  An earlier note claimed the status
    panel showed reassigned tiles; it did not, it was occluded by the equip
    frame, and that claim is withdrawn.

The yield is the only thing the paced path did that stock does not, so it is
what was removed.  Treat the fix as principled rather than proven.

The composer is atomic with respect to the window stack and has to stay that
way.  A run now composes whole and LoadWindowTiles pays its delay once
afterwards, so a line appears at once and then pauses; the per-character
typewriter is gone from these windows and is not recoverable this way.
`test_itemtext.py` asserts the composer reaches `DMAPlane_A_VInt` zero times.

## $F5 carries two operand bytes (the yes/no branch targets)

`TextCtrlCode_YesNo` ends with

    move.b  (a0,d0.w), d0     ; d0 is 0 for yes, 1 for no
    lea     $2(a0), a0
    jsr     (GetOffsetByID).l

so the two bytes after $F5 are the message ids for YES and NO.
`CTRL_OPERANDS` never listed it, so it was modelled as zero-operand and
`ctl.F5` sat in both `treeport.LAYOUT` and `trpatch.LAYOUT_TOKENS`.  Two
consequences, the second serious:

  * extraction decoded the operands as text - the Dorin scene reads
    `{ctl.F5} あうむ。` where the JP is `{ctl.F5:0001}うむ。`;
  * `emit()` takes a non-layout token's bytes from the US engine list, but a
    LAYOUT token is written bare.  So every ported $F5 lost the US build's two
    branch bytes, and the engine read the first two characters of the
    following English as message ids instead.  Answering the information
    dealer jumped into the Tonoe cutscene: wrong branch, that message's panel
    loads drew several panels at once, and its scene art landed over the town.
    Reported as "corruption after an hour idle"; the idle time was incidental.

Fixed: `CTRL_OPERANDS[0xF5] = 2`, `ctl.F5` removed from both layout sets, and
the 27 rows re-decoded so `jp` and `en` both carry `{ctl.F5:xxxx}`.

**Verification that matters:** all 27 slots now match the untouched US tree
with byte-identical operands, and there is no slot where only one side has an
$F5.  The recovered values were derived from the JP hex and agree with the US
independently.

Two follow-on repairs:

  * `_rows_per_page` split on a bare `{ctl.F5}` pattern, so an
    operand-bearing token stopped ending a page and 21 messages measured as
    one long page.  It now allows `(?::[^}]*)?`, as the line-width splitter
    beside it already did.
  * tree 27 $1A held a **fossil**: our English plus a bare $F5, ported back
    when $F5 was layout.  `treeport` edits the .asm in place and leaves
    messages it cannot port, so content that stops porting silently persists.
    The untouched US message there is EMPTY (`dc.b $FF`), and a row carrying
    an $F5 can never port into a zero-engine slot, so the slot was restored to
    the terminator.

## The Hunters Guild has eight prompts, and all eight are intact

Every one of the eight jobs can be accepted or declined.  `lz1D9436` carries
exactly eight rows with `{ctl.F5:0100}`, and the US has exactly eight $F5
slots for them - two in tree 26 (Mile ranch $14, Rocky $1A) and six in tree 27
($1F $24 $28 $2D $31 $35).  The JP guild is one stream; the US split it across
two trees, and `tree_group` maps the rows to whichever tree matches.  All
eight land on an $F5 slot with byte-identical operands.

An earlier note here claimed the Rocky job was the first guild job and a
tutorial, and therefore not optional.  That is wrong on every count and is
withdrawn.  It was invented to explain a slot that only looked prompt-less
because `canonical_text(0x1A)` had been called with 0x1A as the TREE number -
26 - so the comparison was reading tree 26 throughout.

**Do not "repair" a tree with `treegen`.**  It emits trailing alignment
padding as an extra message (`dc.b " "`), so a fresh generation looks one
message longer than the live source in 17 of 43 trees.  That is treegen's
artefact, not damage.  Regenerating tree 27 on that false reading also cost 14
translations the current porter can no longer place; they were restored from a
snapshot.

## The pool cannot be reclaimed while battle keeps no bookkeeping

REVERTED, twice.  Understand this before trying a third time.

`VWFMenu_Sweep` decides liveness by reading `Plane_A_Buffer`.  Acting on that
answer is only safe where something maintains the pool across windows, and
every `SaveRegion` / `Mark` / `Release` / `RemapRegion` call site is inside
`Window_Create` / `Window_Destroy` -- the FIELD window system.  Battle has its
own window code: it block-copies plane regions with `loc_27DD04` and keeps
none of that bookkeeping.  So a tile referenced only by a saved battle window
looks dead to the sweep, reuse hands it out, and the restore puts back a cell
index pointing at another string's glyph.

Two attempts, both wrong:

  1. Sweep at `SLOTS - 31` and let `StripEnsure` reuse a free run.  Fixed the
     item list; corrupted the battle Skill list ("Illusion" through the tail
     of "Double Slash") and collapsed the framerate re-uploading tiles.
  2. Gate both on a1 lying inside `Plane_A_Buffer`.  Does not separate them:
     `loc_199E` draws the battle Tech list at **$FFFF8600**, inside the plane.
     The Tech list scrambled when paging from page 2 back to page 1.

Both were reverted. The next implementation added a field Item-page-only
scope: `Win_ItemList` swept once before its synchronous row loop and permitted
contiguous strip reuse only until the loop ended. It also made strip metadata
atomic and made composed strings preflight their actual size before a
field-only sweep. Battle never sweeps, regardless of whether `a1` happens to
point inside `Plane_A_Buffer`.

The 2026-09-09 playtest showed that this was necessary but not a final
resolution:

  * Item rows were blank for one or two frames and then populated normally.
    The persistent strip failure was no longer observed, but the transient
    remains undiagnosed.
  * Hunter Knife and Claw LOOK descriptions still stopped mid-sentence. Their
    source and assembled data were complete; two proportional rows could still
    exhaust the live pool. All 320 static description rows fit the original
    28-cell renderer (longest 26), so `Win_ItemActionLook` now calls the
    pool-free `LoadWindowTiles`. Dynamic item notices stay proportional.
  * Tech page 2 -> page 1 still corrupted. The earlier 12-to-14-column widening
    missed `loc_E8C`, the helper used only by `Battle_TechPrevWin`; it now
    copies all 14 columns.
  * Double Slash and Illusion could fail to render because Tech/Skill/Item
    strip allocations remained charged after a submenu closed. All six final
    selected/cancelled exits now restore `VWFMenu_PoolTop` to
    `VWFMenu_BattleBase`. Page transitions do not roll back while their
    private buffers still reference the allocations.
  * Technique User could later display partial `Res`, and the level-up panel
    could display `Technique has been mastered!` with no name. Technique User
    actually reads full `Resta` from `EnemySkillNames`; it never reads the
    legacy `RES` entry. Two remaining slots reproduce the partial four-cell
    composition. Under the same pressure, the full translated learned-Tech
    strip fails atomically and leaves its three stock field cells blank.

The last pair came from transient battle surfaces outside the submenu
lifetime. Player action names (`loc_4A94` -> `loc_4B6E`), enemy action names
(`loc_B4E0` -> `loc_B59A`), and the recurrent results panel (`loc_4624`)
now use three dedicated marks. Each rollback occurs only after that exact raw
battle buffer is gone or immediately before the same results panel is
replaced. No battle sweep or global reset was added, and these marks are not
conflated with the command-menu `VWFMenu_BattleBase`.

`test_strip.py` covers scoped/unscoped allocation, fragmented capacity, stale
Hunter Knife metadata, and partial-visibility run pinning. `test_itemtext.py`
audits every LOOK row, confirms the fixed renderer, and retains field/battle
overflow checks. `test_battle_tech_layout.py` covers all six 14-column paths
and all six final submenu releases. The complete source build has 0 errors and
0 warnings. `test_battle_text_lifetime.py` reproduces both later symptoms
under one measured pressure state and verifies all three new lifetimes;
`disasmport.py` and all ten regression scripts pass. Current `ps4en.bin`
SHA-256 is
`3F10D33007050DB769CC2A6CEF713698858E73E85D22AC51DEF2B8F00E6527DC`.
Exact emulator reproduction is still required before calling these runtime
issues closed.

### Two testing lessons from this

Three test files -- `test_paths`, `test_strip`, `test_wrap` -- computed an `ok`
flag, printed "FAILURES ABOVE", and exited 0 regardless; their `assert`s only
guarded symbol lookup.  A suite run reported them green while `test_strip` was
printing four failures on its own stdout.  All three now
`sys.exit(0 if ok else 1)`.  When adding a test file, check it can fail:
`for f in tools/test_*.py; do grep -L sys.exit $f; done`.

And do not assert a bug at one arbitrary magnitude. `test_itemtext` briefly
asserted "a run at prefill 60 still blanks"; an unrelated width change made it
stale. The durable composer test derives the run's actual cell count and leaves
exactly five slots. The durable strip boundary remains: an unscoped strip at a
full pool fails, while an explicitly scoped field allocation may reuse a whole
contiguous dead run.

## Hunters Guild job titles (segment 00:007)

Nine `dc.b "...", $FE` strings at $071F6E, each separately labelled and listed
through the self-relative word table `HuntersGuildTextOffset`.  Never
extracted.  The JP originals are at **$071D96** in `work/rom.bin`, found by
searching the JP ROM for the reader's own instruction sequence -- `lea (X).l,a1
/ moveq #7,d7 / moveq #0,d6` -- which occurs exactly once.

They now COMPOSE, via `VWFMENU_GUILD_LO/HI`, which is what lets them say what
the Japanese says: "The Ranch Owner of Mile" is 23 characters and could never
have fit the 16-cell fixed field, but it composes to 15 cells.

That costs pool, and this board is the worst case in the game for it: eight
rows drawn at once, all live on the plane together, so the sweep can reclaim
none of them.  `tools/guildnames.py` therefore checks two budgets - each
title against the 16-cell field, and the whole board against the pool.  The
board check enumerates the 256 real boards (each row shows its own title or
"Listing Pending" when the job is not yet listed) rather than counting all
nine strings together, which over-states it: a substituted row costs the
placeholder INSTEAD of its title, not as well.  Measured worst case **76 of
83**, seven spare.

## VWFMENU_COMBO_HI was the wrong label

The order in ROM is `ComboNames $29F69C`, `VehicleData $29F74E`,
`VehicleAttackNames $29F79C` - the stats table sits BETWEEN the two name
tables.  `VWFMENU_COMBO_HI = VehicleData` therefore covered only ComboNames,
and every vehicle attack name went on drawing fixed-width after being reported
as composed.  The ceiling is `VehicleSkillData`; spanning VehicleData is
harmless, since it is stats and never reaches the composer as text.

Caught only because `test_paths` gained a case for it.  The lesson is the
cheap one: assert the ceiling on a label, and assert the label PAST it draws
fixed, or a range that silently covers nothing looks exactly like one that
works.

## The location banner

`WinGroup_PlaceName` is a family of NINE pre-built windows (indices 0-8) that
widen by one cell per index and step their X origin left every second index --
the whole-cell way to grow a box and keep it centred.  `loc_66434` counts the
name's characters, creates window `count - 2`, and draws the text two cells in
from that window's left edge.  In fixed-width Japanese a character is a cell,
so the name landed right every time.  Nothing centres text in a box.

Note WHICH characters it counts: the bytes in `PlaceNames`, which still hold
the US strings, because menu lists draw prerendered strips keyed by that
table's OFFSETS and never read its text.  So the box is sized by a US name
while our translation is drawn inside it.  Measured over all 54:

    already centred          30
    text 1-3 cells too far right  15
    text 1-3 cells too far left    9
    text OVERFLOWS the box         5   (HANGER, THE EDGE, MYST VALE ...)

Two changes.  The box is sized by `max(characters, cells)`, so the original
width stands as a FLOOR -- sizing by cells alone shrank "ZEMA" and "MILE" to
labels that read as a mistake -- and grows only for the five whose English is
wider in cells than the Japanese was in characters.  And the text is centred in
the box interior instead of always starting two cells in: the frame takes a
cell each side and the odd cell of slack goes left, which is where the original
put it too.  Byte 0 of the window entry is the width, so the placement follows
whatever size was chosen.

Result across all 54: no overflows, 35 exactly centred, 19 with the odd cell
left.  Highest window index needed is 8, which the family exactly covers.

### The descriptive place names were half-translated

Nothing was missing from segment `00:004` -- 54 rows, 54 table entries, none
empty.  But 24 of the names are descriptive phrases rather than transliterated
proper nouns (they carry hiragana), and half of those were still US wording.
Twelve were changed: seven needed only Title Case, five had lost the sense.

    ちかかくのうこ   SUBSTORAGE  -> Sub-Hangar       geo 格納庫 is a hangar
    ガンビアスだいじいん GUNGBIUS   -> Gungbius Temple  だいじいん was dropped
    ちかそうこ      BASEMENT    -> Storehouse       地下倉庫
    なぞのざんがい    WRECKAGE    -> Mystery Wreck    謎の was dropped
    ひみつのつうろ    SECRET PATH -> Secret Passage   通路 is a passage

The dialogue says "Gungbius Grand Temple" in 33 places, but the banner cannot
hold "Grand" -- `Gungbius Temple` is 10 cells, the exact ceiling.

Ceiling note: 10 cells, enforced from two directions.  `trpatch8` caps
`00:004` at 10, and the window family stops at index 8, so an 11-cell name
would index past the table.  Keep both in mind before lengthening one.

`MysteriousValley` is run together only because "Mysterious Valley" is 11
cells.  Left as it is; "Mystery Valley" is 9 if the run-together ever grates.

### Two things this file said before that were wrong

The family has 9 entries, not 15; and the banner was NOT "24px left of centre".
Both came from measuring the English `en` strings, which run to 16 characters,
instead of the US byte table the engine actually counts, which stops at 10.
Measure the table the code reads, not the JSON that fed it.

## Verification

Run after menu/VWF changes:

```text
python tools/checkbuild.py
python tools/test_party_reset.py
python tools/test_strip.py
python tools/test_reveal.py
python tools/test_wrap.py
python tools/test_battle_tech_layout.py
python tools/test_fieldtext.py
python tools/test_paths.py
python tools/test_treeport_controls.py
python tools/test_itemtext.py
python tools/test_shared_cells.py
python tools/test_giresta_window.py
python tools/battle_drive.py work/pd-slot7.state --rounds 1   # composed build, in BlastEm: expect blank 0, lag well under 10%
python tools/field_drive.py work/field-slot0.state "w30 R R L L B C"   # Item page flips: refused 0, flips under 15 lag
```

All of these pass for the current build.

## Efficient future prompt

“Read `work/STATUS.md` and `work/glossary.md`. Continue with [one bounded
translation range or one reproducible bug]. Build and run the listed checks.”

For a bug, include the ROM hash, savestate name, exact menu/event, expected
behavior, and first visible failure. For translation, specify one event range
or one name table per task.

## 2026-09-16: field chrome pool / saved-state migration checkpoint

The composed field-menu pool is now 114 slots: the established 88 plus the
complete duplicate uppercase bank at `$7C0-$7D9`. Those 26 tiles are
field-only capacity. Battle remains capped at 88 because that VRAM bank can
also contain battle sprite art; allocation growth, hash lookup and free-slot
reuse all enforce that boundary.

The larger arrays use RAM layout `VWF3`. `VWFMenu_EnsureLayout` migrates both
legacy ten-byte save records and the intermediate `VWF2` layout in place,
relocates the resized reference/chain arrays, clears the rebuilt hash buckets,
and initializes the new tails. Save records are now compact eight-byte
composition keys, allowing 104 records in the same save-stack footprint.

Direct BlastEm replay of the user's `slot_6.state` covered Tech -> Skill ->
Equip after migrating the old state. Tech opens at 113/114 slots with 13 lag
frames; Skill opens at 114/114 with 8 lag frames; Equip opens at 85/114. No
open refused a cell. Tech and Skill close make 23 and 5 allocation attempts,
respectively, only during frames where `VWFMenu_ReclaimInhibit=1`; the completed
screens have zero visible pool cells with a dead reference and zero unresolved
save markers. Thus these are animation-only pressure, not persistent reused
tiles.

The same checkpoint moves field Tech/Skill usage text through VWF before and
after the effect, adds `/2-Handed` as composed chrome, and retains the prior
Save-window, Each-got/EXP, DYING, Miracle, Berserker, COMMAND and retreat-text
fixes. Old save states that already lost cells cannot reconstruct those old
cells, but closing and reopening the affected page rebuilds them cleanly.

Fixed-alphabet audit: normal field menu text no longer needs the duplicate
uppercase copy; it is pool storage now. The known live alphabet holdout is
the battle-results prompt family at `loc_27E784..loc_27E7C6` (`But pack is
full!`, give-up/discard prompts, and `Yes`/`No`). The generic fixed fallback
is retained for safety, and `$7C0` cannot be treated as pool storage in battle.
Numerals, punctuation, cursor/frame glyphs and UI icons are separate concerns
and must remain. Migrating and lifetime-testing that result-prompt family is
the next prerequisite before removing the remaining lowercase fixed glyphs or
the fallback wholesale.

`python tools/checkbuild.py` and all 13 `tools/test_*.py` files pass. The
published artifact is `work/ps4en_compose.bin`, SHA-256
`69C7D8A88BCF28149AC592327792160C5EEB52E76672AA9BC21841B018A0DA02`.

## 2026-09-16: full save ledger, status tiles and result-panel lifetime

The composed saved-region ledger now has 114 records, matching all 114 field
pool slots.  The previous 104-record ceiling was the cause of the user's deep
Status > Tech > Skills / Equip corruption: the final ten covered keys were
left as raw tile IDs and later restored after those slots had been reassigned.
RAM layout `VWF4` moves the composed hash to 32 heads at `+$950`, keeps the
114 chain links, and uses `+$5C0..+$94F` for the full ledger.  VWF3 states
migrate without moving their existing keys, refs, links or compact records;
only the derived hash heads are cleared and rebuilt.

`DYING`, `PARA ` and `POIS ` now route through the VWF chrome path, so they no
longer read the duplicate-uppercase tiles that the field pool reclaims.
`COMMAND` receives a one-pixel left lead inside the composer, centering its
38-pixel label in the five-cell field.  Load Game level numbers move from
column 8 to column 6, and merchant choices are now `Buy` / `Sell`.

Battle-result replacements are double-buffered: the currently visible panel's
cells remain resident while the next panel composes, and a commit helper first
publishes the new plane map and then sweeps Plane A.  This removes the live
tile overwrite behind the level-up/item/attribute flicker without expanding
the battle pool beyond its safe 88-slot boundary.  The early battle routine
retains its previous byte length and all replacement calls use six-byte
absolute forms, preserving later native-savestate code addresses.

The user's correction about Reverser was honored: no Reverser-specific change
was made.  Its pre-effect and post-effect field messages already use the forced
VWF path in this build.

`python tools/checkbuild.py` and all 13 `tools/test_*.py` files pass.  The
BlastEm GDB harness can load `slot_7` and `slot_8`, but these two native states
hit the 68000 address-error trap during the first reset-restored VInt before a
joypad frame is reached, so final visual progression needs a manual BlastEm
pass.  Published artifact: `work/ps4en_compose.bin`, SHA-256
`BD1B16134616E43B83226EAA2E4A658EAD1511A6FE71A3494609C3BCDE2ACBEB`.

## 2026-09-16: saturated-ledger fail-safe and final menu alignment

The latest `slot_0.state` proves that active saved-region keys can exceed the
114 resident pool slots: the pool and ledger are both at 114, while the next
nested Status subpage still covers new keys.  Matching the ledger size to the
pool therefore was necessary but not sufficient.  `VWFMenu_SaveRegion` now
fails closed when its ledger is full: it leaves the backup cell as a raw tile
ID, pins that physical slot, records the overflow lifetime in the window's
save mark, and blocks reclamation until the matching close.  `SaveMarkPop`
then restores the real mark and retires that gate.  The new regression fills
all 114 records and verifies that the raw tile survives replacement without
being recycled, then that both mark and gate unwind correctly.

Party ailments now clear nine complete cells of the former `Level <n>` field
before drawing `DYING`, `PARA`, or `POIS`, eliminating the surviving final
level digit.  `COMMAND` moves one additional pixel right (a two-pixel lead in
its 40-pixel field).

Load Game no longer draws the dead `Chaz:LV` summary.  Each slot reads its
saved lead-character ID, resolves the translated name from `CharNameData`,
composes that RAM-built `Name:` through the VWF, draws `LV` separately at
column 15, and right-aligns the two-cell level field at column 18.

The ROM assembles with zero errors and warnings.  `python tools/checkbuild.py`
and all 13 `tools/test_*.py` files pass, including the new saturation,
full-ailment-clear, dynamic-leader, forced-VWF and alignment assertions.
Published artifact: `work/ps4en_compose.bin`, SHA-256
`710903FAA262F3612F88C765CF67B9392B747B45110EAF9A7C0856D6145097D8`.

## 2026-09-16: Rudy-anchored Load Game and physical ailment clear

The first Load Game revision incorrectly used the saved party leader and put
the numeric field at column 18. The slot interior ends at column 10, so the
numbers wrapped into the following slot: slot 1's 27 appeared in slot 2 and
slot 2's 42 appeared in slot 3. The summary now always resolves translated
character record 0 (`Rudy:`), matching the protagonist-centric level already
stored at SRAM offset `$811`. It composes the unabbreviated `Level` label at
column 6 and draws the two-cell level field at column 9, ending at the slot's
rightmost interior cell. Single-digit levels retain their leading blank and
therefore share the same right edge as double-digit levels.

The prior ailment clear reused `loc_2AA43C`, but that address could be routed
through a composed chrome range; a run containing only spaces can emit no
cells and leave the old rightmost digit untouched. The new extension-ROM
`VWFMenu_StatusLevelClear` is outside all compose ranges and is verified to
take the fixed fallback, physically writing nine `$680` blank cells before
`DYING`, `PARA`, or `POIS` is drawn.

The ROM assembles with zero errors and warnings. Build invariants and the
focused path, save-ledger, fixed-clear, reveal, tree-port and wrapping
regressions pass. Published artifact: `work/ps4en_compose.bin`, SHA-256
`D73D1E33F0E08087C5BC0E616DADE85B66FC3949C8D1EC41C9A45FF801C5A609`.

## 2026-09-16: bounded party-ailment clear

Manual testing confirmed the Rudy-anchored Load Game layout. It also exposed
that the party-ailment clear confused the nine source characters in
`Level <n>` with the five rendered cells actually occupied by the field.
Starting at window X+6, `Level` composes into X+6..8 and the two-digit number
uses X+9..10. Writing nine fixed blank cells therefore crossed the party
window boundary and produced the horizontal blank bands visible beside every
afflicted character.

`VWFMenu_StatusLevelClear` now writes exactly five physical blank cells. This
still removes the complete label and both digits before `DYING`, `PARA`, or
`POIS` is composed, while stopping at the field boundary. The path regression
now asserts both the fixed-renderer route and the exact five-cell span.

The ROM assembles with zero errors and warnings. Build invariants, status-path
tests, and shared-cell lifetime regressions pass. Published artifact:
`work/ps4en_compose.bin`, SHA-256
`6E25AD2DF6315EB319AD9C1B8CA8D884E99D2363404EF815B65420C3F17475AC`.

## 2026-09-16: saved-region dereference and DYING-target messages

The native Skills-subpage state showed all 114 VWF menu slots falsely live.
`VWFMenu_SaveRegion` converted successfully saved cells to `$700` markers but
did not release the corresponding physical tile reference. Repeated nested
Status subpages therefore saturated the pool; subsequent strings emitted blank
cells, and those blanks remained over the status and equipment windows after
returning. The marker path now dereferences the physical tile before replacing
the saved cell. The raw-overflow path remains pinned until its window closes.

`VWFMenu_Deref` now reverse-maps the non-contiguous physical tile pool instead
of assuming tile IDs are contiguous slot numbers. A focused regression draws a
shared name twice, markerizes one saved cell, and verifies that its reference
count falls from two to one without invalidating the surviving owner.

The Tech and Skill failure-message paths already composed translated character
names into RAM, but their final sentence renderer still used the fixed-width
loader. Both now force `VWFField_LoadWindowTiles`, fixing the broken name and
fixed-width `is on the verge of death!` warning for DYING targets.

The ROM assembles with zero errors and warnings. `checkbuild.py`, path tests,
menu-pool tests, reveal tests, and shared-cell lifetime regressions pass.
Published artifact: `work/ps4en_compose.bin`, SHA-256
`69279228D24F577F568BD753BAEDDA7793DD0ABAB193B2EAB6DD1349B9FC95A4`.

## 2026-09-16: synchronize shared refs before saved-region dereference

The new `slot_3.state` captured a distinct shared-cell lifetime failure after
Status -> Rudy -> Tech -> Skills -> back twice. Its key table and physical VRAM
were internally synchronized, and both closed Tech-window backups remapped
perfectly. However, `Guardian Mail` at logical X=4..10 was corrupted in its
middle cells even though the Tech window began at X=10: those cells were never
covered and remained visible for the whole sequence. Their content-keyed slots
were shared by text inside the covered region, whose `SaveRegion` dereference
recycled them because the cached reference multiplicity was stale.

Field `VWFMenu_SaveRegion` now runs `VWFMenu_Sweep` before markerizing any
backed-up cells. This rebuilds exact multiplicity from the visible Plane A map;
each subsequent marker dereference can therefore remove its covered owner
without freeing a slot still used elsewhere. Battle retains its existing
lifetime rules. The regression deliberately gives two visible copies of a key
only one cached reference, saves one copy, and verifies the other remains live.

The Japanese remnants and lowercase alphabet visible in VRAM are not evidence
of this failure. They are intentionally outside `pooltile.bin`: lowercase and
the remaining fixed fallback paths still depend on their stock tiles. The
duplicate uppercase `$7C0-$7D9` bank is the alphabet range currently reclaimed
for the 114-slot field pool.

The ROM assembles with zero errors and warnings. All 13 `tools/test_*.py`
files and `tools/checkbuild.py` pass. Published artifact:
`work/ps4en_compose.bin`, SHA-256
`7B99C4F5B5D6921FBDA4649CC3C571E266219A4F8B0C4DB86225C193912D9DE5`.

## 2026-09-16: 146-slot field pool landed; two latent allocator bugs fixed

This closes the checkpoint the previous session left half-edited.  Its
17:52 build carried four fixes that were never recorded here: RAM-built Save
confirmation and money-chest messages force `VWFField_LoadWindowTiles`; the
single-digit battle EXP formatter clears its stale five-cell tail; ORDER's
direct window restore now sets `VWFMenu_RemapIdx` for its own region before
the reveal; and `VWFMenu_DrawString` composes any unclassified run that
contains A-Z or a-z, so the fixed path can never draw a letter again.  Those
are all present and pass `tools/test_paths.py`.

The 146-slot extension was then applied in two pieces - constants and the
generator at 17:57, `vwfmenu.asm` at 18:02 - and the tree was left between
them: it assembled, but `tools/checkbuild.py` failed five invariants and
seven of the thirteen tests failed.  What was wrong, and what changed:

* `tools/menupool.py` had both a widened `CONTIG` (to `$6D8`) and the new
  `FIELD_FONT_EXTRA` list for the same tiles, so `$6D6` was a duplicate and
  the generator aborted.  `CONTIG` is back to `$682-$6C0`; the 32 font tiles
  append as slots 114..145, and slots 0..113 are byte-identical to the
  published 114-slot order.  Slots 114..145: `$6C1-$6D2` (a-r), `$6D7` (ü),
  `$6D8-$6DE` less the three already scattered (the Japanese remnants),
  `$7F8-$7FF` (s-z).  `checkbuild.py` sizes the base `SaveStack` by
  `VWFMENU_BASE_SLOTS` (records 114..145 are in `SaveStackX`) and no longer
  counts the long-reclaimed voicing marks `$7EE/$7EF/$7F4/$7F5` as reserved.
* `VWFMenu_Sweep_Range` was mid-conversion: the `(a1,d0.w)` index had been
  removed but `lea (VWFMenu_Refs)` not yet replaced, so every swept cell
  counted into `Refs[0]`.  It, `Deref`, `SaveRegion`, both glue paths and
  `GlueBegin`/`GlueRemember` now go through the tail-aware helpers, and a new
  `VWFMenu_SlotCap` bounds every slot derived from a plane cell by game
  mode: 146 in the field, 88 in battle.  That bound matters now - the tails
  are `Enemy_Stats`/`Obj_Fighters` once battle is running, and
  `VWFMenu_BattleResultCommit` sweeps in battle, so a lowercase or Japanese
  tile on the battle plane would otherwise have counted into enemy data.
  `KeyAddr2`/`RefAddr2` answer in a2 with a1 preserved for the composer.
* **Latent bug 1 (from 17:57):** `moveq #VWFMENU_SLOTS` with 146.  moveq
  takes -128..127 and AS wrapped it to -110 without a warning, so the hash
  chain bound went negative on its first decrement and every lookup missed:
  no tile sharing at all.  Both sites are `move.w`; `checkbuild.py` now
  resolves every `moveq #VWFMENU_*` and range-checks it.
* **Latent bug 2 (shipped since the hash index):** `VWFMenu_KeyUnlink`'s walk
  feeds `NextAddr` through d0 and never restored it, so whenever the stale
  key of the slot being claimed shared a bucket with a live slot that was not
  the chain head, `Alloc_Take` linked, counted and RETURNED the chain node
  instead of the claimed slot - the cell drew another glyph's tile.  Every
  fresh slot's all-ones key hashes to bucket 0; with the old 128 buckets that
  collided rarely, with the 32 buckets the enlarged ledger left room for it
  was one glyph in 32, which is why the emulator tests caught it here.  It is
  a plausible cause of the sporadic name corruption (Rudy, Thray) seen in the
  published build.  `KeyUnlink_Done` restores d0; `test_shared_cells.py`
  has a case that fails without the fix (the cell held slot 5 for slot 0).
* Save-record markers now reach `$700+145 = $791`.  `$700-$77F` is Plane B's
  nametable and `$780-$793` the sprite table; no Plane A cell names either.
  Real tiles resume at `$7C0`, so `VWFMENU_SAVEN` must stay below 192.
* `tools/menuharness.py` gained `SlotLayout`, which resolves a slot's key,
  count, link and a record's key to base or tail exactly as the helpers do.
  `test_shared_cells`, `test_itemtext` and `test_strip` seed through it -
  they had been writing 146 keys/counts over the 114-byte base arrays.
  `test_party_reset`/`test_reveal` expect the `VWF5` stamp, `test_reveal`
  also checks a migrated state's tail is initialised, `test_menupool` pins
  the 114 + 32 composition, and `test_wrap` measures `ITEM`'s cell count
  instead of assuming the fixed font's four (it composes to three now).

Reclaimed-tile safety, re-checked: the only `$6xx`/`$7Fx` immediates that
touch the 32 new tiles are `Battle_LoadObject` type IDs (`$6C4`, `$6C8`,
`$7F8`, `$7FC`) and a palette value (`$6CE`) - the false-positive class the
contiguous-range exemption already describes.  Every routine that names
`$FFFF4200-$443F` by symbol or literal is battle code, and
`GameMode_LoadBattle` runs `VWFMenu_Reset` before `Battle_SetupEnemyData`.

The ROM assembles with zero errors and warnings.  `tools/checkbuild.py`
(18 invariants) and all 13 `tools/test_*.py` files pass.  Not yet done: a
manual BlastEm pass over the saved states (Save confirmation, money chest,
single-digit EXP, ORDER teardown, Rudy/Thray) against this build.
Published artifact: `work/ps4en_compose.bin`, SHA-256
`B5BDC086E70626623B5AD575B0D9C39282E3CD3E0091C1C6FFD2F961A72E961F`.

## 2026-09-16: ps4.asm sizes restored; EXP/ORDER/Save verified in BlastEm

The 17:52 fixes had grown three `ps4.asm` routines in place - the EXP
formatter `loc_3138` (+20), the ORDER restore (+6: a `move.w` to
`VWFMenu_RemapIdx` before `jsr loc_6881E`) and the money-chest message (+2:
`bsr.w LoadWindowTiles` became a six-byte `jsr`) - so every address from
`$32DA` to `$7AB2F` had moved by up to 28 bytes and no native savestate from
the published build could replay (the address-error traps on slot_7/8 were
this).  All three are back to their stock sizes: `loc_3138` is a `jmp` to
`VWFMenu_BattleExpCompact` padded to 22 bytes, ORDER calls
`VWFMenu_OrderRestore` (names the region, then `jmp loc_6881E`), and the
chest's `lea ($FFFFE220).l` is `.w`.  Against `ps4built.prev.bin` the ROM
now differs only in place: `jsr` targets into the extension, the three
sites, and the 17:52 size-neutral edits.  `test_paths.py` pins the 22-byte
stub and the wrapper's bytes.

Replayed under `tools/blastem_drive.py` on this build:

* slot_4 (battle result "Each got 7 EXP 7"): re-entering `loc_30C2` with
  d1=7 from the state draws "Each got 7 EXP" - no trailing digit.
* slot_6 (ORDER): closed everything, STATUS > ORDER, picked all four,
  screenshot every two frames through the teardown.  The frame that used
  to show garbage (ORDER window shrinking over TALK/MACRO) shows the right
  glyphs; the final main menu is intact.  Names render correctly throughout.
* Save prompt (Start > SAVE > slot): "Previous Data / will be erased. OK?"
  composes; backed out with B, `save.sram` byte-identical afterwards.
* Money chest: no state; same forced-VWF path as the save prompt, pinned by
  `test_paths.py`.
Pool high-water mark across the session: 74 of 146.

Published artifact: `work/ps4en_compose.bin`, SHA-256
`4B01E36E227DDA7FE49CCC42CC131F98F7E53B82A917E8EB3AB642160E145DAD`.

## 2026-09-16: vehicle battles - pool base above the labels, $7C0 letters restored

slot_7 (Land Rover vs Grass Hound/Forced Fly, OPTION list open) showed two
things.  `ATTACK/OPTION/RUN` read `Cluster / Bomb av`: `Battle_VehOpenMainOptions`
took `VWFMenu_BattleBase` before composing its three labels, and
`Battle_VehOpenSkills` rewinds to that base while the label window is still
up, so the list's names landed on the labels' slots (a character's command
menu is icons, which is why the character path never showed this).  The
capture now sits after the third `loc_27DB92`; same instruction, same
routine size (`$DC`), pinned by `test_paths.py`.

The HUD read `a0:740` for `SP:740`.  `loc_75BC` writes tiles `$7D2 $7CF
$7F3` straight from the `$7C0` font copy, and `Battle_OpenMacroLetters`
draws its A-H from `$7C0..$7C7` the same way - but the field pool owns
`$7C0-$7D9` (slots 88..113) and the bank is loaded exactly once, in
`Title_ArtPtrs`, so a battle inherited whatever the field composed there.
`tools/menufixed.py` now also emits `vwf/menualpha.bin` (the stock A-Z,
26 tiles) and `VWFMenu_Reset` uploads it to `$7C0` through
`VWFMenu_BankRestore`; `GameMode_LoadBattle` calls Reset before its VRAM
fills (which clear `$0000` and `$2000` only), and in the field the pool
simply re-composes over the letters.  `test_party_reset.py` checks the
VRAM image after Reset.  No ps4.asm address moves.

Replayed on this build from slot_7 with a one-off bank restore standing in
for battle entry: HUD `SP:740`; the next turn's menu took base 23 above the
labels, and opening OPTION twice left `ATTACK / OPTION` intact.

Also: the field main menu is one unit narrower (`WinGroup_Menu` entry 0,
`$08` -> `$07`, 8 cells): STATUS plus cursor needs seven, the submenus and
the ITEM list overlay it as before.  Cosmetic only - blank cells cost no
pool slot.

`tools/checkbuild.py` and all 13 `tools/test_*.py` pass.  Published
artifact: `work/ps4en_compose.bin`, SHA-256
`9BF5CC9E667ED644E676DD0D9E903AA1A6900A52ED5A2CC25685CB0D6BA22DB3`.

## 2026-09-16: "EXP and", closed-up names spaced, proofreader on the real face

`loc_27E5C3` is `" EXP and"`: the result reads `Each got <n> EXP and` /
`<m> meseta!`.  Replayed from slot_4 with 7 and 12345: five digits still fit
the box.  The four bytes of growth sit in the string tables before
`align $8000`, so no code moved (nothing executable follows those tables).

Names that were closed up to fit the fixed face are spaced again, every one
measured against its window with `menuwidth.bin` first: Titanium Slicer,
Titanium Shield, Plasma Dagger, Zirconium Gear, Zirconium Armor, Composite
Armor, Pelorie Mate, Termi Pennant, Carved Sandworm, Stealth Canceler (items,
widest 72 px of 80), Hyper Jammer and Medical Power (skills, 8 of 8 cells),
Napalm Missile (vehicle, 8 of 8), Grass Slaughterer (enemy, 77 px of 80; its
effect line is still 17 of 18 cells).  `LaSheek` is left as a name.  The
profession is `Newman` (PSO/PSU spelling) in `VWFMenu_ProfessionNameData`
and both JSON lists.  Regenerated through menustrip/enemynames/combonames
and the vwf binaries; `trpatch8 check` clean.

`tools/proofread.html` now embeds the current `menufont.bin`/`menuwidth.bin`
(it had the Sep 2 face) and `proofsync.py` generates `MENU_LIMITS` from the
generators' own budgets - menustrip, combonames, guildnames, spacemenu and
trpatch8's index split - so every composed segment (items, techs, skills,
places, combos, vehicle skills, guild titles, spaceship menu, party and
enemy names, actions, professions) gets the true-size cell preview with its
field shaded, and the legacy JP-ROM byte spans no longer count for JSON rows
the source build assembles.  Item descriptions (`01:003`) get a stacked
per-line preview against the 24-cell window; `itemdesc.py` measures lines in
pixels the same way instead of counting characters.  Worth a pass: the
widest description line is 111 px of 192 - they were written to the old
24-character limit and could carry more per line.

Fixed-width audit.  Static: `LoadWindowTiles`, `RunText` and both battle
renderers (`loc_27DB92`/`loc_27DB9C`) hand every run with a letter to the
composer; the only raw letter-tile writes in ps4.asm are the battle MACRO
letters and the vehicle HUD label, both served by the `$7C0` restore;
`VWFMenu_FixedArt`/`FixedMap` are unreferenced.  Dynamic: with a breakpoint
on `VWFMenu_DrawString_Label` through every field menu and subpage, the SYS
menu, the vehicle battle menus and the result screen, the fixed path drew
only blanks and control glyphs.  Digits, `:`, `.`/`'`/`,`, cursor and frame
glyphs stay fixed by design.

The field main menu note above should read 8 cells, not 16: widths in
`WinGroup_Menu` are cells, so `$07` is one cell narrower than stock.

`tools/checkbuild.py` and all 13 tests pass.  Published artifact:
`work/ps4en_compose.bin`, SHA-256
`10AEE86B2B73922A58FDC991F1AB3AE5B6CCE367EAF572E371C7C8ED5CD1A4FB`.

## 2026-09-16: description pass, two faces; the $21A000 align; CAN EQUIP

Item descriptions (`01:003`) are shown in two places with two faces, and a
line must fit both: Item > Look composes with the MENU face into the 24-cell
message window (192 px; measured on screen, "A medicine that" is 64 px), and
shop vendors show the same line through the dialogue engine in the DIALOGUE
face (256 px box, `dialogue_reflow.LIMIT`).  The dialogue face is ~1.45x
wider, so it binds: 255 px there is ~176 px in the menu face.  `trpatch8
check`, `itemdesc.py` and `proofread.html` now measure every line in both
(the page cue reads `Look 160px of 192 . shop 231px of 255`) and refuse a
third line.  `trpatch8` had been measuring only the dialogue face; for a
while today `itemdesc.py` measured only the menu face - both were wrong.

All 158 translated descriptions were re-read against the JP and rewritten
to fill the box, breaking at sentence boundaries where there are two.
Accuracy fixes of note: Phantasm Robe raises evasion; Impacter is a shock
gun of weak power; Ceramic Helm traps heat and gets stuffy; Struggle Axe is
"built for battle, quite heavy"; Alsulin is a secret medicine; the ocarinas
are strange instruments (JP がっき), not devices; Silver Tusk is handed down
through the musk cat clan; Termi Pennant shows Termi's name AND scenery; Land
Master crosses quicksand, Ice Decker smashes ice walls in cold regions;
Stealth Canceler detects enemies with stealth; Carbon Suit is often found in
ancient city ruins.  "????" items stay "????".  Widest lines now 253/255 px
(dialogue) and 186/192 px (menu).

The user's JSON pass (title-case locations, `Mystery Wreckage`, `Mysterious
Valley`, `PelorieMate` restored) went through every generator.  An 8-byte
dialogue edit from 15:28 (DialogueTree7) pushed the trees/examine/credits
block from `$219FFC` to `$21A004`, across the `align $1000` before
`loc_200000`, and moved `Battle_SetupWindow`, `loc_27DB92`, the battle
strings and `EnemyNames` by `$1000` - the savestate-breaking shift again.
The block's `even`s are not load-bearing (RunText/RunText2 and
GetOffsetByID are byte readers; `padding off` means AS adds none), so the
17 between `loc_1FE7E6` and `CreditTextHeaders` are dropped (comment left in
their place; `examinecredits.py --write` preserves that) and the block ends
at `$219FF0`: `loc_200000` is back at `$21A000` with 16 bytes of slack.
`checkbuild.py` now pins eight code anchors (`GameMode_LoadBattle`,
`Window_Create`, `loc_2AA43C`, `loc_200000`, `Battle_SetupWindow`,
`loc_27DB92`, `Art_ChazField`, `VWFMenu_Alloc`) and asserts the block ends
at or below `$21A000`, so the next dialogue edit that crosses it fails the
build instead of the player's states.  `trpatch check --budget`'s two
"OVER" streams are the legacy compressed-path ceiling and exit 0.

The who-can-equip list's caption read `equip` (lowercase, a hand edit with
no record); it is `CAN EQUIP` as in script `01:002` and every other frame
caption.  Verified in play: Leather Shield's two-line Look, the caption.

`tools/checkbuild.py` (20 invariants) and all 13 tests pass.  Published
artifact: `work/ps4en_compose.bin`, SHA-256
`A1549307D4671DD9EA6A9C01C3DED612EE1FA2BB43337DA2231E5319B7CBC23C`.

## 2026-09-16: macro set/erase prompt letter

slot_8 (field MACRO, "s-MACRO will set up."): `Win_MacroSetupMsg` and
`Win_MacroEraseMsg` build the prompt in RAM with `$80+slot` as the letter,
the stock convention for "a letter from the $7C0 copy" (LoadWindowTiles adds
$C0).  The composer still honours that as window furniture, and in the field
$7C0-$7D9 are pool slots 88..113, so the cell showed whatever glyph was
composed there.  Both builders now write the charset code (`addi.b #1`,
same encoding size), so the whole run composes.  Also "will set up" ->
"will be set" (JP 設定します).  `test_paths.py` pins the builders' bytes.
Verified from the state: "E-MACRO will be erased. / Are you sure?".

The battle MACRO window's A-H stay stock fixed tiles on purpose: battle
never allocates past slot 88, and `VWFMenu_BankRestore` puts the stock
letters back at `$7C0` on every battle entry, so they have no side effects.

`tools/checkbuild.py` and all 13 tests pass.  Published artifact:
`work/ps4en_compose.bin`, SHA-256
`E6206E43C16F2C371BD6FDCC0AFF574E1C6CBBC9EAE821B8384D209EB496B090`.

## 2026-09-17: battle pool - MACRO browser, options labels, Defend box

Route from the report: battle start, MACRO, hover a few macros, cancel,
COMMAND, Tech/Skill -> refused cells.  Three separate leaks, all in the
"transient surface without a mark" class, each fixed with six-byte jsr
wrappers in the extension so no battle address moves:

* The macro preview (`loc_4E22`) composed the macro's five names on every
  hover and never rewound; PoolTop crept to 88 and `Battle_OpenCharComd`
  took its base on top of that.  `VWFMenu_BattleMacroMark` is taken when the
  letters window first opens; every preview redraw and both closes rewind
  to it.  Traced: hovering now oscillates 51/65/59/51 and returns to 51.
* A character's main options window composes `COMMAND/MACRO/RUN` (eleven
  slots) and closes before the command menu opens, but the base was taken
  after it, so every list in the battle carried eleven dead slots.
  `VWFMenu_BattleOptionsMark` is taken before the labels compose
  (`Battle_OpenMainOptions`) and `Battle_MainOptionSelected` rewinds to it.
  On the two-enemy state the base drops from 51 to 40 and the two-page
  Skill list fits (78 of 88) where page two used to read "Rec er".
* The Defend command's "DEFENSE" box (`loc_49AC`/`loc_4A40`) took no mark
  and never rewound: five slots per defending character, per turn, for the
  rest of the battle.  It now uses `VWFMenu_BattleActionMark` like the
  generic action box; a Defend-all turn returns PoolTop to 51 (was 56).

Note for states saved on earlier builds: a battle whose options window was
already open before this build keeps its labels below the base for the rest
of that battle; the fix applies from the next battle's first open.
`test_paths.py` checks all eight wrapper call sites.  `checkbuild.py` and
all 13 tests pass.  Published artifact: `work/ps4en_compose.bin`, SHA-256
`BA2ED969FE9946604C485AEC71F607C462566DBD4A584F69F4B5589E533CC5EE`.

## 2026-09-17: Alsulin -> Alshlin; release packaging

アルシュリン ships as `Alshlin` (was `Alsulin`; the user's call, keeping the
シュ).  Twelve sites: eleven dialogue lines and the `01:003` item name, which
feeds the menu, field and dialogue item-name tables.  Same length as the old
spelling, so the trees/examine/credits block below `$21A000` is untouched -
`Alshulin` was tried first and its extra byte crossed the align (the block
had 4 bytes of slack; it still does).  Moving the credits above `$300000` was
prototyped and then reverted at the user's request: nothing in the source
tree moved.

In the same build the `01:003` Alshline description went back to
`A secret medicine that turns a body of stone back to flesh.` -
`script_translated.json` had drifted to `An elixir that can turn ...` after
the 09-16 description pass while the published ROM kept the medicine; the
user chose the ROM's wording and the JSON now agrees with it.

The new ROM differs from the previous published build in exactly 16 bytes
(checksum, 11 dialogue bytes, 3 name-table bytes).  `checkbuild.py` and all
13 tests pass.  Shipping ROM: `ps4en_retranslation.bin` = `work/ps4en_compose.bin`
= `ps4disasm/ps4built.bin`, SHA-256
`01ED8D914539FCB82D3E28B62B9DDCFE8D72562DBFA1E2B987E5C4C59C7DE7F9`.

Distribution: `python tools/release.py <ver>` builds `release/PS4_Retranslation_v<ver>/`
(BPS via `flips/flips.exe`, offline `Patcher.html` that also takes/gives
`.smd`, readme rendered from `release/readme_template.txt`) and the zip.  The
stock US ROM is `work/ps4us_stock.bin` (CRC32 FE236442, identical to the
user's `P-STAR4.SMD` deinterleaved).  Note for the pipeline: `checkbuild.py`
reads the *previous* listing, so after a build that broke an anchor, assemble
once with `build.bat` before `sourcebuild.py` will pass again.

## 2026-09-18: v1.02 packaged

Built immediately before packaging from a clean tree: SHA-256
`1654688EEB2B06A58D6CF0FA68A41F32EC1D3689A620BB9F8CDC35F152414C96`,
CRC32 `1F69C8AD`; the tag reproduces it.  Changelog: "Chests which
contain meseta use a consistent numeric font. Status ailments are no
longer abbreviated on the Party screen."  The script reconciliation from
the v1.01 mismatch ships here too (three `Right!`, Shess's `Right! Leave
it all`).  `release/PS4_Retranslation_v1.02.zip`.

## 2026-09-18: whole status words on the party bar; v1.01 source mismatch

`PARA`/`POIS` are now `PARALYZED`/`POISONED`.  The party-bar field was the
five cells of `Level NN` (X+6..10, 40 px); PARALYZED is 46 px in the menu
face, POISONED exactly 40.  The pad cell before `Level` (X+5) is always
blank - the widest name that can carry an ailment, Shess, is 25 px (Forren
and Frena are androids, immune; a name would need 33 px to reach X+5) - so the
status field is now X+5..10 (48 px): `VWFMenu_StatusLevelClear` is six
blanks, the draw starts at X+5 (`addq.w #5,d0`, same size), and the words
live in the extension (`VWFMenu_ParalyzedStr`/`PoisonedStr`, own chrome-
table entry) so nothing in ps4.asm moves; the fixed build keeps the stock
strings.  The wipe is free: the normal `"     Level"` redraw emits blank
tiles through the pad cell, and `Win_CharStatsOverview_Main` is the only
consumer of the `$FFFFE3C0` status table.  Verified on Mark's
`compose10-para.state` (`work/status_words.png`: PARALYZED / POISONED /
DYING / POISONED on one bar; a cured reopen shows five clean `Level NN`).
`test_paths.py` checks the words, their widths against 48 px, the six-cell
clear and the X+5 draw.

Found on the way: the v1.01 tag does not reproduce the v1.01 ROM.  Mark's
`dialogue_full.json` was saved at 17:59, after the 17:36 build and before
the 19:31 commit, so the ROM carries only the "fruit of a thousand years
... unto the" edit while the tag's JSON also has six "Okay then!"-class
edits - and those overflow the `$21A000` anchor by 13 bytes (loc_200000
would move to `$21B000` and every field/battle address with it).  Resolved
with Mark: the three `Okay then!` and Shess's `All right then! Leave it
all` go back to `Right!`; `Okay! Then let's go`, `Y-yeah!` and the fruit
line stay.  Block now ends at `$219FFB`.  Lesson: always `sourcebuild`
immediately before `release.py`, and `checkbuild` reads the PREVIOUS
listing - a plain assemble is needed before `sourcebuild` after any build
that broke an anchor.  Also: `subprocess.run(['cmd','/c','build.bat'],
cwd=...)` does not run ("not recognized"); pass build.bat's full path.

Also: the money chest's "<n>00 meseta procured!" mixed faces - the
amount's digits come from `ConvertToDec3Digits` as the big fixed tiles
(`$9A`-`$A3`) while the literal `"00"` in `loc_2AAACA` went through the
window charset as the VWF `0`.  The two zeros are now `$9A, $9A`, so the
whole number is the fixed digits and only " meseta procured!" composes
(`test_paths.py` checks the bytes; emu68k confirms the head flushes as
tile `$7DA` and the tail composes).

`checkbuild.py` and all 13 tests pass.  `work/ps4en_compose.bin` SHA-256
`1654688EEB2B06A58D6CF0FA68A41F32EC1D3689A620BB9F8CDC35F152414C96`.

## 2026-09-18: enemy-name box after a mid-battle merge ("ND MACRO")

Mark's `slot_2.state` (now `work/compose9-metaslug.state`): two Zol Slugs
fused into a Meta Slug and its name box then showed the tail of `COMMAND`
and `MACRO`.  Replayed in the harness: every mid-battle enemy rebuild goes
through `loc_14D46`, which recomposes both group-name boxes while the
acting enemy's action-name window ("Fusion") is still open.  The new name
landed above `VWFMenu_BattleEnemyMark` (slots 22-26 over the mark at 18);
`loc_B59A` rewound to 18 when that window closed, and the next turn's
options labels took 18-29.  The state has exactly that layout.

Fix: `VWFMenu_BattleRebuildNames` (vwfmenu.asm), a six-byte jsr replacing
each of the two `jsr EnemyGroup_SetupNames` in `loc_14D46`, composes the
name and then lifts every battle mark (base, action, enemy, result, effect,
macro, options) that is nonzero and below the new PoolTop up to it - the
boxes live for the rest of the battle, so nothing may rewind under them
again.  The label open at the time stays pinned beneath (four cells, once
per battle: the merges are one-way).  No battle address moves; the state
replays on the new build.

Verified on each pair's own AI with `tools/enemy_rebuild_trace.py` (the
state's Meta Slug is forced to its split object and the spawned formation
rewritten to the pair; the party then only defends): the last two Zol
Slugs' Fusion -> Meta Slug, ArthroPod + Wiredine's Combine -> Life Deleter,
Blade Right + Haken Left's Combine -> Twin Arms.  In all three the rebuild's
slots are still the box's slots rounds later and the marks sit above them
(e.g. names 25-29, marks 30, labels 30-41).  The other two `loc_14D46`
callers (Sand Worm spawn, the Jr. Ooze split object) take the same path.
`test_paths.py` checks both wrapped call sites.  `checkbuild.py` and all
13 tests pass.  `work/ps4en_compose.bin` SHA-256
`7A90CB96DF6F0E7BB2D9DA407235F48EAAB5491363F06DE1C960E6B26A93FCE1`,
listing `work/ps4en_compose.lst`.

## 2026-09-18: repository packaged for release

`git init` at the project root; two commits.  `.gitignore` keeps every ROM,
build product, savestate (except the three BlastEm states and, in
`work/fixtures/`, the five Exodus states the tests replay), emulator and
Flips binary out; `.gitattributes` disables line-ending conversion because
the generators are byte-exact.  `README.md` is now the user guide (the dev
log moved to `docs/devlog.md`), `docs/pipeline.md` documents the build and
retargeting, `LICENSE` is MIT, `NOTICE.md` lists third-party terms.
`tools/export_mdtools.py` lifts the 20 game-independent tools into
`mdtools/` with a generated README and an isolation smoke test;
`tools/webpatch.py` renders the offline patcher for any BPS.  Fixed in
passing: `decomp.py` read one byte past a Nemesis blob that ends exactly
at the stream's end (7 of the 12 art blobs); `sourcebuild.py` assembles
once first when `ps4built.bin`/`ps4.lst` are missing.

Verified from a fresh clone: `sourcebuild.py` reproduces SHA-256
`01ED8D91...` byte for byte, all 13 tests pass, `git status` is clean after
a build, `export_mdtools.py` and `release.py` (bps.py fallback) both run.
Commit author is a placeholder noreply address until the user sets one.
