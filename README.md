# Phantasy Star IV: English Retranslation — source and tools

[![Latest release](https://img.shields.io/github/v/release/ExcalZ/ps4-retranslation?label=Download%20the%20patch)](https://github.com/ExcalZ/ps4-retranslation/releases/latest)

**Players:** get the patch from the [Releases page](https://github.com/ExcalZ/ps4-retranslation/releases/latest) — the zip has an offline patcher (`Patcher.html`), the BPS and the readme. Nothing else on this page is needed to play.

A new English translation of *Phantasy Star IV: The End of the Millennium*
(Mega Drive / Genesis), made from the Japanese script, built as a **source
patch on top of the game's disassembly** rather than by editing the ROM. Along
the way the game's text engine was rebuilt: proportional (variable-width) text
in the dialogue window and in every menu, with item, technique and skill names
drawn in full instead of truncated.

This repository holds everything needed to rebuild the patch from source and
to adapt the work to another language or another project:

* the translation itself, as editable JSON (`work/`);
* the two VWF engines and the tile-pool allocator behind the menu VWF
  (`ps4disasm/vwf/`), plus the edits to the disassembly that wire them in;
* the toolchain that writes the JSON into the assembly sources, generates the
  fonts and tables, checks budgets and invariants, assembles the ROM, tests it
  under an emulator and packages the release (`tools/`);
* a set of general Mega Drive utilities that do not depend on this game
  (BPS patcher, SMD conversion, Kosinski/Nemesis codecs, 68000 disassembler
  and interpreter, BlastEm harness, offline web patcher) — see
  [Generic tools](#generic-mega-drive-tools).

**Just want to play?** Download the [release zip](https://github.com/ExcalZ/ps4-retranslation/releases/latest)
(patch + offline patcher + readme); nothing in this repository is needed.
No ROM is included here or there.

## Repository map

```
README.md            this file
docs/pipeline.md     how a build works, what each stage reads and writes, how to
                     retarget the pipeline (another language, another text change)
docs/devlog.md       the development log: every measurement, dead end and
                     correction, in order (long; not an introduction)
work/STATUS.md       current state and the verification checklist - read this
                     before changing anything
work/glossary.md     translation conventions and every naming decision, with the
                     reasoning
work/dialogue_full.json      the dialogue script: 2,170 messages in 29 streams,
                             JP / EN / US side by side
work/script_translated.json  names, descriptions, banners, menus: 865 entries in
                             17 segments
ps4disasm/           the game's disassembly (lory90) with the translation applied
ps4disasm/vwf/       the VWF engines (vwf.asm, vwfdia.asm, vwfmenu.asm) and the
                     generated font/table binaries they include
tools/               the toolchain (Python 3, standard library only)
tools/proofread.html the proofreading editor - open it in a browser
release/             release templates: readme_template.txt, patcher_template.html
```

## Requirements

* **Windows** for the stock build: the assembler (`ps4disasm/AS/win32/asw.exe`,
  Macro Assembler AS) and `build.bat` are Windows binaries. Linux users can
  assemble with `ps4disasm/linux_build/` and `asl` from their distribution; the
  Python tooling itself is portable.
* **Python 3.10 or newer.** No packages to install.
* Optional: [BlastEm 0.6.2](https://www.retrodev.com/blastem/) unpacked as
  `blastem-win32-0.6.2/` in the repository root - it is git-ignored - (the
  emulator harness and three tests drive it through its GDB stub); [Flips](https://github.com/Alcaro/Flips)
  as `flips/flips.exe` (smaller patches; `tools/bps.py` is the fallback);
  BizHawk 2.11 for `tools/playtest.py`.
* To **package a release** you need the stock US ROM as a plain binary at
  `work/ps4us_stock.bin` (No-Intro *Phantasy Star IV (USA)*, 3,145,728 bytes,
  CRC32 `FE236442`). An interleaved `.smd` dump converts with
  `python tools/bin2smd.py your.smd work/ps4us_stock.bin`. Nothing else in
  the build needs a ROM.

## Building

```bash
python tools/sourcebuild.py ps4en_retranslation.bin
```

That runs the whole pipeline: every generator writes the JSON into
`ps4disasm/`, the fonts and tables are regenerated, `checkbuild.py` verifies
the invariants, the dialogue and name budgets are checked, the assembler runs,
and the 4 MB ROM is copied to the path you gave. A fresh clone assembles once
first to produce the listing the checks read. Then:

```bash
python tools/checkbuild.py
for t in tools/test_*.py; do python "$t"; done
```

`work/STATUS.md` lists the full verification set, including the two BlastEm
replays that measure pool usage and frame lag in real play.

## Editing the translation

Edit the `en` fields. Never the `hex`, `jp` or offsets - those describe the
original and are what the generators key on.

* **Dialogue** lives in `work/dialogue_full.json`. `{BR}` is a line break,
  `{ctl.FD}` a page wait, `{ctl.F4:nn}` a portrait; the control codes must
  match the Japanese message's (`test_treeport_controls.py` enforces it). A
  line may be up to 255 px in the dialogue face.
* **Names, descriptions, menus** live in `work/script_translated.json`, one
  segment per table (`00:001` items, `00:002` techniques, `00:003` skills,
  `00:004` places, `01:003` item descriptions, `02:001` enemies, ...).
  Names have no character limit but a pixel budget per window; descriptions
  must fit two lines in two different faces. The generators report anything
  that does not fit and the build refuses to ship it.
* `tools/proofread.html` shows every line in the real fonts with live pixel
  widths; load the JSON, edit, save it back over the file.

Then build, run the tests, and diff the ROM against the previous build - a
name change should touch exactly the bytes you expect. `docs/pipeline.md`
has the details, including the one hard address constraint (`$21A000`).

## Packaging a release

```bash
python tools/release.py 1.0
```

writes `release/PS4_Retranslation_v1.0/` - the BPS patch, `Patcher.html`
(an offline, single-file web patcher that also accepts and produces `.smd`)
and the readme rendered from `release/readme_template.txt` with every hash
filled in from the actual files - and zips it. It refuses to package a ROM
that differs from the last assembly, or a patch that does not re-apply to a
byte-exact copy.

## Generic Mega Drive tools

Part of `tools/` has nothing to do with this game and is kept
self-contained so it can be lifted into other projects:

| Tool | What it does |
|---|---|
| `bps.py` | BPS patch create / apply / info, pure Python, with an encoder that finds moved data |
| `smd.py`, `bin2smd.py` | interleaved `.smd` <-> plain binary |
| `expand.py` | grow a ROM to the 4 MB cartridge window, fix header end address and checksum |
| `kosinski.py`, `kosdec.py` | Kosinski decompression (and a validator for compressors) |
| `decomp.py`, `nemcmp.py` | Nemesis decompressor and compressor |
| `lzss.py`, `lzss_enc.py` | the LZSS variant Phantasy Star IV uses for its script |
| `m68k.py` | a compact 68000 disassembler |
| `emu68k.py` | a 68000 interpreter, for executing a routine against a memory image without an emulator |
| `png.py`, `pngread.py`, `tiles.py` | dependency-free PNG writer/reader; render 1bpp/4bpp tile data |
| `blastem_drive.py` | drive BlastEm from Python through its GDB remote stub: breakpoints, RAM read/write, pad injection, frame stepping |
| `blastem_ram.py`, `blastem_screen.py` | pull work RAM out of a BlastEm savestate; render its VDP planes to PNG |
| `webpatch.py` + `release/patcher_template.html` | render a single-file offline HTML patcher for any BPS |

```bash
python tools/export_mdtools.py
```

copies exactly that subset into `mdtools/` with its own README and license,
and verifies the copy imports and runs on its own. `docs/pipeline.md`
describes which of them the PS4 build actually uses and where.

## Adapting this to another language

The pipeline is language-agnostic up to the fonts. In outline: translate the
`en` fields (the field name is historical), add any glyphs your language needs
to `tools/vwfmixed.py` (menu face, 8x8 cells) and to the 8x16 dialogue font
(`ps4disasm/general/art/uncompressed/DiaFont.bin` + `tools/diavwf.py`), map
them in the two charsets, and build. The German patch's experience - the
stock fonts have no umlauts - is exactly the case this handles. See
`docs/pipeline.md`, "Retargeting".

## Credits and legal

Translation, hacking and testing by **Excalibur_Z**, with Claude (Anthropic)
for translation and technical work. Built on lory90's Phantasy Star IV
disassembly and its bug-fix patch. Tooling, engines and documentation are
MIT licensed (`LICENSE`); third-party components and their terms are listed in
`NOTICE.md`. Phantasy Star IV is copyright SEGA; this repository contains no
ROM image and no right to one.

Contact: Discord `@Excalibur_Z`, Twitter `@ExcalZGaming`.
