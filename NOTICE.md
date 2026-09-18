# Third-party components

| Component | Where | Origin | Terms |
|---|---|---|---|
| Phantasy Star IV disassembly (`ps4disasm/`) | the whole directory, minus `vwf/` and the translation edits | lory90's `ps4disasm` (the original GitHub repository is gone; `squidfeatures/ps4disasm` mirrors it and still assembles the stock US ROM bit-exact with every option at 0) | Its author's disclaimer, reproduced below. No formal license. Non-commercial. |
| Bug fixes in the disassembly (`bugfixes = 1`) | `ps4disasm/ps4.asm` | same project, "Phantasy Star IV Bugfix" | as above |
| Macro Assembler AS (`ps4disasm/AS/win32/asw.exe`, `p2bin.exe`) | `ps4disasm/AS/` | Alfred Arnold, http://john.ccac.rwth-aachen.de:8000/as/ | AS's own free-software license; the message catalogues and DLLs beside it are part of that distribution |
| `ps4p2bin`, `fixheader.exe` | `ps4disasm/` | ship with the disassembly | as the disassembly |
| Linux build script (`ps4disasm/linux_build/`) | that directory | Ilja Sara, `mdps-asm-builder` | BSD 3-Clause (see its `LICENSE`) |
| creep typeface glyphs | `tools/creepfont.py` | romeovs, https://github.com/romeovs/creep | MIT; the notice is in the file. Not used by the shipping build. |
| BPS format | `tools/bps.py` | byuu's beat format, reimplemented from the public specification | - |
| Kosinski / Nemesis / LZSS codecs | `tools/kosinski.py`, `tools/decomp.py`, `tools/nemcmp.py`, `tools/lzss*.py` | reimplemented from the game's own routines | MIT (this repository) |

Not included, but used by the build and test tooling - install them yourself:

* **BlastEm 0.6.2** (GPL) - `tools/blastem_drive.py` expects `blastem-win32-0.6.2/blastem.exe` beside the repository.
* **Floating IPS (Flips)** (GPL) - `tools/release.py` uses `flips/flips.exe` when present and falls back to `tools/bps.py`.
* **BizHawk 2.11** - `tools/playtest.py` looks for `EmuHawk.exe`.
* **Exodus 2.1** - some measurement scripts read its savestates.

## Disassembly disclaimer

> DISCLAIMER: Any and all content presented in this repository is presented for
> informational and educational purposes only. Commercial usage is expressly
> prohibited. I do not claim ownership of any code in this repository. You
> assume any and all responsibility for using this content responsibly. I do
> not claim responsibility or warranty.

Phantasy Star IV: The End of the Millennium is copyright SEGA. This repository
contains no ROM image; see `README.md` for how to obtain the one the patch
applies to.
