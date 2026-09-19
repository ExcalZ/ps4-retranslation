================================================================================

  PHANTASY STAR IV: THE END OF THE MILLENNIUM
  English Retranslation

  Version @VERSION@
  Release Date: @DATE@

  Author: Excalibur_Z
  Platform: Sega Genesis / Mega Drive

================================================================================


--------------------------------------------------------------------------------
  1. ABOUT THIS PATCH
--------------------------------------------------------------------------------

This patch is a new English translation of Phantasy Star IV: The End of the
Millennium, made from the Japanese script rather than from the 1995 US
localization. It is an unofficial fan project and is not affiliated with or
endorsed by SEGA.

The 1995 release was a good localization for its day, but it was written
into a menu system that cut technique names to about five letters and a
dialogue window that could hold very little text per page. A great deal of
the original writing was compressed, paraphrased or dropped to fit. This
patch rebuilds the text engine so that the game can carry a translation of
the Japanese script in full.

  WHAT IS TRANSLATED

  Dialogue ............ all of it, translated anew from the Japanese
  Narration ........... opening prologue and story narration
  Examine / shop text . translated
  Item descriptions ... translated
  Location banners .... translated
  Menus / system text . retranslated where the Japanese differs
  Staff credits ....... left exactly as the US release has them

  NAMES

Names follow the Japanese game. Where SEGA has since printed an official
English spelling for a Japanese name (in later Phantasy Star titles or in
Japanese-side material), that spelling is used; otherwise the katakana is
transliterated directly, with the word's origin settling any ambiguous
letters. Some of the changes players will notice first:

  Party:       Chaz -> Rudy          Alys -> Laila Brangwen
               Rika -> Fal           Wren -> Forren
               Demi -> Frena         Gryz -> Pyke
               Kyra -> Shess         Seth -> Thray
               Hahn, Rune, Raja and Zio keep their names.

  Techniques:  Foi/Gifoi/Nafoi -> Foie/Gifoie/Rafoie
               Wat/Giwat/Nawat -> Barta/Gibarta/Rabarta
               Gra/Nagra/Gigra -> Grants/Gigrants/Ragrants
               Rever -> Reverser, Ryuka -> Ryuker, Gelun -> Jellen,
               Res -> Resta, and so on. Megid, Hinas and Zan are as
               before. Nothing is truncated any more.

  Items and enemies follow the same rule (Alshline -> Alshlin,
  Perolymate -> PelorieMate, Lassic -> LaSheek, ...). Long-established
  series terms keep their familiar spelling where the Japanese supports it:
  Algol, Motavia, Dezolis, meseta, Laconia, Elsydeon.

  WHAT CHANGED UNDER THE HOOD

  - Proportional (variable-width) text in the dialogue window, so lines
    hold far more text and read as ordinary mixed-case English.
  - Proportional, mixed-case text in the menus. Item, technique and skill
    names are composed on the fly from their full spelling instead of
    being drawn from fixed 5- or 8-character slots, so no name is cut
    short anywhere: field menus, shops, battle, status and equip screens.
  - The dialogue script is stored uncompressed, and the new name tables
    live above the original 3 MB, which is why the ROM grows to 4 MB
    (see section 4).
  - The bug fixes from the Phantasy Star IV disassembly project are
    included: the level 99 bugs, stats not updating on level-up, the
    shield element carrying over to weapons, the Zelan/Rykros event-flag
    skip, the Aiedo NPC softlock, the frame-perfect Cancel corruption in
    several windows, vehicles taking 1 damage, the simultaneous left+right
    crash, and the rest of that patch's list. Four of its balance-type
    changes are deliberately NOT included, so the game plays as SEGA
    shipped it in those respects: Igglanova status immunities, Psy-Robe
    psychic protection, Raja being unable to equip the Psycho Wand, and
    the reduced Shadow Blade stat penalty.
  - The two enemies left unused in the original game (Acacia and Shadow
    Mirage) are restored to their encounter tables.

  HOW IT WAS MADE

This translation was produced by a single author working with the AI
assistant Claude (Anthropic), which was used both for the translation from
Japanese and as technical support for script extraction, the disassembly
work, the variable-width font engines and the tooling around them. Every
line of the translation was reviewed by the author. The build was
exercised in an emulator through a library of saved states covering field,
shop, battle, status and equipment screens across the game, backed by
automated regression tests over the menu engine.


--------------------------------------------------------------------------------
  2. REQUIRED ROM
--------------------------------------------------------------------------------

  Game:          Phantasy Star IV - The End of the Millennium (USA)
  Region code:   4  (USA)
  Serial:        GM MK-1307 -00
  Copyright:     (C)SEGA 1994.NOV
  Size:          @SRC_SIZE@ bytes  (3 MB / 24 Mbit)
  Header:        none - plain headerless .bin / .md / .gen dump

  CRC32:         @SRC_CRC32@
  MD5:           @SRC_MD5@
  SHA-1:         @SRC_SHA1@

The patch applies to this exact ROM only. If your file has a different
size or checksum, the patching tool will refuse it. Interleaved .smd dumps
(3,146,240 bytes, with a 512-byte header) contain the same ROM in a
different byte order; Patcher.html handles them directly, other patchers
need a plain binary.

No ROM is included with this patch and none will be provided. You must
supply your own copy of the game.


--------------------------------------------------------------------------------
  3. HOW TO PATCH
--------------------------------------------------------------------------------

  EASIEST WAY: Patcher.html

    1. Open Patcher.html from this archive in any web browser.
       It works offline; nothing is uploaded anywhere.
    2. Drop your Phantasy Star IV (USA) ROM onto the page, or click to
       choose it. Plain .bin / .md / .gen dumps AND interleaved .smd
       dumps are accepted - .smd files are converted automatically.
    3. The page checks that your ROM is the right one, applies the
       patch and offers the result for saving - as a plain .bin or as
       an interleaved .smd, whichever your emulator or flash cart
       expects. Both hold the same game. Never overwrite your original
       ROM.

  WITH A CONVENTIONAL PATCHER

  Patch format:  BPS
  Patch file:    @PATCH@

  Recommended tool: Floating IPS (Flips)
                    https://www.romhacking.net/utilities/1040/

    1. Open Flips and choose "Apply Patch".
    2. Select @PATCH@ from this archive.
    3. Select your unmodified Phantasy Star IV (USA) ROM as a plain
       binary (.bin / .md / .gen). Flips cannot convert .smd files -
       use Patcher.html for those.
    4. Save the result under a new file name.

  Alternatively, use an online BPS patcher such as the one on
  ROMhacking.net.

  BPS patches store a checksum of the source ROM. If the tool reports a
  mismatch, your ROM is not the expected version - see section 2.


--------------------------------------------------------------------------------
  4. VERIFYING THE RESULT
--------------------------------------------------------------------------------

  After patching, the file should match these values:

  Plain binary (.bin / .md / .gen):
  Size:          @OUT_SIZE@ bytes  (4 MB / 32 Mbit)
  CRC32:         @OUT_CRC32@
  MD5:           @OUT_MD5@
  SHA-1:         @OUT_SHA1@

  Interleaved .smd, as saved by Patcher.html:
  Size:          @SMD_SIZE@ bytes
  CRC32:         @SMD_CRC32@
  MD5:           @SMD_MD5@
  SHA-1:         @SMD_SHA1@

  A 4 MB .smd is unusual - the format's header only counts up to 255
  blocks of 16 KB, and this image has 256 - but emulators size the data
  from the file length, not the header. BlastEm and Genesis Plus GX
  (BizHawk) were both confirmed to load the .smd correctly. If yours does
  not, save the .bin instead.

  The patched ROM is 4 MB, one megabyte larger than the original. The
  Genesis maps cartridge ROM across the whole 4 MB window, so no mapper or
  bank switching is involved; the ROM end address in the header is set to
  @ROMEND@ accordingly.

  The internal Genesis checksum has been recalculated and is valid
  (@MDCHK@), so the patched ROM passes the console's own integrity check.

  The SRAM configuration is unchanged (8 KB at 0x200001-0x203FFF), so
  battery saves work exactly as in the original game.


--------------------------------------------------------------------------------
  5. TESTED ON
--------------------------------------------------------------------------------

  Emulator:      BlastEm 0.6.2  (primary)
                 Exodus 2.1 and BizHawk 2.11 (Genesis Plus GX core) were
                 also used during development.

  This release has not been tested on real hardware. The image is a plain
  4 MB binary with the game's original SRAM mapping, which flash carts
  that support Phantasy Star IV should accept, but this is unverified.
  Reports from EverDrive / Mega SG / Mega Everdrive owners are welcome.


--------------------------------------------------------------------------------
  6. KNOWN ISSUES
--------------------------------------------------------------------------------

  - Four dialogue messages (out of roughly 2,170) still show the 1995 US
    wording. Their control codes could not be matched between the two
    scripts automatically and they were left alone rather than guessed at.
    They will be addressed in a future version.

  - The menu text engine draws letters from a shared pool of tiles. Very
    long play sessions late in the game with large inventories have had
    less testing than the earlier game; if you ever see wrong or garbled
    letters in a menu, please report it (see section 9) with the emulator
    savestate and a note of which menus you had open.

  Please report text bugs with a savestate or a description of where the
  passage appears.


--------------------------------------------------------------------------------
  7. CREDITS
--------------------------------------------------------------------------------

  Translation, hacking, testing ......... Excalibur_Z
  Translation and technical support ..... Claude (Anthropic)

  Built on the Phantasy Star IV disassembly (ps4disasm) and its bug-fix
  patch by lory90, without which none of the engine work would have
  been practical. The bug fixes listed in section 1 are that project's.

  Tools ................................. AS macro assembler,
                                          BlastEm, Exodus, BizHawk,
                                          custom Python tooling

  The original SEGA staff credits are preserved in full. No developer
  has been removed from or replaced in the in-game credit roll.

  Thanks to the ROMhacking.net community for the documentation and
  utilities that made this project possible.


--------------------------------------------------------------------------------
  8. LEGAL
--------------------------------------------------------------------------------

  Phantasy Star IV: The End of the Millennium is copyright SEGA.
  This is an unofficial, non-commercial fan translation distributed as a
  patch file only. It contains no copyrighted game data.

  The patch may be freely redistributed as long as this readme is
  included and no fee is charged. Do not distribute pre-patched ROMs.


--------------------------------------------------------------------------------
  9. CONTACT
--------------------------------------------------------------------------------

  Discord ........... @Excalibur_Z
  Twitter ........... @ExcalZGaming


--------------------------------------------------------------------------------
  10. CHANGELOG
--------------------------------------------------------------------------------

  v@VERSION@  -  @DATE@  -  Fixed an instance of tile recycling for enemies
                             that summon, combine, or split.
  v1.0   -  18.09.2026  -  Initial release


================================================================================
