# Handoff: menu VWF — mixed-case face, composed chrome, fast window close

Written 2026-09-15 for whoever picks this up (Codex).  Everything here is
also in `work/STATUS.md` under the dated entries of 2026-09-14/15; this is
the short version with the open items first.

## Where things stand

Two builds, selected by two options in `ps4disasm/ps4.options.asm`:

| option | `ps4en.bin` (shipping) | `work/ps4en_compose.bin` (experimental) |
|---|---|---|
| `vwf_menu_hash` | 0 | 1 |
| `vwf_menu_chrome` | 0 | 1 |

- `ps4en.bin` == `work/ps4en_compose_stable.bin` (SHA-256 `D8372FE7…`),
  listing `ps4disasm/ps4.lst` after a default build, copy at
  `work/ps4en_compose_stable.lst`.
- `work/ps4en_compose.bin` (SHA-256 `AE278A9B…`) is the experimental one.
  Mark plays it from the BlastEm profile named `ps4en_compose`
  (`%LOCALAPPDATA%\blastem\ps4en_compose\`), which is where his saves and
  `slot_N.state` files live.  **Keep writing the experimental build to
  this filename.**  Its listing is `work/ps4en_compose.lst`; the harness
  (`tools/field_drive.py`) defaults to this ROM and listing.
- 13/13 `tools/test_*.py` pass on both builds.

Build either one with the flags set as above and:

    python tools/sourcebuild.py <output.bin>
    cp ps4disasm/ps4.lst work/<output>.lst     # the harness needs the matching listing

## What was done this session (2026-09-14 → 15)

1. **Mixed-case menu face** (`tools/vwfmixed.py`, emitted by
   `tools/menuvwf.py`; ships).  Stock vertical metrics: caps rows 0-6,
   x-height 2-6, 1-px descender, baseline 6.  Replaced the small caps.
   Evaluation page with switchable in-game mock-ups:
   https://claude.ai/artifact/VgJMZfZuiFLsbLEd7DWQPN
2. **Battle menus and flow messages compose** (ships): `VWFMENU_FLOW_LO/HI`
   in `ps4.constants.asm`; `COMD` → `ORDERS`, `MACR` → `MACRO`, vehicle
   `ATTAC/OPTIN` → `ATTACK/OPTION`, ` defeated...!` → ` was defeated...!`.
   The command menu's entries are 9 and 8 bytes (`lea 9(a0),a0` replaced
   `addq.w #7,a0` + a dead `clr.w d1`, same size).
3. **Field menu** (ships): 10 wide with fixed labels in `ps4en.bin`
   (`STATUS`, `MUMBLE`); back to 9 wide and composed in the experimental
   build.
4. **`vwf_menu_hash=1`** — hashed key lookup (128 buckets in `StripOf`,
   chains in `StripNext`, slot+1 encoding, `VWFMenu_IndexRebuild` on every
   `Mark`/`Release`) **plus** the real win: `VWFMenu_RemapRegion_Cell`
   tests for a marker before calling `RemapCell` (5,760 calls → 290).
   Window close went from 14-20 lag frames to 4-5.  Candidate to ship.
5. **`vwf_menu_chrome=1`** — the fixed-width labels compose.  Gate is a
   table, `VWFMenu_ChromeTable` in `ps4disasm/vwf/vwfmenu.asm` (lo, hi,
   kind).  Kind 1 = PAD rule: a space that starts a run, sits in a run, or
   precedes a colon/graphic/control advances to the next cell boundary; a
   lone space between glyphs is a word space; a colon is the stock tile
   from the `$7C0` copy (`$7F3`) in one cell.  `VWFMenu_DrawString_Pad`,
   `VWFMenu_PadMode`/`VWFMenu_PadRun` (RAM `+$B85`/`+$B86`).
   Converted: field menu, `Meseta`, `Level`, `Age`, the six attributes
   (`Strength   :` etc. — pads put the colon on the stock column), equip
   comparison labels, `Exp :`/`Next:`, every frame caption, title menu,
   SYS menu (`BATTLE SPEED`), speed selectors (`FAST`/`SLOW`), button
   window (`CANCEL`, six permutations generated from the face), save-slot
   rows, chest `DISCARD`/`RETURN`, `USE`/`LOOK`/`DISCARD`, `YES`/`NO`,
   shop `buy`/`sell`, field notices (six typewriter-mode sites swapped to
   `VWFField_LoadWindowTiles`, same size), `Victory!`/`Each got`/`EXP`/
   `meseta!`, battle item `Use`/`DSC`, and the level-up sequence:
   `<name>'s Level increased!`, `<attribute> increased by <n>!`,
   `Max HP increased by <n>!` (the results code's blank-skipping
   `lea 2(a1)`+`jsr loc_4640` pairs are `nop`s under the flag; the strings
   carry exactly the blank cells the value needs).  Windows widened by one:
   both meseta windows, chest decide, item action.
6. Tests: `tools/test_paths.py` models the pad rule with the composer's
   widths and asserts every colon/cursor/control lands on its stock
   column, every label ends before its numeric field, and the level-up
   blank counts.  `tools/emu68k.py` learned `eor.l`/`eor.b Dn,Dm`.

All ps4.asm changes for the experimental build are under
`if vwf_menu_chrome=1 … else … endif` with identical sizes, so no code
below `$300000` moves and savestates load on both builds.

## Open items, in the order Mark asked for them

1. **Glue mode** for `<name>'s Level increased!` (and ` retreated!` etc.):
   the message starts on the cell after the name's last cell, so up to
   7 px of gap can show between `Forren` and `'s`.  Fix sketch: have the
   composer remember the last run's end (`a1` after its last cell, the
   pixel remainder, the slot/key of that last cell) and, when the next
   `DrawString` starts at that `a1` with a flag or an apostrophe, seed the
   scratch with that cell's 1bpp (from `VWFMenu_Keys`), start the cursor at
   the remainder, and write the merged cell back at `a1-2`.  Not built.
2. **Class names** on the status screen (`ANDROID` etc., `CharNameData`
   region / segment `03:001`): still fixed and all caps; would need a
   range and probably title-casing in `work/script_translated.json`.
3. **Still fixed** (deliberately or not yet): `HP`/`TP` graphic pair
   (`$78 $79` / `$7A $79`), `2-HAND`, `DYIN`/`PARA`/`POIS`, title-screen
   slot summary (`Chaz:LV`, `M`, `NO DATA`), the debug CHECK WINDOW and map
   overlay labels (`loc_2AA65C..loc_2AA702`), `IPPO`, the NTSC boot notice,
   credits headers, and the **LOOK item description** (`InventoryDescriptions2`
   via `Win_ItemActionLook`) — that one is pool-bound: a typical LOOK
   screen would need ~95-100 slots against 88.  The lever is freeing the
   26 uppercase tiles of the `$7C0` font copy once *no* fixed uppercase
   label remains (digits stay).
4. **Not verified live**: the level-up window (no battle state here
   levels), `Cannot escape!`/`retreated` (the boss state never reaches a
   run attempt; the `giresta-*` states reset the driver).  Everything else
   above was screenshotted through the harness.
5. If the hash/remap optimisation is to ship, flip `vwf_menu_hash` to 1
   for `ps4en.bin` too; it is independent of the chrome flag.

## Working notes that cost time (also in Claude's memory files)

- `ps4disasm/build.bat` calls `pause` on an assembler error, which hangs
  a scripted build for its whole timeout and leaves `ps4built.bin` moved
  to `ps4built.prev.bin` (then `menustrip.py` fails).  Assemble first with
  `subprocess.run(['cmd','/c',build.bat], cwd=ps4disasm, stdin=DEVNULL,
  timeout=300)`, read `ps4disasm/ps4.log` (exists only on error), and
  restore `ps4built.bin` from `.prev` before `sourcebuild.py` if it failed.
  Short branches (`bcs.s`) around the gate chain and compose loop are the
  usual error when inserting code there.
- Harness: `python tools/field_drive.py work/field-slot0.state "B w20 B w20
  B w20 A*6 w30 C w30" --shots out/` — `A` opens the field menu, `B`
  closes, `S` opens the SYS menu whose first entry is SAVE: never script
  `C` blindly after `S`, the ROM's profile is Mark's real one.
  Screenshots need the BlastEm window visible (`tools/winshot.py`).
- A BlastEm state saved under an older font keeps old pool keys in RAM and
  old tiles in VRAM; redraws on it show hybrid glyphs until every window
  is closed and reopened.  Not a bug.
- `tools/blastem_screen.py state.state out.png` renders a state's planes
  without the emulator; the scratch mock-up tooling from the font
  evaluation is not in the repo (it lived in the session scratchpad).
- Three `blastem.exe` processes dated Sep 13 were running on the machine
  before this session and would not die to `taskkill`.
