# The build pipeline, and how to retarget it

This is the working reference for anyone changing text, fonts or engine code
in this repository. It describes what exists today; the reasoning behind each
decision is in [`devlog.md`](devlog.md) (search for the heading named here),
and the current state and checklist are in [`../work/STATUS.md`](../work/STATUS.md).

## 1. Shape of the build

There is no ROM patching. The game is assembled from source
(`ps4disasm/ps4.asm` and what it includes) by Macro Assembler AS, and the
translation reaches the source through **generators**: Python scripts that
read the two JSON files in `work/` and rewrite well-delimited regions of the
assembly, or emit binary tables the assembly `binclude`s. Running the build
twice with unchanged JSON produces the identical ROM.

```
work/dialogue_full.json ----treeport.py---------> ps4disasm/script/dialogue N.asm   (29 trees)
                        ----shoptext.py--------> shop / inn prompt block in ps4.asm
                        ----examinecredits.py--> "nothing here" + scenery examine block
work/script_translated.json
      00:001-004 names --menustrip.py---------> vwf/menunames.bin, menunameidx.bin, menustripmap.bin
                       --fieldstrings.py------> vwf/fielditemnames.bin, fieldtechnames.bin, fieldskillnames.bin
      00:005/006       --combonames.py--------> ComboNames / VehicleAttackNames in ps4.asm
      00:007           --guildnames.py--------> Hunters Guild job titles
      00:008           --spacemenu.py---------> spaceship destination menu
      01:003           --itemdesc.py----------> both item-description tables
      01:004           --soundtest.py---------> sound-test track titles
      02:001/002       --enemynames.py--------> enemy and enemy-skill names
      02:000, 03:000/001 party names and professions: applied once by
                       disasmport.py and kept in ps4.asm - edit there
work/dialogue_full.json ----spacenames.py-------> planet / space-travel banners (dlg02 rows)
                        ----titleport.py--------> attract-mode prologue (TitleText / TitleText2)
tools/vwfmixed.py       --menuvwf.py-----------> vwf/menufont.bin, menuwidth.bin (the menu face)
DiaFont.bin (stock art) --diavwf.py------------> vwf/diafont.bin, diawidth.bin, nibexp.bin
                        --menupool.py----------> vwf/poolslot.bin, pooltile.bin (slot<->tile maps)
                        --fixwinfont.py--------> the one extra glyph in the stock window font
```

`tools/sourcebuild.py` runs all of these in the right order, then
`checkbuild.py`, then the two budget checks (`trpatch.py check --budget`,
`trpatch8.py check`), then `build.bat`, and copies the 4 MB result to the
path you name. Every generator is idempotent and asserts its entry counts
against the assembled tables, so a JSON that has lost or gained a row fails
the build instead of shifting every following entry.

The `ps4.options.asm` flags select what gets assembled. The shipping
configuration is `bugfixes=1, optional_fixes=0, restore_unused_enemies=1,
dialogue_uncompressed=1, vwf_menu=1, vwf_menu_fixedlabels=1,
vwf_menu_strips=0, vwf_menu_hash=1, vwf_menu_chrome=1, vwf_measure=0`.
`sourcebuild.py` prints the ones that matter and refuses to run with the
source-build ones off.

## 2. The two JSON files

Both are lists of entries with the **original bytes** (`hex`, `raw_len`,
`offset`), the **Japanese** (`jp`), the **translation** (`en`), and for the
dialogue also the 1995 US text (`us`). Only `en` is ever edited; the
generators key on the original fields to find where each line goes.

**`work/dialogue_full.json`** - 2,170 messages in 29 streams. The `id` is
`<stream>#<index>` (`lz1CF6D6#0007`, `dlg01#0012`). Text markup:

| token | meaning |
|---|---|
| `{BR}` | line break (`$FC`) |
| `{ctl.FD}` | wait for a button, then clear the box |
| `{ctl.F4:nn}` | speaker portrait `nn` |
| `{ctl.F2:...}`, `{ctl.F9:..}`, `{ctl.FA:....}` | engine controls with operands - scripting, flags, branches |

The engine controls of a translated message must match the Japanese
message's, in order, with the same operands; `treeport.py` places the text
around them and `test_treeport_controls.py` fails the build on a mismatch.
Four rows carry a portrait the US tree has no slot for and are deliberately
skipped (they keep the US wording); `treeport.py` reports them.

**`work/script_translated.json`** - 865 entries in 17 segments, each a table
in the ROM's 8x8 text bank. Segments and their generators are in the diagram
above. Names are plain text; the item descriptions (`01:003`) may contain
one `{FC}` line break and must fit two lines in *two* faces, because the
same line is drawn by the menu engine (Item > Look, 192 px wide) and by the
dialogue engine (shop vendors, 255 px wide).

## 3. Budgets and hard limits

Everything here is enforced by a tool; this list says which one.

| limit | value | enforced by |
|---|---|---|
| dialogue line width | 255 px in the dialogue face | `trpatch.py check`, `dialogue_reflow.py`, `proofread.html` |
| menu name width | per window; the widest current name is the effective budget of its table | `menustrip.py`, `test_wrap.py` |
| item description | 2 lines; 192 px menu face and 255 px dialogue face per line | `trpatch8.py check`, `itemdesc.py` |
| status-screen party name | 4 cells | `menustrip.py` (`work/glossary.md`, "Status-menu name field") |
| decompressed dialogue stream | 8,192 bytes of RAM; the longest is 8,169 | legacy `trpatch.py check --budget` (its OVER lines refer to the retired compressed layout and exit 0) |
| **the `$21A000` align** | the dialogue trees, examine text and credits must end at or below `$21A000` | `checkbuild.py` |
| eight pinned code anchors | `loc_200000`, `Battle_SetupWindow`, `VWFMenu_Alloc`, ... must not move | `checkbuild.py` |

The `$21A000` one deserves a paragraph. Below it sit all 29 dialogue trees,
the examine text and the staff credits, followed by an `align $1000` before
`loc_200000`. If the text grows past `$21A000`, the align jumps to `$21B000`
and every battle routine after it moves by `$1000` - which breaks players'
savestates and every pinned anchor. `checkbuild.py` prints the remaining
slack; at the time of writing it is **4 bytes**. A text edit that adds bytes
must be paid for elsewhere in the block (a shorter line, a removed stray
space before `{BR}`), or the credits tables - reached only through
`lea (label).l` - can be moved above `$300000`, which was prototyped and
reverted on 2026-09-17 in favour of a same-length wording.

`checkbuild.py` reads the **previous** listing (`ps4.lst`), because it runs
before the assembler. After a build that tripped an anchor, run `build.bat`
once by itself before `sourcebuild.py` will pass again.

## 4. The text engines

The stock game has two text engines and this project made both proportional.

**Dialogue (`vwf/vwfdia.asm`, 278 lines).** The 8x16 dialogue font is
composed into a RAM buffer a glyph at a time by OR-ing 1bpp glyph rows onto
paper: the box is pre-filled with colour `$E` and ink is `$F`, so setting the
low bit turns paper into ink and no read-modify-write is needed
(`nibexp.bin` is the 256 x 8-shift expansion table that makes this a table
lookup). Widths come from `diawidth.bin`; `diavwf.py` derives both from the
stock `DiaFont.bin`, left-normalising each glyph. The narration and shop
text share this path.

**Menus (`vwf/vwfmenu.asm`, 3,337 lines).** Menu text is drawn into 8x8
cells from a fixed 4bpp bank, so a proportional face needs tiles that hold
*composed* pixel columns rather than single letters. The engine keeps a
**pool of tiles** (`VWFMENU_SLOTS = 146` in the field, `88` in battle where
the bank also holds sprite art) and composes each name into as many fresh
tiles as its pixel width needs, deduplicating identical 8-byte tile images
through a 32-bucket hash (`vwf_menu_hash`). Windows nest, so the pool is
managed as a stack of **marks**: opening a window records the pool top,
closing it rewinds. Cells that outlive their window (a name shown under a
newer window) are saved in a ledger of `VWFMENU_SAVEN` records keyed by
glyph content, not by tile, so recycling a tile cannot change what an
older window shows. `vwf_menu_chrome=1` also composes the fixed labels
(party names, Meseta, Level, attribute names).

Names come from `menunames.bin` (the translated text in the menu charset)
via `menunameidx.bin`; the ROM's own name tables keep the US text because
the game walks them by terminator and lays windows out from their lengths.
The face is `menufont.bin` + `menuwidth.bin`, generated from the glyph
definitions in `tools/vwfmixed.py`.

The constants (`VWFMENU_*` in `ps4.constants.asm`) are the tuning surface.
`checkbuild.py` asserts the RAM map has no overlaps, that every `moveq` of
one of them fits a byte (AS wraps silently), and that the pool's tile range
is disjoint from the glyphs chrome draws from.

## 5. Verification

```
python tools/checkbuild.py                      # 20 invariants, ~1 s
python tools/test_*.py                          # 13 tests; three replay BlastEm savestates
python tools/battle_drive.py work/pd-slot7.state --rounds 1     # pool and lag in a real battle
python tools/field_drive.py work/field-slot0.state "w30 R R L L B C"
```

The tests fall into two groups. Most run the assembled routines under
`tools/emu68k.py` against a real savestate's RAM (`menuharness.py`), with no
emulator process - fast, deterministic, and they fail loudly on any opcode or
flag the interpreter does not model. Three drive BlastEm through its GDB stub
(`blastem_drive.py`), replaying a savestate and reading RAM back; they need
`blastem-win32-0.6.2/` beside the repository and the three `.state` files
kept in `work/`.

After any change, diff the ROM against the previous build
(`work/STATUS.md` records each shipping build's SHA-256). A rename should
touch exactly the bytes you expect and nothing else; a shift of everything
after some address means an align moved.

## 6. Retargeting: another language

The pipeline is language-agnostic up to the fonts and charsets.

1. **Text.** Translate the `en` fields in both JSON files (the name is
   historical). Keep the engine controls of each dialogue message exactly.
   Use `tools/proofread.html` for width feedback; it draws with the real
   fonts.
2. **Menu face.** Add glyphs to `tools/vwfmixed.py`: `_g(char, top_row,
   *rows)` with `#`/`.` art, at most 8 rows and 8 columns. Then map the
   character to a code: the menu charset is `general/tables/wincharset.asm`
   (space 0, A-Z 1-26, 0-9 27-36, a-z 57-82, punctuation as listed in
   `menuvwf.py`); unused codes are free. `fixwinfont.py` shows how one extra
   glyph (u-diaeresis) was installed in a free slot of the stock window font
   for the fixed-width paths.
3. **Dialogue face.** `ps4disasm/general/art/uncompressed/DiaFont.bin` is 80
   glyphs x 16 bytes, 1bpp. Add glyphs (the file is plain tile art; `tiles.py`
   renders it for inspection), map them in `script/charset.asm`, and rerun
   `diavwf.py` so the widths follow. `english.py` has the slot table the
   dialogue encoder uses.
4. **Generators** need no change unless you add a token type. `treeport.py`
   encodes text through `dialogue.py`, so a new character must be in its
   table.
5. **Build, test, diff.** Expect the `$21A000` slack to be the first thing
   you hit if your language runs longer than English; see section 3.

## 7. Retargeting: another game

Only the generic layer transfers directly - see the `mdtools` export in the
README. The engines are written against this game's window system (its
window stack, its `$7C0` numeric bank, its DMA-from-RAM tile loading), and
the generators against its table layouts. What transfers as *method* is
documented in the devlog: composing into a tile pool with marks and a
content-keyed ledger is how you get a proportional menu font on a
fixed-tile renderer, and the emulator harness plus interpreter-backed tests
are how you find out whether it works without playing for ten minutes per
change.
