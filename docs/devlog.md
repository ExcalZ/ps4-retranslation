# Development log

This is the project's working notebook, kept in the order the work happened:
every dead end, retraction and measurement. It is long because it was written
to be re-read by the person doing the next session, not to introduce the
project. For that, start at [`../README.md`](../README.md) and
[`pipeline.md`](pipeline.md); the current handoff state is in
[`../work/STATUS.md`](../work/STATUS.md).

Two things to know when reading it: early sections target the **Japanese**
ROM and a patch-the-binary pipeline that has since been retired (see
"Should the work move to the US ROM?"); and later sections correct earlier
ones - a claim is only as good as the last section that mentions it.

---

# Phantasy Star IV (ps4japa.smd) — translation toolchain

A format-preserving extract → edit → reinsert pipeline for the Japanese
Mega Drive ROM, plus a proofreading editor.

## Status

| Piece | State |
|---|---|
| SMD ↔ raw BIN codec | **Done**, byte-exact round-trip verified |
| 68k disassembler | **Done**, validated against the reset vector |
| Text addressing model | **Solved** — no pointer table, see below |
| Extractor / reinserter | **Done**, variable-length, round-trip verified |
| Proofreading tool | **Done**, live per-segment budgets |
| Character table (byte → glyph) | **Not resolved** — font is compressed |
| Remaining ~99% of script | **Not reachable** — compressed |

## Layout

```
tools/
  smd.py          SMD <-> BIN (512-byte header, 16 KiB odd/even deinterleave)
  m68k.py         68000 disassembler
  table.py        byte <-> text table, loads ps4.tbl
  ps4.tbl         the table itself — edit this, no code changes needed
  script_io.py    extract / reinsert, segment-aware repacking
  ps4tool.py      CLI driver
  png.py tiles.py tile renderers used for font hunting
  proofread.html  the proofreading editor (open directly in a browser)
work/
  original.smd    your ROM, untouched
  rom.bin         deinterleaved
  script.json     extracted script
```

## Use

### Current English source build

The current `ps4disasm` configuration assembles uncompressed dialogue, both
VWF renderers, fonts, narration, and prerendered menu strips directly. Build it
from the translation JSONs with:

```bash
python tools/sourcebuild.py ps4en.bin
```

Do not run the older JP-ROM relocation/font patches over `ps4built.bin`; their
absolute addresses overlap live source-build code and title assets. For
compatibility, `ps4tool.py en-build ... --source-build` now performs a safe
copy only. `sourcebuild.py` is the JSON-to-ROM path.

### Packaging a release

```bash
python tools/release.py 1.0
```

Writes `release/PS4_Retranslation_v1.0/` (BPS patch, `Patcher.html`, rendered
`readme.txt`) and the matching `.zip`. The patch is made with `flips/flips.exe`
when present (smaller) and otherwise by `tools/bps.py`, a self-contained BPS
encoder/decoder that in either case re-applies the result; the script refuses
to package unless that reproduces the ROM byte for byte, and unless
`ps4en_retranslation.bin` matches `ps4disasm/ps4built.bin`. `Patcher.html`
(from `release/patcher_template.html`, patch embedded as base64) is a
single-file offline patcher that also accepts interleaved `.smd` dumps - a BPS
sourced from an `.smd` is either 2.5 MB or emits a 4 MB `.smd` with an
overflowed header, so the conversion is done in the browser instead; it can
also save the result re-interleaved as `.smd`, which BlastEm and BizHawk's
Genesis Plus GX both load correctly despite the 256-block count. The source is the stock US ROM at
`work/ps4us_stock.bin` (No-Intro CRC32 `FE236442`; identical to the
deinterleaved `P-STAR4.SMD`, and to the upstream disassembly built with every
option at 0 - the `squidfeatures/ps4disasm` mirror still assembles it).
The readme text lives in `release/readme_template.txt`; hashes, sizes and the
date are `@TOKENS@` filled from the files, so edit the template, never the
rendered copy.

```bash
python tools/ps4tool.py extract work/original.smd work/script.json
```

Open `tools/proofread.html`, load `work/script.json` and `tools/ps4.tbl`,
edit, save back over `script.json`. Then:

```bash
python tools/ps4tool.py check work/script.json
```

```bash
python tools/ps4tool.py insert work/original.smd work/script.json work/patched.smd
```

`insert` recomputes the Mega Drive checksum and re-interleaves to SMD
automatically. Output format follows the output filename extension.

## The addressing model (this is the important part)

**There is no pointer table for this text.** The canonical lookup lives at
`$05CCB6` and is reached from 22 call sites:

```
05CCB6  move.l  d1,-(a7)
05CCB8  move.w  #$FE,d1
05CCBC  andi.w  #$FF,d0        ; message index
05CCC0  beq     done           ; index 0 -> base unchanged
05CCC2  cmp.b   (a0)+,d1       ; scan forward to the next $FE
05CCC4  bne     05CCC2
05CCC6  subq.w  #1,d0
05CCC8  bne     05CCC2
05CCCA  done: move.l (a7)+,d1
05CCCC  rts
```

The caller passes a base in `a0` and an index in `d0`; the routine just counts
`$FE` terminators. Two inline copies at `$001FC0` and `$003CC0` do the same
with a hardcoded `adda.w #$2DD,a0` for indices ≥ `$50`, and a dispatcher at
`$28081E` selects between three different bases.

Scanning the ROM for 32-bit values landing inside the block yields **12
distinct hardcoded entry points**, which `script_io.ANCHORS` records.

Two consequences:

1. **Messages can be resized freely.** A message's position is defined only by
   how many terminators precede it, so nothing needs repointing — the earlier
   in-place-only restriction was wrong and has been removed.
2. **Budgets are per segment, not per message.** The span between two anchors
   must keep its byte count and its terminator count. Shortening one message
   frees space for its neighbours in the same segment.

The segment map, from `ps4tool.py check`:

```
 seg            range  msgs   used    cap   free
   0 2ABF00-2AC006    29    257    262      5
   3 2AC02B-2AC1DD    46    432    434      2
   4 2AC1DD-2AC210     5     51     51      0
  11 2AC5D6-2AC780    54    426    426      0
  12 2AC780-2AC900    52    377    384      7
```

Segments 4, 10 and 11 have exactly zero slack — data is packed right up
against the next hardcoded base. That is strong independent evidence the
anchor list is correct.

## Verified behaviour

- Extract → reinsert with no edits reproduces the ROM **byte-for-byte**.
- Resizing messages preserves every segment's terminator count (checked
  per segment), and touches nothing outside the block except the checksum.
- The reinserter never copies live message bytes into padding — a stray
  `$FE` there would shift every later message index.

## Accuracy audit (corrections)

An error spotted in the output — a spell name decoding with the wrong small
kana — turned out to be the thread that unravelled four separate bugs. All are
fixed; recording them because three were silent.

1. **The katakana bank omits ヘ and ヲ.** It runs ア..フ contiguously
   (`$32-$4D`), then ホ `$4E`, マ `$4F`, ミムメモヤユヨ `$50-$56`,
   ラリルレロワン `$57-$5D`, small kana `$5E-$65`.

   ヘ is missing because katakana ヘ and hiragana へ are indistinguishable at
   8x8, so the font ships a single tile (`$1D`) and the game spells katakana
   ヘ with the hiragana code — ヘルメット is stored that way, and there are 17
   sites where `$1D` is directly followed by a katakana. That one omission
   accounts for the whole downstream offset.

   It also explains a detail that had looked odd: `$4E` carries a dakuten mark
   in 13 of its 14 occurrences. As ホ that is simply ボ, which is common; as ヘ
   it would have been ベ, which is not.

   Every reading taken off the font image in this range was wrong. The layout
   was recovered from the ROM instead, using loanwords whose spelling is
   forced:

   | evidence | fixes |
   |---|---|
   | ラコニア (Laconia), クロー, スライサー | `$57`=ラ, `$5B`=ロ |
   | チタニウム (titanium) | `$51`=ム |
   | セラミック (ceramic) | `$50`=ミ |
   | ブーメラン, メイル | `$52`=メ |
   | アーマー, マント | `$4F`=マ, so ホ is the absent glyph |

   Reading 8x8 kana off a screenshot proved unreliable three separate times.
   Byte-level evidence should be preferred wherever it exists.

2. **`$F0`/`$F1` were treated as two-byte prefixes.** They are standalone
   combining marks, so voiced kana rendered as `{F038}` instead of ギ. They now
   compose on decode and split on encode.

3. **A range test admitted impossible bases.** Unicode interleaves は ば ぱ ひ
   び ぴ, so `'は' <= c <= 'ほ'` accepted べ as a base and decomposed ぺ into a
   character with no tile. Replaced with explicit base sets.

4. **Two digit banks both mapped to ASCII 0-9.** `$A4` decoded as `0` but
   re-encoded as `$9A` — a silent corruption on any edited line. The second
   bank is now fullwidth `０-９`.

**Six of the eight "confirmed" text regions were 68k code.** They had been
accepted because executable code points at them, but a pointer proves a region
is *addressed*, not that it holds text. Three independent checks reject them —
68k opcode density, popcount share, and above all dakuten density: `047E83`
and `04A637` hold 6 KB between them without a single voiced kana, which cannot
occur in Japanese prose. Disassembly confirms it.

Note that byte round-trip is **not** a usable discriminator here — unmapped
bytes survive as `{XX}` escapes, so code regions round-trip perfectly too.

Corrected totals: **2 regions, 519 messages, 6813 bytes, 96.4% mapped,
519/519 decode->encode identity.**

## Text regions (superseded - see audit above)

The original scan found only 2.5 KB of text because it required the narrow
alphabet of the item block (`$00–$65`). The renderer actually accepts
`$00–$EF`, and dialogue uses the upper range heavily — roughly 75% low bytes
(kana) to 11% high bytes (kanji), plus control codes `$F2`–`$FD`.

Rescanning with the renderer's real constraints — no `$FF`, `$FE` at
text-like intervals, mixed low/high distribution — finds **16.6 KB across 8
regions**, every one confirmed by hardcoded pointers from executable code:

```
        region  anchors  msgs   bytes
047E83-048D3A       105    34    3767   fixed 16-byte stride
04A637-04AFE0       151    47    2473   fixed 16-byte stride
071BE0-071E50         7    13     624
1FF141-1FF3BB         5    28     634
2AB0C4-2AB3EA        16    11     806
2AB988-2ABC9B        59    57     787
2ABEFF-2AC911         8   308    2578   the original item block
2ADF23-2AF268        15   211    4933   dialogue-length, avg 23 B
```

A ninth region at `0x18D360` matches the text profile but has **no** code
references, so its boundaries are unverified and it is deliberately excluded.

Two addressing styles show up, and `regions.py` handles both with one
mechanism. In `047E83` the anchors sit exactly `$10` apart — those are
fixed-width 16-byte records, each individually pointed at. `2AB988`'s anchors
are irregular, so those entries are variable length. Treating every
code-referenced address as a fixed anchor covers both cases: a fixed-stride
region simply yields 16-byte segments, which enforces the record width for
free.

## Blocker: the bulk of the script is still compressed

### The 8 regions are the complete uncompressed set

Worth stating because it bounds the search. Relaxing the scan (allowing
sparse `$FF`, window-based rather than maximal runs) surfaces ~112 KB of
candidate regions, including a tempting 40 KB block at `0x1F6000` with
apparently consistent ~25-byte message spacing.

It is not text. Its byte histogram is dominated by `00 20 10 08 04 40 01 02`
— single-bit values — and 46% of its bytes have popcount ≤ 1, against 2–17%
for confirmed text. It is bitmap data; `$FE` simply recurs at a roughly
geometric spacing in any dense stream, which fakes the message rhythm.

Three properties separate real text from dense binary, calibrated on the
confirmed regions:

| | items | dialogue | names | bitmap false positive |
|---|---|---|---|---|
| popcount ≤ 1 | 2% | 17% | 23% | **46%** |
| distinct bytes | 96 | 148 | 92 | **250** |
| control codes `$F0`–`$FD` used | 2 | 4 | 3 | **14** |

The last one is the sharpest: genuine text reuses a handful of control codes,
while dense binary hits every value in the range. Screening every candidate
in the ROM on all three, plus requiring an anchor density under one per
600 bytes, returns **no regions beyond the eight already listed**.

So 16.6 KB is far short of a full RPG script, and most dialogue is packed.
It is **not** packed with the graphics codec: partially decoding 49,057 valid
blobs at every even offset in the ROM and testing each against the script
alphabet returns **zero** matches. That is expected in hindsight — the codec
models 4bpp nibble runs, which is a poor fit for text.

So a second, text-specific codec exists and has not been found yet. An
entropy map shows the ROM is overwhelmingly high-entropy (H > 7.4 across most
banks), and the font lives in that same unexplored space.

That has a concrete consequence for the table: mapping bytes to glyphs
normally means rendering the font tiles and reading the character order off
the image. 1bpp and 4bpp renders at 8×8 and 16×16 across every low-entropy
island produced no font — it is compressed too. So `ps4.tbl` declares only
the `$FE` terminator and the extractor emits `{4B}`-style raw escapes.

Reaching the bulk of the script means finding and reversing the decompressor,
then writing a matching compressor for the write path. The disassembler is now
in place for that work, but it is a substantial project in its own right.

## Encoding notes

The renderer at `$280564` settles the encoding:

```
280568  moveq   #0,d2
28056A  move.b  (a0)+,d2        ; character byte
28056C  bpl     $280586         ; < $80
28056E  cmpi.b  #$FE,d2
280572  bcc     $280590         ; >= $FE -> end of message
280574  cmpi.b  #$F0,d2
280578  beq     $2805A0         ; dakuten
28057A  cmpi.b  #$F1,d2
28057E  beq     $2805BC         ; handakuten
280580  addi.w  #$740,d2        ; $80..$EF -> tile $740 + byte
280584  bra     $28058A
280586  addi.w  #$680,d2        ; < $80    -> tile $680 + byte
28058A  add.w   d0,d2           ; + palette/priority attribute
28058C  move.w  d2,(a1)+        ; write nametable entry
```

- The mapping is **flat 1:1, code → 8×8 tile**. There is no character
  banking, which is why a simple `HH=char` table is sufficient.
- One tile is written per character byte, so every glyph is a single 8×8
  tile. The font is roughly 368 tiles (~`0x2E00` bytes as 4bpp).
- `$F0` / `$F1` are **combining marks**, not bank prefixes — they render to
  their own tiles (`$7EE`/`$7EF`, or `$6EB`/`$6EC` when composed) and sit
  *before* the kana they modify. `$F1` precedes exactly five distinct bytes
  across the whole block, matching the five kana that can take handakuten.
  (This corrects the earlier "two-byte code" reading; the practical effect on
  the tooling is nil, since neither ever precedes a terminator.)
- Base alphabet spans `$00–$65`, plus `$B0`. 80 distinct symbols.
- `$B0` is followed by `$FE` in 195 of its occurrences — very likely
  sentence-final punctuation.

## Font search: ruled out

The font is not present uncompressed anywhere in the ROM. Independently:

- A nibble-alphabet scan for 4bpp low-colour tile data (the signature of a
  2–3 colour font) returns **no regions at all**.
- Every low-entropy island was rendered as 4bpp and as 1bpp at 8×8 and
  16×16 and inspected; all show sprite/tile graphics or noise, no glyphs.
- No literal VDP write command for VRAM `$D000` (tile `$680`) exists, so the
  font upload computes its address — consistent with a decompress-then-DMA
  path.

## Decompressor: SOLVED

The graphics codec lives at `$0416F6` and is reimplemented in
[`decomp.py`](tools/decomp.py). It is **RLE + Huffman over 4bpp nibbles**.

Found by following an asset loader at `$05CF90`:

```
05CF9C  move.w  #$580,d0          ; VRAM tile index
05CFA0  lea     ($05D660).l,a0    ; pointer table
05CFB0  movea.l (0,a0,d1.w),a0    ; compressed blob
05CFB4  jsr     ($041C40).l       ; tile index -> VDP write command
05CFBA  jsr     ($0416F6).l       ; <-- the decompressor
```

Stream layout:

```
word    header      bit15 = XOR filter; (hdr << 3) & 0xFFFF = longword count
                    (so hdr & 0x7FFF == tile count)
bytes   code table  built by $0417E4, terminated by $FF
bytes   bitstream
```

Decoding uses a 256-entry fast lookup table indexed by the **top 8 bits** of a
16-bit bit buffer. Each entry is a word `(code_length << 8) | symbol`, where
`symbol = (run << 4) | nibble` — so one Huffman code yields a nibble repeated
1–8 times. Codes whose top 8 bits are `>= $FC` escape to a 7-bit literal
`[run:3][nibble:4]`.

Output accumulates 8 nibbles into a longword, then jumps through `a3` to one
of four 5-instruction handlers at `$0417B8`:

| handler | destination | filter |
|---|---|---|
| `$0417B8` | `(a4)` — VDP data port | none |
| `$0417C2` | `(a4)` — VDP data port | XOR with previous longword |
| `$0417CE` | `(a4)+` — RAM buffer | none |
| `$0417D8` | `(a4)+` — RAM buffer | XOR with previous longword |

Header bit 15 selects the XOR variant by adding `$A` to `a3`.

**Verified**: blobs from the `$05D660` table decode to exactly their declared
sizes (2528 / 3040 / 2464 / 2720 bytes) and yield clean 4bpp tile graphics.
221 blobs across the ROM's pointer tables decompress without error.

```bash
python tools/ps4tool.py decompress work/original.smd 297960 out.bin
```

## Character table: SOLVED

Read out of live VRAM using BlastEm's VDP VRAM Debugger while a dialogue box
was on screen. The font never had to be found in the ROM at all — the game
decompresses it for us at boot, and the renderer's `tile = char + $680` tells
us exactly where to look.

VRAM row 26 (tile `$680`) holds exactly 64 tiles: a space at `$00`, then the
gojūon from `$01`, ending at katakana セ at `$3F`. Row 27 resumes with ソ at
`$40`.

```
$00        space
$01-$2E    hiragana  あ..ん
$2F-$31    small     ゃゅょ
$32-$5F    katakana  ア..ン
$60-$68    small     ァィゥェォッャュョ
$80-$EF    kanji     (not yet identified)
```

**Verification.** The table was confirmed against the ROM without reference to
the font, using Japanese phonology: `$F0` (dakuten) may only precede a voiced-
consonant base, and `$F1` (handakuten) only the five kana that accept it.
Across all 709 extracted messages:

| mark | valid base | invalid |
|---|---|---|
| `$F0` dakuten | 732 | 1 |
| `$F1` handakuten | 53 | 0 |

The single exception is `$F0` followed by `$00` (space), which is padding. A
wrong base offset would break essentially all 785 of these, so this is
conclusive.

### High bank (VRAM row 31, tile `$7C0`)

`$80-$99` are **A-Z**, proven by decoding rather than by reading pixels:
the assignment yields `THE`, `HP`, `FIELD`, `DUNGEON`, `TOWN`, `START`, and
the series' planet names `DEZORIS` and `MOTABIA` — 121 distinct Latin runs.
Two digit sets follow at `$9A-$A3` and `$A4-$AD`.

Two punctuation marks were pinned by context, which corrected an earlier
mistake:

* `$B0` = **ー** (long vowel) — 259 of its 263 occurrences directly follow
  katakana. This had previously been guessed as sentence-final punctuation
  because many item names end with it; that was wrong.
* `$B4` = **。** — 146 of its 160 occurrences end a message.

`$AE`, `$AF`, `$B1`-`$B3`, `$B5`+ are left as raw escapes on purpose. They
are punctuation, but the 8x8 glyphs are too ambiguous to identify safely and
a wrong entry would silently corrupt re-encoded text.

**Result: 94.5% of all script bytes now decode**, up from 0%.

### Retracted: `$7E` is not a dictionary code

An earlier revision of this file claimed `$7E` expanded to two characters
(RA+RE) and treated that as proof of MTE compression. **That was wrong.**
`$7E` is small TSU — the only one in the font, since the hiragana bank has
none — so the construction is TSUKUTTA (made), not TSUKURARETA. The 15 plain
RA+RE byte pairs cited as evidence of ambiguity were simply the other verb
form spelled out. There was never a conflict.

The lesson is the same one the katakana bank taught: a reading that requires
an exotic mechanism should be distrusted when a mundane one fits. MTE was
invented to explain a gap that did not exist.

The `$C0-$ED` hypothesis below stands on its own evidence (those codes cannot
be glyphs, because their tiles exceed VRAM) but it no longer has `$7E` as
supporting precedent.

## Row 27 tail (`$66-$7F`)

Read off the VRAM font: left arrow, empty and grey squares, then window-frame
pieces. `$6B-$72` are the dakuten and handakuten marks pre-composited onto the
window background in four palettes — exactly the eight tiles the renderer
selects with `move.w #$6EB,d2` followed by `add.w d3,d2` where `d3 = d0 >> 12`.
That closes the loop on the `$2805A0` disassembly.

`$76`/`$77` are the middle dot and slash. `$78-$7D` duplicate glyphs that
already exist elsewhere (H/P/T narrow forms, small o, long vowel, RE); they are
left as escapes because mapping them would make encoding ambiguous.

## Two separate text systems (important)

The game has **two unrelated text pipelines**, and everything in this repo
belongs to the first one:

**1. The 8x8 bank — what this toolchain handles.** One tile per character,
rendered by `$280564`. Used for item, monster and character names, battle
text, the status menu, and the item-collection descriptions. This is the
`$00-$B5` table, and the 519 extracted messages are all of this kind.

**2. A 16x16 on-demand system — the story dialogue, NOT handled here.** Each
dialogue character is built from four 8x8 tiles (top and bottom halves, each
two tiles wide), and the glyphs are composed into VRAM per message rather than
living in a fixed bank. Confirmed directly: the VRAM capture in `work/vram.png`
contains exactly the characters that were on screen in the dialogue box at that
moment, three rows above the kana bank, and nothing else.

That second system needs kanji, so its script cannot use the one-byte encoding
above. This is why every scan in this repo failed to find the story script: the
scans searched for the 8x8 bank's byte signature, which the dialogue does not
use. Finding it means finding the glyph-composition routine and working back to
whatever feeds it — a much better-defined target than the blind sweeps tried
earlier.

The practical consequence: **this pipeline covers the game's names, menus and
item text, not its story script.**

## Hunting the dialogue script: what has been eliminated

Three independent static approaches have now failed to find it. Recording them
because they bound the search rather than merely being dead ends.

1. **One-byte alphabet scans.** Every sweep for the `$00-$B5` bank's byte
   signature returns only the two regions already extracted. The dialogue does
   not use this encoding, which is expected now that the 16x16 system is known.

2. **Graphics-codec blob sweep.** 49,057 valid blobs decoded at every even
   offset, none producing script-like output. The codec models 4bpp nibble
   runs and is a poor fit for text.

3. **Two-byte encoding scan.** Kanji forces a wider code space, so the ROM was
   swept for regions whose 16-bit words cluster in a few high-byte banks.
   Seven candidates surfaced; all were eliminated:

   | region | verdict |
   |---|---|
   | `0E1C00`, `0F4800`, `0FEC00`, `115800` | 8-bit PCM audio — 30-52 distinct words all hugging `$80`, the unsigned-sample midpoint, with a smooth waveform |
   | `228400`, `22C000` | sorted tables — ascending runs, ~120-160 distinct values |
   | `27F800` | tilemap / table data |

   Genuine 2-byte text would show hundreds of scattered values plus a
   recurring terminator. Nothing in the ROM does.

4. **Runtime elimination (BlastEm breakpoints).** All three candidate paths
   were ruled out by observation, not inference:

   | breakpoint | fires during dialogue text draw? |
   |---|---|
   | `$280564` 8x8 renderer | **no** |
   | `$0416F6` graphics decompressor | **no** — only scene loads, window frames, portraits |
   | `$041C40` VDP address helper | **no** — observed tiles were `$372 $37A $4DC $4E6 $55C` |

   `$55C` fires on portrait changes specifically, never on text. So the
   dialogue path shares no infrastructure with the systems mapped here.

5. **The font is not stored uncompressed.** Glyph bitmaps were lifted straight
   out of a VRAM capture (rows 22-23, `$580-$5FF`, four 8x8 tiles per 16x16
   character, two lines of text) and searched for in the ROM:

   * as 1bpp: tiles that *did* match average **6.5 set bits**; tiles that did
     not average **11.4**. Only sparse tiles match, which is coincidence — a
     mostly-empty 8-byte pattern occurs anywhere in 3 MB. Real storage would
     match regardless of density.
   * as 4bpp at every foreground index: 1-2 of 20 tiles, same coincidence.
   * no 1bpp->4bpp nibble expansion table exists anywhere in the ROM.

**Conclusion.** The dialogue system is a wholly separate pipeline with its own
compression, its own renderer, and its own VDP access. Nothing in this repo
touches it.

## Breakthrough: everything reaches VRAM by DMA from RAM

Captured live in Exodus. A `$C00004` breakpoint halted at PC `$042152`, inside
a **DMA queue processor**:

```
04213A  lea     ($FFE000).w,a0   ; RAM command queue
042148  move.l  (a0)+,(a6)       ; VDP command words
042152  moveq   #0,d3            ; <- halt
042154  move.b  (-5,a0),d3       ; rebuild DMA source from the entry
042166  movea.l d3,a2            ; a2 = DMA source
042170  move.l  d1,(a6)          ; fire the transfer
```

`a0` was `$FFFFE00E`, exactly one 14-byte entry past the queue base.

The queue is filled by the helper at **`$0420D6`**, which is the single
chokepoint for every VRAM upload in the game:

```
0420DA  lea     ($FFE000).w,a0   ; queue base
0420DE  move.w  ($FFEF1E).w,d3   ; queue index, 16 bytes per entry
0420E6  move.b  #$93,(a0)+ / d2  ; VDP regs 19-20 = DMA length
0420F4  move.b  #$95,(a0)+ / d0  ; VDP regs 21-23 = DMA source
04210E  move.w  d1,d0            ; d1 = destination command
```

**d0 = DMA source, d1 = VDP destination command, d2 = length in words.**

This explains why every earlier search failed. The game never writes tiles
through the data port; it queues DMA requests in RAM and fires them in vblank.
There is no ROM-to-VRAM code path to find, because none exists. Dialogue
glyphs are composed **in RAM** and DMA'd across, which is also why the font is
not present in the ROM in any renderable form — it is presumably stored
transformed and expanded into a RAM buffer before transfer.

### Live captures at `$0420D6`

Confirmed working in Exodus. Two distinct transfer types were caught:

| d0 (source/2) | real source | d1 (dest) | d2 (words) | what |
|---|---|---|---|---|
| `$7FFFC000` | RAM `$FFFF8000` | `$C000` | `$800` = 4096 B | plane-A nametable, refreshed every frame |
| `$00148780` | ROM `$290F00` | `$A780` | `$80` = 256 B | 8 tiles - sprite/portrait art, not glyphs |

`$290F00` was rendered as 4bpp and is multi-coloured blob art, so it is
portrait/sprite data. Neither destination falls in the `$B000-$BFFF` glyph
range, so the glyph upload has not yet been caught.

Useful mechanics established:

* input reaches the game via SendKeys once the display has focus (`a` acts as
  the action button, arrows move), so dialogue can be advanced programmatically
* with **Break** unchecked and **Log** checked the game runs freely while every
  hit is still recorded, but the log stores only the address - register values
  must be read from the Registers window, so free-running logging cannot
  capture `d0`/`d1`/`d2`
* stepping with F3 between captures proved unreliable when driven blind: the
  same halt state was re-read repeatedly

### LZSS compressor - the story script is now reinsertable

[`lzss_enc.py`](tools/lzss_enc.py) produces streams the game's own decompressor
reads. Greedy matching with a lazy-match heuristic: if starting one byte later
buys a materially longer match, emit a literal now and take it next round.

All eight streams round-trip (`decompress(compress(x)) == x`), and the output
lands **1.2% under the originals**, so a rewritten stream fits the space the
original occupied - nothing repoints, so fitting is mandatory.

| stream | original | recompressed | headroom | gap to next |
|---|---|---|---|---|
| `$1CC476` | 3692 | 3668 | +24 | 4 |
| `$1CD2E6` | 4704 | 4681 | +23 | - |
| `$1D02D6` | 3955 | 3944 | +11 | 13 |
| `$1D1256` | 4552 | 4523 | +29 | - |
| `$1D4FB6` | 2660 | 2646 | +14 | 12 |
| `$1D5A26` | 3559 | 3540 | +19 | - |
| `$1DA026` | 4109 | 4082 | +27 | 3 |
| `$1DB036` | 1721 | 1714 | +7 | - |

A no-op rewrite reproduces all eight streams' decompressed contents exactly
(verified by decompressing both ROMs and comparing), and changes nothing
outside the rewritten spans.

**All eight streams are reinsertable.** An earlier version of this document
recorded two of them as excluded because `$1D4FBC` and `$1D59B0` had
overlapping compressed spans. That overlap was an artifact of wrong start
addresses, not a real conflict - see *Wrong stream starts* below. With the
corrected starts every adjacent pair has a small positive gap (3-13 bytes),
which is what genuine neighbours look like. `reinsert_streams` keeps its
overlap check as a guard, but it no longer fires.

**Extractor bug found while testing this.** `extract_streams` skipped empty
messages (`if raw:`), so each consecutive-`$FF` pair silently lost a
terminator, and bytes after the final terminator were dropped entirely. One
stream came back 13 bytes short - exactly its 12 empty messages plus a 1-byte
tail - which shifted every later message. Empty messages are now kept and the
tail is stored as its own entry flagged `tail`.

### Kanji table complete (859 glyphs)

Built by rendering the glyphs the script actually uses and reading them off the
sheet, in batches of 60 ordered by frequency. 16x16 1bpp renders at scale 4 are
cleanly legible, so this is mechanical rather than uncertain.

Two indices render the same character (`$28F`/`$1CA` and `$21D`/`$495`). Only
the first of each pair is mapped; the second stays a `{Kxxx}` escape, because
mapping both would make the encode direction ambiguous and break byte-exact
round-trip.

All sixteen `$F0-$FF` control codes are now named. Their semantics are still
unknown - they are placeholders (`ctl.F4` etc.), not decoded behaviour - but
naming them keeps real escapes visible instead of drowning in noise.

**Final state: 1329 messages, 46207 bytes, 1329/1329 lossless.**

Remaining escapes: **43 of 46207 bytes (0.09%)**

* 34 invalid single-byte characters (`$D3 $D4 $D9 $DA $DE`). These index past
  glyph 209, where the font is graphics, and the renderer has no special
  handling below `$F0` - so they should not be renderable. Most likely control
  codes that take an operand byte, which the parser currently reads as a
  character. The dialogue dispatch table at `$06AB58` is degenerate (`$F0-$FE`
  all branch to a bare `rts`), so the operand handling is elsewhere.
* 9 duplicate-reading kanji, deliberately left as escapes per above.

### SOLVED: the story script - a third codec (LZSS)

The story script is LZSS-compressed in ROM and expanded into the RAM buffer at
`$FF3000`. This is a **third** codec, unrelated to the 4bpp graphics
Huffman/RLE at `$0416F6` - which is why sweeping every compressed blob with
that decoder found no script whatsoever.

Reimplemented in [`lzss.py`](tools/lzss.py). Decompressor at `$041BA0`:

```
041BA2  move.b (a0)+,(1,a7)   ; 16-bit flag word, low byte first
041BAC  lsr.w  #1,d5          ; one flag bit per operation
041BC2  move.b (a0)+,(a1)+    ; bit set   -> literal byte
041BC6  ...                   ; bit clear -> match
```

Matches take two forms: **short** (2 more flag bits give length-1, then one
byte gives an 8-bit negative offset) and **long** (two bytes give a 13-bit
negative offset and a 3-bit length-1). A long-form length code of 0 means an
extended byte follows: 0 ends the stream, 1 is a no-op, otherwise it is the
length. Offsets index backwards into the output, so matches may overlap.

Called via the wrapper at `$05402A`, which reads the stream pointer from a
table and sets `a1 = $FFFF3000`.

**Eight script streams**, found by sweeping `$1C0000-$1E0000` and validating
the output as dialogue:

| stream | bytes | spurious spaces before fix |
|---|---|---|
| `$1CC476` | 5148 | 812 |
| `$1CD2E6` | 6116 | 0 |
| `$1D02D6` | 4802 | 142 |
| `$1D1256` | 5864 | 0 |
| `$1D4FB6` | 3676 | 139 |
| `$1D5A26` | 4730 | 369 |
| `$1DA026` | 6298 | 0 |
| `$1DB036` | 2652 | 1079 |

Decode -> encode reproduces the decompressed bytes exactly for every stream.

#### Wrong stream starts - the missing-characters bug

The brute-force sweep that located these streams returned starts that were
*plausible* rather than correct: five were 6-190 bytes late. An LZSS stream
decodes correctly enough from a late start to look like real dialogue, because
most of the data is literals - so the usual validity checks all passed.

What gave it away is that the decompressor was **papering over the damage**.
A back-reference reaches backwards into the output produced so far, and a
stream never references before its own start, since the game decompresses into
a fresh buffer. Starting late means some references point before the buffer
start. `lzss.py` was appending `0x00` in that case - and `$00` decodes to a
space. So the failure was silent and looked like nothing at all: **1258
underflowing references produced 2541 spurious spaces**, dropping characters
out of the middles of sentences.

The fix is in two parts:

- `lzss.py` now **raises** on an underflow instead of substituting a zero. A
  wrong start should be loud.
- The starts were corrected by searching outward from each bad one for a
  candidate with zero underflows and zero invalid kanji indices. All five
  resolved, and the corrected `$1DB036` matches the entry in the real pointer
  table at `$58A50` exactly - independent confirmation.

The three streams that were already correct (`$1CD2E6`, `$1D1256`, `$1DA026`,
the last of which came from that pointer table) kept their space counts
unchanged at 110, 82 and 80. The corrected streams dropped into the same range
(34-89). Those are genuine spaces.

This also dissolved the "overlapping streams" problem recorded above: the
overlap was between two *wrong* starts.

#### The last 13 kanji - and a wrong entry in the existing table

After the two fixes above, 26 `{Kxxx}` escapes remained across 13 distinct
glyph indices. These were rendered straight out of the font at `$1F62BA` and
read off.

**The kanji font uses the same layout as the 8x8 font**: four 8x8 tiles in
row-major order (TL TR BL BR), 8 bytes each. Drawing it as 16 rows of 2 bytes -
the obvious reading of a 16x16 1bpp glyph, and the one tried first here -
produces pure noise. This is the second time that assumption has cost time in
this project; it is written down now.

| index | glyph | fixed by context |
|---|---|---|
| `K021` | 研 | research |
| `K03E` | 陥 | subsidence |
| `K05C` | ヶ | counter, not a kanji at all |
| `K096` | 殻 | crustal upheaval |
| `K0A0` | 混 | confusion |
| `K0E3` | 憶 | memory |
| `K189` | 秘 | mysterious |
| `K242` | 偉 | great |
| `K28F` | 維 | carbon fibre |
| `K429` | 冬 | cold sleep |
| `K467` | 似 | resembles |
| `K48A` | 字 | writing |
| `K495` | 簿 | household ledger |

Each was confirmed twice over - once from the rendered glyph, once from the
surrounding words - and the two agreed in every case.

`K495` needed the bitmap to settle: at display size the top radical reads as
艹, which would make it 薄. The bitmap row is `.######.#######.`, two separate
horizontal bars rather than one continuous one, which is ⺮. So it is 簿.
Scaled-up screenshots are not reliable for radical-level distinctions; dump the
bits.

**Adding these exposed an error in the pre-existing 859-glyph table.** `K28F`
is 維, but the table already carried 維 at `K1CA`, so re-encoding silently
substituted one for the other and round-trip broke on exactly one message.
The two bitmaps are *not* identical: both have the 糸 radical, but `K28F` has
隹 on the right (糸+隹 = 維) while `K1CA` has 夂 over a 辶 sweep (糸+逢 = 縫).
`K1CA` occurs once, in a list of household chores ending in 裁縫, sewing.
`K1CA` is now 縫.

That error had been invisible for as long as `K28F` was unmapped - nothing
collided, so nothing complained. The check that catches this class of mistake
is now run over the whole table: no two identical bitmaps may carry different
characters, and no character may claim two different bitmaps. **0
inconsistencies across 872 mapped glyphs.**

#### Control codes take operand bytes

The remaining 45 bytes with no table entry were not characters either. The
dispatcher at `$06AE32` does `andi.w #$F,d5` / `add.w d5,d5` (twice) /
`jmp (94,pc,d5.w)`, so the branch table is 16 `BRA.w` entries at `$06AEA6`:

| code | target | behaviour |
|---|---|---|
| `$F2` | `$06AEE8` | `move.b (a0)+,d0`, then sub-dispatch via `$06A652` - **1 operand byte** |
| `$F4` | `$06AEFE` | `move.b (a0)+,d0` - **1 operand byte** |
| `$FA` | `$06AECE` | branches to a bare `rts` |
| `$FC` | `$06B044` | line break |
| `$FD` | `$06B056` | page / wait |
| `$FE` | `$06AE9C` | stores `a0` to `$FFECF0` and returns |
| `$FF` | `$06AE7E` | message terminator |
| `$F0 $F1 $F3 $F5 $F6 $F8 $FB` | `$06AEE6` | bare `rts` |

Because the dispatcher arrives by `JMP` rather than `JSR`, an `rts` in a
handler returns out of the renderer entirely. So `$FA` **ends the text**, and
the two bytes following it are read by the event interpreter rather than drawn.

Applying exactly these three widths - `$F2`:1, `$F4`:1, `$FA`:2 - takes the
count of bytes with no table entry from **45 to 0**. That is what pins the
widths down: `$D9` and `$DA` occur in the entire script *only* as the first
operand byte of `$FA`, 45 times out of 45. Two further speculative widths were
tested and rejected - they changed nothing, so there is no evidence for them.

Before this, 1176 operand bytes were being decoded as ordinary kana, putting
stray characters inside sentences. They now decode as `{ctl.F4:01}` /
`{ctl.FA:DA02}`, which round-trip exactly and are counted against the byte
budget by the proofreader.

**Measurement caution.** An earlier check reported 0.3-1.2% bad bytes and a
suspicious skew toward stream ends. That was wrong: it scanned linearly with
`enumerate`, so the *second byte of every two-byte kanji code* was being tested
as though it were a standalone character. Those continuation bytes can hold any
value. Walking the stream properly (`i += 2` past kanji) gives the 0.12% above.
This is the same failure as the `{C0}` miscount recorded elsewhere in this file
- a flawed measurement presented as a finding.

These streams are fully reinsertable - see *LZSS compressor* above.

### The script is decompressed into RAM

Caught live in Exodus. Breakpoint on the glyph selector `$06A9FA` - the
chokepoint every rendered character passes through - halted with:

```
a0 = $FFFF3B31     script stream pointer  -> RAM, not ROM
d0 = $000000E0     character code, a kanji lead byte
pc = $0006A9FA
```

`a0` points into work RAM. **The dialogue script is decompressed into a RAM
buffer before rendering**, which explains why only ~5 KB exists in ROM in this
encoding and why none of the 49,057 compressed blobs contained any: the
finished form never exists in ROM at all.

Next step is a watchpoint on writes to that buffer (~`$FF3B00`) to catch the
routine that fills it - the same technique that found the glyph composer.

**Three earlier inference chains were wrong** and are recorded here so they are
not retried:

* `$FFEC2C` - assumed to be the script pointer because a `movea.l` of it sits
  near the renderer call. It actually precedes a `jmp $051C28` elsewhere. Its
  value never changed between a savestate load and a live conversation, which
  a real message pointer would.
* `$14B0A8` - the table `$FFEC2C` points at. Parses with 67 invalid kanji
  indices; not script.
* `$FF0200` - derived from `$FFECF0`. Contains only nibbles `0`/`F`, i.e. 4bpp
  pixel data, and changed only across a cutscene rather than per conversation.

Also note `$06AE1E` is **not** the renderer used for NPC dialogue: a
breakpoint there never fires. There are two text loops reading `(a0)+`, at
`$06AE34` and `$06AAE4`; dialogue uses the latter. Breakpointing the shared
selector `$06A9FA` avoids having to pick correctly.

### Search for the rest of the script: exhausted

With a working decoder the search could finally be done properly, and the
answer is that there is not much more to find.

**Kanji font extent measured.** Glyph-likeness testing from `$1F62BA` shows a
sustained non-glyph run beginning at index `$4DE`. The located script's highest
used index is `$4DD` - exactly one before it. So the table holds **1246 glyphs,
indices `$000-$4DD`, `$1F62BA-$1FFE7A`**, which independently matches the
extent derived earlier from the maximum index alone.

**Not in the graphics codec.** The 49,057-blob sweep was re-run, this time
validating output as *dialogue* rather than against the 8x8 alphabet (the
earlier sweep tested the wrong encoding). Result: **zero** blobs decode to
valid dialogue.

**Not elsewhere uncompressed.** A ROM-wide scan requiring no invalid kanji
index, sane message lengths and real kanji density returns ~8 KB, nearly all
of it either already known or kana-heavy windows that pass by accident.

### Correction: region bounds, and a weak test retracted

The dialogue region was originally given as `$2AC800-$2AE000`. That **overlapped
two regions already validated as 8x8 text** - item names at `$2ABEFF-$2AC911`
and item descriptions at `$2ADF23-$2AF268` - so 221 bytes of 8x8 text were
being mis-parsed as dialogue. Corrected to `$2AC911-$2ADF23`.

An earlier claim that "kanji index validity" was a hard validator is
**retracted**: it passes trivially on any data containing few `$E0-$EF` bytes,
including confirmed 8x8 text. The 8x8-mapping-rate test was likewise too noisy
to locate a boundary (74-87%, oscillating).

What *does* separate the two encodings sharply:

| region | kanji | `$FF` messages |
|---|---|---|
| 8x8 item names | **0** | **0** |
| 8x8 item descriptions | **0** | **0** |
| dialogue | 715 | 327 |

The 8x8 regions contain **zero** bytes in `$E0-$EF` and **zero** `$FF` bytes,
so they cannot be confused with dialogue in either direction. Two adjacent
spans were tested and rejected on principle: `$2AB0C3-$2ABEFF` averages 44.6
characters per message, impossible for a 16x2 box holding 32, and `$2AF268`
onward contains no kanji at all.

### Dialogue toolchain

`dialogue.py` + `ps4_dialogue.tbl` extract the dialogue stream, separate from
the 8x8 pipeline. `ps4tool.py`-style usage is via the module directly.

```
328 messages   5547 bytes   715 kanji   0 unmapped
decode -> encode identity: 328/328
control codes: BR 105, ctl.FE 35, ctl.F0 22, ctl.F1 5
```

Kanji are emitted as `{Kxxx}` escapes rather than characters. Identifying all
4096 glyphs means reading them off the font sheet one at a time; a placeholder
round-trips exactly and can be filled in incrementally.

**The dialogue font table (`$2A3452`) is not the same as the 8x8 table.**
It is richer and, crucially, has **pre-composed voiced kana**, so the dialogue
stream needs no `$F0`/`$F1` combining marks at all:

| index | contents |
|---|---|
| 0 | blank |
| 1-46 | hiragana A..N |
| 47-55 | small a i u e o, tsu, ya yu yo |
| 56-80 | voiced/semi-voiced hiragana GA..PO |
| 81-90 | digits 0-9 |
| 91-136 | katakana A..N |
| 137-145 | small katakana |
| 146-170 | voiced/semi-voiced katakana GA..PO |
| 171-181 | `! ? kagi . : chouon . , ( / ...` |
| 182-207 | A-Z |
| 208-209 | closing kagi, `)` |

Index 210+ is graphics, so 209 is the last character. The script's single-byte
codes top out at 208, which corroborates both the table and the region.

Control-code names in the table are deliberately non-hex (`ctl.F0`, not `C0`):
an earlier revision named `$F0` as "C0", which decoded to `{C0}` and was then
miscounted by the tooling's own unmapped-byte check as a raw escape. Nothing
was actually unmapped.

### Dialogue script located at `$2AC800-$2AE000`

Found by parsing the ROM *as* the decoded encoding and testing self-consistency,
after a value-based scan failed completely (it matched 1.88 MB - unsurprising,
since this encoding makes all 256 byte values legal, so byte histograms cannot
discriminate at all).

Validation of `$2ACC00-$2AE000` (5120 bytes):

| measure | value |
|---|---|
| kana characters | 3265 |
| kanji characters | 715 |
| control codes | 425 |
| messages | 246, median length **16** |
| kanji index range | `$00A-$4DD`, 217 distinct |
| control codes used | `FF`:285, `FC`:110, `F0`:20, `FE`:8, `FB`:2 |

Three independent checks agree:

1. **Median message length is 16**, matching the renderer's 16-column box.
2. **`$FC` is the line break**, used 110 times here - the same code and role
   measured independently at 106 uses in the 8x8 item text.
3. **Kanji indices land inside the font.** Max index `$4DD` implies the table
   runs to `$1FFE7A`. An earlier scan had flagged `$1FF141-$1FF3BB` as
   "text-like"; that was kanji glyph data all along. No index overflows into
   unrelated data.

A wider structural sweep reports 37 KB across 22 regions, but most are isolated
1 KB windows inside graphics banks and have the signature of false positives.
Only the contiguous `$2AC800-$2AE000` block is corroborated by the validation
above. 6 KB is far short of a full RPG script, so either more script lives
elsewhere in a form this sweep misses, or it is banked.

**To settle it definitively:** read the longword at `$FFEC2C` (the script
pointer, loaded into `a0` by `$05AEB0`) while different dialogues are on
screen. Each value is a live script address, which maps the real extent
without guesswork.

### SOLVED: the dialogue script encoding

The renderer at `$06AE1E` walks the script one byte at a time from `a0`:

```
06AE34  move.b  (a0)+,d0      ; next script byte
06AE36  cmpi.b  #$F0,d0
06AE3A  bcs     $06AE4A       ; < $F0 -> printable
06AE3E  andi.w  #$F,d5        ; $F0-$FF -> control code
06AE46  jmp     (94,pc,d5.w)  ; 16-entry bra.w dispatch table at $06AEA6
06AE4A  jsr     ($06A9FA,pc)  ; -> glyph pointer
06AE4E  jsr     ($06AA30,pc)  ; -> expand into the glyph buffer
06AE5C  addq.w  #1,d1
06AE5E  andi.w  #$F,d1        ; 16 columns
06AE64  addq.w  #1,d2
06AE66  andi.w  #$1,d2        ; 2 rows
```

and the selector at `$06A9FA` splits kana from kanji:

```
06A9FE  cmpi.b  #$E0,d0
06AA02  bcs     $06AA1C       ; < $E0 -> kana, single byte
06AA04  lsl.w   #8,d0         ; >= $E0 -> two-byte code
06AA06  move.b  (a0)+,d0      ;   second byte from the stream
06AA08  andi.w  #$FFF,d0      ;   12-bit kanji index (0-4095)
```

**Encoding:**

| byte | meaning |
|---|---|
| `$00-$DF` | single byte, index into the kana table at `$2A3452` |
| `$E0-$EF` | first of a **two-byte** code; `(b0<<8 \| b1) & $0FFF` indexes the kanji table at `$1F62BA` |
| `$F0-$FF` | control code, 16 handlers dispatched from `$06AEA6` |

16 columns x 2 rows matches the dialogue box and the VRAM rows 22/23 seen in
the font capture.

This is why every scan for the script failed. The searches assumed the one-byte
alphabet of the 8x8 bank; the dialogue stream is mixed-width with a 12-bit
kanji space, so its byte histogram looks nothing like the item text.

**The script pointer is the RAM variable `$FFEC2C`**, loaded into `a0` by the
caller at `$05AEB0` (`movea.l ($FFEC2C).w,a0`) immediately before invoking the
renderer. Reading that longword while a dialogue box is on screen yields the
address of the live script.

### SOLVED: the dialogue font, and how glyphs are built

Found by watchpointing writes to `$FF7000` in Exodus. (The watchpoint must be
committed with **Save** or it silently never arms - that cost several attempts.)

**Font tables** — both 1bpp, 16x16, **32 bytes per glyph**:

| address | contents |
|---|---|
| `$2A3452` | kana, indexed `index * 32` via a word multiply |
| `$1F62BA` | kanji, indexed `index * 32` via a long multiply |

Glyph layout is **four 8x8 tiles in row-major order** (2 across, 2 down), not
16 rows of 2 bytes. Rendering it the latter way produces convincing-looking
noise, which is what made earlier bitmap searches fail even when pointed at
the right region.

The kana table's index order matches the 8x8 bank exactly: blank at 0, then
the gojuon from 1. That strongly suggests the dialogue script reuses the same
character codes already decoded in `ps4.tbl`.

**The expander at `$06AA30`** turns 1bpp into 4bpp on the fly:

```
06AA34  movea.l a1,a0            ; source = 1bpp glyph
06AA36  lea ($FFFF7000).l,a1     ; dest = glyph buffer
06AA4C  move.w  #$F,d0           ; ON  colour $F
06AA50  move.w  #$E,d1           ; OFF colour $E
06AA54  move.w  #$1F,d7          ; 32 source bytes
06AA58  move.b  (a0)+,d6         ; 8 pixels
06AA62  btst    d4,d6            ; set -> $F, clear -> $E
06AA72  move.l  d5,(a1)+         ; 8 nibbles out
```

32 source bytes become 32 longwords = 128 bytes, exactly the DMA size seen in
the queue. `$06A8AA` clears both VRAM `$B000` and the RAM buffer beforehand,
confirming the pairing.

**Full chain, now complete:**

```
character code
  -> * 32 into the font table at $2A3452 (kana) or $1F62BA (kanji)
  -> 1bpp glyph, 32 bytes
  -> expander at $06AA30, 1bpp -> 4bpp ($F on, $E off)
  -> RAM buffer $FF7000, 128 bytes per character
  -> DMA queued by $0420D6, fired by $04213A
  -> VRAM $B000-$BFFF
  -> rendered as 16x16 text in the dialogue box
```

This is why the font was never findable in ROM by bitmap search: it is stored
1bpp at a third the size of the 4bpp form that reaches VRAM, in a tile order
that defeats naive rendering.

### Glyphs are composed in RAM at `$FF7000`

Read straight out of the DMA queue at `$FFE000` while dialogue was drawing.
Each entry is 16 bytes of VDP register/value pairs followed by the destination
command: `93 <len lo> 94 <len hi> 95 <src lo> 96 <src mid> 97 <src hi> <cmd>`.

| # | length | source | destination | what |
|---|---|---|---|---|
| **0** | `$40` w = **128 B** | **`$FF7000`** RAM | **`$B100`** | **one 16x16 glyph** |
| 1 | `$800` w = 4096 B | `$FF8000` | `$C000` | nametable |
| 2 | `$800` w = 4096 B | `$FF8000` | `$C000` | nametable |
| 3 | `$100` w = 512 B | `$FF9C00` | `$EC00` | sprite table |

Entry 0's command `$71000082` decodes as VRAM `$B100` (`$3100` from the high
word, `(82 & 3) << 14` from the low), DMA bit set. `$B100` is tile `$588`,
in row 22 - the top line of the dialogue box. 128 bytes is exactly four 8x8
tiles, i.e. one 16x16 character.

**Conclusion: the dialogue font is never in ROM in renderable form.** Glyphs
are built one character at a time into a RAM buffer at `$FF7000` and DMA'd to
VRAM. Every bitmap search of the ROM was therefore doomed regardless of method.

**Next: watchpoint on writes to `$FF7000`.** That catches the composition
routine, and whatever it reads to build the glyph is the font source - most
likely a packed or compressed form indexed by character code. Following the
index back gives the script.

**Superseded experiment.** Breakpoint `$0420D6` and record `d0`/`d1`/`d2` on
each hit while dialogue draws. The entry whose `d1` decodes to a VRAM address
in `$B000-$BFFF` is the glyph upload, and its `d0` is the RAM buffer holding
the composed glyphs. A watchpoint on writes to that buffer then catches the
composition routine, and from there the script.

Exodus exposes 68000 Watchpoints and a Call Stack window
(Debug > Mega Drive > Main 68000), and the Event Log can be exported to CSV,
which makes this tractable. Note the log records only the accessed address,
not the PC, so register values must come from the Registers window.

**What it would take (superseded by the above).** The glyph slots are computed at runtime, so there is
nothing to grep for; the composition routine has to be caught writing. That
needs a VRAM write watchpoint on `$B000-$BFFF`. BlastEm 0.6.2's debugger has
no watchpoint command (`?`/`help` are not valid, `vdpwatch` is silently
ignored) and its win32 build does not bind to piped stdio, so this is the
point at which a different debugger is worth more than further static work.
Exodus and Regen both expose VRAM access breakpoints.

## Retracted: the MTE hypothesis has no evidence left

Two earlier claims in this file supported the idea that the script was
compressed with a substitution dictionary. Both were wrong:

* `$7E` was read as a two-character macro. It is small TSU.
* `$C0-$ED` were reported as 61 in-use codes whose tiles exceed VRAM, and
  therefore "not glyphs". Those measurements came from the six regions later
  proved to be 68k code. **In the confirmed text regions, no byte >= `$C0`
  occurs at all** except the control codes `$FB` and `$FC`.

Nothing supports MTE compression. The pattern in both cases was the same:
reaching for an exotic mechanism to explain an artefact of bad input data.

## `$C0-$ED` are not glyphs (superseded - see retraction above)

61 distinct codes in this range are in active use, but the renderer would map
them to tiles `$800-$82D` — past the top of a 64 KB VRAM (`$7FF`). They
therefore cannot be characters, and something must expand them before the
renderer ever sees them.

The most likely explanation is **MTE (multi-tile encoding)**: a dictionary of
common words or phrases, each referenced by a single byte. That is a standard
JRPG script-compression technique and would explain a great deal — why no
bitstream text decompressor was ever found, and why the uncompressed script
is far smaller than the game's real dialogue volume.

If that holds, the "missing text codec" is not a codec at all but a
substitution table, and finding it means locating the dictionary plus the
routine that expands these codes. That is the next thread to pull.

## Font in ROM: still not located

The font remains the one thing standing between this toolchain and a real
character table. It is **not** reachable through the codec above:

- Exhaustive sweep of every even offset in the ROM for a valid blob with
  32–700 tiles and font-like ink coverage (12–32%) yields 41 candidates,
  all small sprite/UI fragments in the graphics banks.
- Targeted searches at the two sizes the renderer implies — ~128 tiles for
  the `$680` range and ~368 tiles for the full `$680`–`$7EF` span — return
  nothing that renders as glyphs.
- The two exact-11776-byte hits (`$06B98C`, `$06C2D8`) decode to blank tiles.

So the font is either compressed with a second, different codec, or stored
in a form whose header does not match this one. Finding it is now a bounded
search problem rather than an unsolved format, since the general-purpose
decompressor and the disassembler are both in hand.

## Extending

Add `HH=char` lines to `ps4.tbl` as glyphs are identified; the extractor,
checker, reinserter and proofreader all pick them up with no code change.
Add newly located regions to `ANCHORS` / `BLOCK_END` in `script_io.py`.

## Half-width text rendering

The renderer draws one 16x16 glyph per cell and wraps at 16 columns
(`andi.w #$F,d1`), then at 2 rows (`andi.w #$1,d2`). Sixteen characters a line
is fine for Japanese and hopeless for English. This patch makes `d1` count
HALF cells (0..31), so an 8-pixel glyph occupies half a cell: **32 characters
per line**.

**Why it is possible.** `$06AA7E` DMAs from a fixed source - `#$7FFFB800`, and
`$FFFF7000 >> 1` is exactly that. So the expander stages ONE glyph into a
128-byte buffer at `$FFFF7000` and the DMA copies that buffer to the cell's
VRAM address. The buffer persists between characters, so two 8-pixel glyphs can
be composed into one cell before it is sent. A cell is four 8x8 tiles at
offsets 0/32/64/96, so the left half is 0+64 and the right half is 32+96.

A half-width glyph is stored in the **left half of its 16x16 font cell** -
source bytes 0-7 (top) and 16-23 (bottom).

### Layout

| what | where |
|---|---|
| width bitmap | `$0E7140`, 28 bytes, one bit per code `$00-$DF`, MSB first |
| draw routine | `$0E7160`, 300 bytes |
| call site | `$06AE4A`, 36 bytes (replaces the inline draw sequence) |

`$0E7130-$0E7FFF` is `$FF` filler at a bank boundary; the patcher refuses to
run if that region is not filler.

### Inert by default

The width table ships **all zero**, so every glyph stays full-width and the
display is unchanged. That keeps "did the patch break anything" separable from
"does half-width look right". Verified three ways:

- 357 bytes differ from the stock ROM, **0 outside the three intended regions**
  (plus the checksum)
- all eight script streams decompress byte-identically
- the column/row/page sequence with an empty table is **identical** to the
  original loop's, simulated over a full line

Opt in per character with `hw-set`; `hw-list` shows what is marked.

### Design notes

- The full-width path forces `d4 = 0` before calling `$06AA30`. `d4` selects
  whether the expander applies a `d1`/`d2` offset, and it must be 0 for the
  staged cell to line up with the fixed DMA source. Forcing it makes the patch
  correct without depending on what the caller happened to leave in `d4`.
- A full-width glyph must start on an even half-column. One landing on an odd
  column skips the empty half. If that skip runs off the line *and* the page,
  the routine rewinds `a0` onto the code byte and returns 0, so the caller runs
  the page handler and the glyph is drawn on the fresh page rather than lost.
  The page handler peeks at `(a0)` without consuming anything unless it sees
  `$FF`/`$F7`/`$FD`, so the rewound byte is re-dispatched cleanly.
- `expand8` seeds each pixel row with the OFF colour `$E` and increments to `$F`
  where a bit is set, instead of holding both colours in registers - the
  routine is already short of registers with `d1`/`d2` reserved for the caller.

### Not yet run under an emulator

Everything above is static verification: the routine was assembled, then
**disassembled and read back** instruction by instruction, and the no-op case
was proven equivalent. It has not been executed. The things most likely to need
a live check are DMA timing (each cell is still one DMA, but half-width doubles
the number of DMAs per line) and whether the staged right-half blanking is
visible as flicker.

### A note on the US release

The US version of the game is a separate build with its own text engine, not a
re-fonted Japanese ROM. It shows that Sega's engine could render English; it is
not evidence that this build accepts a drop-in font swap, and none of its data
was consulted here.

## The script is 26 streams, not 8

Hunting for stream pointers to enable relocation turned up something bigger:
**two thirds of the script had never been extracted.**

There is no single pointer table. Streams are reached three ways:

    move.l #<stream>,d0 ; jsr ($05402C).l    literal in event code
    jsr ($05402A).l followed by an inline longword
    movea.l ($FFECF8).w,a0 ; move.l (a0),d0  first field of an area descriptor

plus $058970, which indexes a small table at $058A50 by the byte at $FFF400.
$05402A and $05402C are two entry points to the same wrapper, one byte apart:
the first reads the pointer from (a0)+, the second takes it in d0.

Scanning for the `move.l #imm,d0 ; jsr ($05402C).l` pattern gave 11 stream
addresses, 9 of which were not in the extracted set. Re-sweeping the ROM with
the strict decompressor then found 26 in total, and the code-derived addresses
cross-check against the sweep.

| | before | after |
|---|---|---|
| streams | 8 | 26 |
| messages | 1360 | 2131 |
| plaintext | 45,391 | 126,917 |

All 26 round-trip byte-exact, with no overlaps and consecutive spans 0-15
bytes apart.

**Why the first sweep missed them.** It used the decompressor that substituted
`0x00` on a back-reference underflow instead of failing. A wrong start still
produced plausible-looking dialogue, so the scan accepted it and skipped past
the real stream behind it. Making underflow raise turned the sweep from
unreliable into decisive - the same bug that ate 2541 characters was also
hiding most of the script.

**A second measurement error.** The first re-sweep reported only 5 streams
because it advanced `i += used` after a hit; `used` is often odd, which threw
every later probe onto odd addresses where no stream starts. Rounding up to
even found 24. Two more were rejected by the strict kanji filter but are
referenced by code, giving 26.

### Entry ids are keyed by stream address

Ids were `lz{index}#{n}`, where index was the stream's position in `STREAMS`.
Adding streams renumbered every later id and orphaned any translation keyed to
one. They are now `lz{address:06X}#{n}`, which is stable as more streams are
found. Migrating existing work across matches on (stream, offset).

## Script fully decoded

| | before | now |
|---|---|---|
| streams | 8 | 26 |
| messages | 1360 | 2131 |
| plaintext | 45,391 | 126,917 |
| kanji mapped | 872 | 1157 |
| unresolved kanji | 26 | **0** |
| unmapped bytes | 45 | **0** |

Round-trip is byte-exact on all 26 streams.

### Two more control operands

`$F9` is a delay - `move.b (a0)+,d7 / subq.b #1,d7 / jsr ($041638) / dbf d7` -
so it takes one operand byte, which the table did not know.

`$F2` is **variable width**. Its byte selects a sub-handler through the table
at `$06A652`, and three of the thirteen read a further byte themselves (#3
`$06A6D0`, #4 `$06A6E6`, #11 `$06A858`); the rest open with
`movem.l ...a0...,-(a7)` and restore `a0`, so whatever they read leaves the
script pointer where it was. Reading the handlers without checking that
distinction over-counts badly - a saved-and-restored `a0` consumes nothing from
the caller's point of view. `dialogue.ctrl_width()` handles the variable case.

Between them these accounted for 48 + N bytes that had been decoding as text.

### The kanji table ends at $4DD after all

An intermediate analysis suggested the table ran to `$DF2`, which would have
meant ~3500 glyphs. It does not: rendering probe glyphs showed `$4D0` and
`$4DD` are real characters, `$4E0` is solid black, and everything past it is
noise. The apparent high indices were an artifact of parsing `$F2`/`$F9`
operands as kanji lead bytes. With correct widths, **every** kanji index in the
script is <= `$4DD`.

### The remaining 285 glyphs

Rendered in six sheets and read off, then cross-checked against context. The
table's ordering is not JIS, Unicode, or anything else exploitable - 50%
monotonic is exactly chance - so there was no shortcut. It does appear to be
roughly first-use order, which shows up as compound words landing on adjacent
indices (`$41F`/`$420` = 永/劫, `$423`/`$424` = 雰/囲); that adjacency is a
useful sanity check on a reading.

**The consistency audit caught two errors, one of them pre-existing.**

| index | was | is | settled by |
|---|---|---|---|
| `$3E2` | 情 (my reading) | 楕 | 長大な**楕**円軌道 |
| `$48D` | 属 (pre-existing) | 彫 | 木**彫**り, **彫**刻 |

`$48D` is the second error found in the original 872-glyph table, after
`$1CA`. Both were invisible until a newly identified glyph collided with them -
which is the whole point of the audit: no two identical bitmaps may carry
different characters, and no character may claim two different bitmaps. It now
reports **0 inconsistencies across 1157 glyphs**.

### Entry ids

Ids are `lz{stream:06X}#{n}`, keyed by stream address rather than by position
in `STREAMS`, so finding more streams cannot renumber existing ones. Migrating
translations across an extraction matches on `(stream, offset)` and verifies
the hex before copying.

## Relocation: remap, do not repoint

Every stream had to fit its original compressed span. The obvious fix - find
each pointer and rewrite it - is unsafe here. Stream addresses are not in a
table; they appear as literals in event code
(`move.l #<stream>,d0 ; jsr ($05402C).l`), as inline longwords after
`jsr ($05402A).l`, and as the first field of area descriptors reached through
`$FFECF8`. A scan turns up ~200 candidate sites, one missed reference crashes
the game, one false positive corrupts data - and `$1D9436` has no findable
reference at all.

So nothing is repointed. The LZSS decompressor is intercepted instead, at the
one place a stream address is actually *used*:

    041BA0  jmp ($0E7300).l    replaces subq.l #2,a7 / move.b (a0)+,(1,a7)

A 50-byte routine looks `a0` up in a 26-entry table, substitutes the new
address on a match, re-executes the two displaced instructions, and returns to
`$041BA6`. All 22 callers of `$041BA0` funnel through it, graphics included;
anything absent from the table passes straight through. Relocation is
therefore independent of how a reference is stored or computed.

Because a relocated stream frees its own span, the arena is the original script
region plus the unused `$FF` blocks:

| | before | after |
|---|---|---|
| headroom | 2 bytes | **68,614 bytes** |

Arena 158,988 bytes, script 90,374. Verified: all 26 streams decompress from
their new addresses to byte-identical content, and 0 bytes changed outside the
intended regions.

### The row "hazard" was not one

An earlier note here flagged `$06A4C6` doing `addq.w #1,d2` unmasked as a
latent bug. It is not. Simulating the original script shows **56 messages
already push past the two-row window**, and originals run to 13 rows, so the
engine handles it as a matter of course. Half-width makes it rarer, not more
likely: at 32 columns text auto-wraps less often than at 16.

What replaces the guard is a measurement. `dialogue.layout()` and the
proofreader's footprint readout report rows used and longest line in half
cells, so a translator can see when a line needs more rows than the original
did - a real constraint, rather than an invented limit.

## 8x8 bank: relocation, and the real width limit

The bank is uncompressed and bounded by anchors, so a translation is capped by
the next anchor rather than by compression. Three translated item names put
segment `2ABF00-2AC4E6` six bytes over, which is what prompted relocating it.

### Anchor detection was wrong twice

`regions.build()` scanned every byte offset for pointers. 68000 operands are
always even aligned, so odd hits cannot be pointers - that alone invented
seven anchors in region 1. Even alignment is still not enough:

    286C26  0000002a    ori.b #$2A,d0

The four-byte window at `286C28` reads `002AC210`, straddling the immediate
`$002A` and the following word. Every region address begins `002A`, so the
pattern recurs. An anchor now requires the preceding word to be an opcode that
takes a 32-bit operand. Region 0 went 8 -> 6 anchors, region 1 went 15 -> 6.

This matters because segments are the spans *between* anchors: a phantom
anchor imposes a size limit the game does not enforce.

### Relocation here does rewrite pointers

Unlike the LZSS streams there is no choke point - text is reached by
`lea (anchor).l,a0` then either the terminator scan at `$05CCB6` or direct
indexing. Rewriting is safe only because every reference is a genuine
instruction operand: 67 of them, all rewritten, into a reserved 22,952-byte
arena (7,514 used).

Three independent checks:

- scanning the WHOLE rom, not just code, for surviving references. All in-code
  hits are the `002A` straddle above, confirmed by disassembly; the rest sit in
  graphics and audio data and point at non-anchor addresses
- **the old text is left in place**, so a missed reference reads the original
  Japanese - a cosmetic regression, not a crash
- 0 bytes changed outside the arena and the rewritten operands

### Width is set by the narrowest menu, not the widest

One byte is one 8x8 cell here, so the byte count is the display width. The
longest name the game ships is 13 cells, which is what the equipment list
allows - but the **item menu** spends cells on an icon and leaves **10**. That
is the binding limit, and it is why 22 of the 160 original names exceed 10:
those never appear in the item menu.

Measuring the data alone gives the wrong answer, because it reports the widest
context an entry can appear in rather than the narrowest. The proofreader now
shows `N cells (was W, limit max(10, W))`: 10 for anything whose original fit
the item menu, and the original length for entries that evidently do not
appear there.

## The name tables, and per-region terminators

Two more 8x8 regions were located, adding 286 entries that no extractor had
ever seen:

| | range | entries | terminator |
|---|---|---|---|
| big | `280CB0-2815D4` | 286 - 11 party, 11 class/vehicle, 152 enemy, 112 battle action | `$FF` |
| small | `2AA1F0-2AA271` | 22 - the party and class names again | `$FF` |

**The terminator is per region.** The two item regions end messages with `$FE`;
these two use `$FF`. That is not inferred from the data alone - the copy loop at
`$0444C4` reads until `$FF` and writes `$FE` only into its RAM copy:

```
0444C4  lea ($2AA1F0).l,a0     ; ROM table
0444CA  lea ($FFF500).w,a1     ; RAM, 11 slots of $80 bytes
0444D6  move.b (a0)+,d0
0444D8  cmpi.b #$FF,d0         ; ROM terminator
0444E2  move.b #$FE,(a3)       ; RAM terminator, written by the copy
```

Counted over the data it is unambiguous: the big table holds 285 `$FF` and zero
`$FE`; the item name region holds 308 `$FE` and zero `$FF`. `REGIONS` entries
are now `(start, end, terminator)` and `build()` returns the terminator, which
`script_io` and `relocate8` both honour. New regions are appended rather than
inserted so region indices - and therefore entry ids - stay stable.

Two traps worth recording, both of which round-tripped perfectly while wrong:

* **The base is `$280CB0`, not `$280CB5`.** Searching the ROM for ライラ hits
  `$280CB5`, because ルディ occupies the five bytes before it. Taking the search
  hit as the base silently drops the first entry - and round-trip still passes,
  since the dropped bytes simply fall outside the region and are never touched.
* **A region can sit inside a CODE range.** The big table does, so the anchor
  scan and `references()` could both take a pointer-shaped run of *text* for an
  operand. Both now exclude sites falling inside a declared region.

Round-trip over all four regions, 827 entries, is byte-exact.

## Retracted: one byte is one cell

The rule "one byte is one 8x8 cell, so the byte count IS the display width"
holds only for unvoiced text. `$F0`/`$F1` are combining dakuten and handakuten
marks and take **no cell of their own**, so a byte count over-measures any name
containing voiced kana.

Correct for that and every table lands exactly on a flat limit:

| table | entries | max cells |
|---|---|---|
| player items | 157 | 10 |
| player techniques | 40 | 5 |
| player skills | 54 | 8 |
| locations | 54 | 10 |
| party names | 11 | 4 |
| enemy names | 152 | 10 |
| enemy skills | 112 | 10 |

Hitting the cap exactly in all seven is what pins them down; they are real
window widths, not the incidental maximum of the data. Checked the other way,
all 613 original entries fit their assigned limit and none exceeds it.

This retracts the earlier `max(10, original)` rule and the argument behind it -
that 22 item names exceed 10 cells and therefore cannot appear in the item menu.
Those 22 exceeded 10 **bytes**; measured in cells they all fit 10, and there is
no exempt set. `proofread.html` still carries the old rule and will mislead a
translator until it is updated.

## `$F2` sub-handler `$00` takes two operand bytes

`F2_SUB_EXTRA` knew about sub-handlers `$03`, `$04` and `$0B`. Sub-handler `$00`
also consumes two bytes, and they were decoding as text - a space plus one kana
glued to the front of a line, visible as ` こ`, ` さ`, ` し` running in gojuon
order through the Birth Valley cutscene.

Read as a big-endian word, the 165 sites hold `$000A..$017F`, 163 of them
distinct, with 97 of the 164 steps exactly `+1`: an id allocated in script
order. The rollover shows up in the old decode too - once the low byte passes
the kana bank the high byte ticks from `$00` to `$01` and the pair prints as
`あル`, `あレ`, `あロ`.

This one bites harder than a cosmetic mis-decode. The bytes round-trip while
they sit in the `jp` string, so extraction looked correct - but a translator
replacing that line drops them, taking 330 bytes of event ids with it. The
failure would present as a hang or a desynced cutscene, not as garbled text.

## ROM expansion: 3 MB -> 4 MB

The ROM is **3 MB**, not the 4 MB usually quoted for this game. The header
agrees: `$1A4` held `$002FFFFF`, and the image is exactly `$300000` bytes.

That matters because the Mega Drive maps cartridge ROM across
`$000000-$3FFFFF`, so **the fourth megabyte was already addressable** — no
mapper, no bank switching, no change to how anything is pointed at. `lea
$3xxxxx.l,a0` worked before this change; there was simply nothing there.

Two premises that had been driving planning are wrong and are recorded here so
they are not re-adopted:

* **The 68000 is not the 4 MB limit.** It has a 24-bit bus and reaches 16 MB.
  The ceiling is the cartridge address decode.
* **There are no 16-bit pointers to widen.** LZSS streams appear as 32-bit
  literals (`move.l #imm,d0 ; jsr ($05402C).l`), as inline longwords, and as
  area-descriptor fields; 8x8 regions are reached by `lea (abs).l`. Messages
  inside a stream are not pointed at all - `$05CCB6` counts terminators. The
  `$041BA0` intercept already relocates streams independently of how any
  reference is stored, which is strictly better than repointing.

### What changed

[`expand.py`](tools/expand.py), driven by `ps4tool.py expand`. Three things:

| | |
|---|---|
| pad | `$300000-$400000`, filled `$FF` |
| `$1A4` | ROM-end longword -> `$003FFFFF` |
| `$18E` | checksum recomputed |

The checksum **did not change**. 1 MB of `$FFFF` words is 524,288 words, and
524,288 is exactly 8 x 65,536, so the 16-bit sum wraps a whole number of times.
Only one byte in the entire image differs: `$1A5`, `$2F` -> `$3F`. The game
reads neither field - there is no boot-time checksum test anywhere in the
disassembly - so both are hygiene.

### Verification

* `rom.bin` vs `rom4m.bin`: **1 byte differs** (`$1A5`), pad is uniform `$FF`,
  stored checksum matches computed.
* `extract` and `dlg-extract` produce **identical** JSON from the 3 MB and
  4 MB images (827 and 2170 messages).
* All **26/26** LZSS streams decompress byte-identically.
* SMD round-trip is exact at 4 MB.
* `expand()` is idempotent.
* A full `en-build` on the 4 MB base produces an image whose **low 3 MB is
  byte-identical to the 3 MB build except `$1A5`** - so the executed code and
  every byte of data are bit-for-bit the same. Expansion is behaviourally a
  no-op.
* **Boots.** Loaded in Exodus, ran through the SEGA logo into the opening
  cutscene at a steady 59-61 FPS with the English narration rendering, which
  also exercises the relocation intercept end to end. Exodus's own cartridge
  module declares `MemoryMapSize="400000"`, independently confirming the
  window size.

### What it buys

`relocate.arenas_for()` clips `ARENAS` to `len(rom)`, so a 3 MB image is
unaffected and only an expanded one is offered the new space. This guard is
not optional: writing past the end of a Python `bytearray` silently **appends**
rather than raising, so an unclipped arena would grow the ROM instead of
failing, and streams would land where the cartridge does not answer.

| | 3 MB | 4 MB |
|---|---|---|
| arena | 136,036 | 1,184,612 |
| free after a full `en-build` | 45,691 | 1,094,267 |
| largest gap | 45,106 | 1,048,576 |

Streams still pack into the original script region first, so nothing moved
above `$300000` - the fourth megabyte is held in reserve rather than being
spent. The immediate use is font data: the English 8x8 bank is currently
Nemesis-compressed to fit a 1,212-byte slot, and `$0E7130-$0E8000` now holds
the half-width routine, the width bitmap, the remap code and table, *and* a
relocated dialogue region. None of that has to stay squeezed.

### Why not 6 or 8 MB

That needs the SSF2 mapper at `$A130F3-$A130FF`, and this game is a poor
candidate. It already drives `$A130F1` to overlay SRAM at `$200001-$203FFF`,
so mapper state would be entangled with save handling; bank state is global
while the game fires DMA from ROM in vblank; and it changes the cartridge type,
which affects flashcart and hardware behaviour. All of that to solve a problem
the measurements say does not exist - see below.

### The script does not need the space

Measured, not estimated. Encoding the 244 translated entries with `english.py`
and compressing with `lzss_enc.py`:

| | Japanese | English |
|---|---|---|
| decoded bytes | 129,555 | 182,202 (projected, x1.41) |
| LZSS ratio | 0.70 | **0.55** |
| compressed | 90,374 | **~99,500** |

English costs 1 byte per character and compresses far better than kanji-heavy
Japanese, and the two effects nearly cancel: **the finished English script
lands at roughly the size of the Japanese original.** The expansion is for
fonts and code, not for text.

### Hazard: the SRAM overlay

SRAM is mapped over `$200001-$203FFF` whenever `$A130F1` bit 0 is set, so reads
there do not reach ROM while a save is in progress, and the enable windows
(e.g. `$044414`) do not visibly mask interrupts. Anything DMA-sourced must stay
clear of that range. Data above `$300000` is clear of it by construction, which
is a second reason to expand rather than keep scavenging the ~95 KB of filler
left below.

### Fixed in passing

`ps4tool.py` re-imported `script_io` inside `main()` for the `en-build` branch,
which made the name local to the whole function and broke `extract` and
`insert` with `UnboundLocalError` on every other path. The local import is
removed; the module-scope one was always there.

### Observed, unrelated: the opening narration overruns the screen

Visible in the boot test - `and Algol tried once again t` is cut off mid-glyph
at the right edge, and several other lines end flush against it. This is a
line-length problem in the translated narration, not an expansion artifact:
the low 3 MB of this build is byte-identical to the 3 MB build. It wants the
proofreader's footprint readout applied to the narration patches.

## The disassembly is the US ROM

`ps4disasm` is the **US** build - `SEGA GENESIS`, serial `GM MK-1307 -00`,
checksum `$5CB`. This project targets the Japanese one - `SEGA MEGA DRIVE`,
`GM G-5524  -00`, `$7667`. They share an engine but not an address map, and the
delta is not constant: the 8x8 name renderer is `loc_27DB9C` in the
disassembly and `$280564` here.

**Use the disassembly for structure, never for offsets.** [`layout.py`](tools/layout.py)
re-derives what it needs by scanning this ROM for instruction patterns.

## Menu geometry is immediates, not tables

`Battle_SetupWindow` at `$2804BE` takes **d1 = width, d2 = height in cells**,
set by `moveq` at each of its 31 call sites. A name's budget is the
displacement of the `lea (d,a1),a1` after the draw - the renderer restores `a1`,
so that displacement alone decides how many cells the name gets.

`layout.fields()` finds two real budgets, and they corroborate the limits
derived earlier from the data alone:

| draw | budget | table |
|---|---|---|
| `$001854` | 5 cells | techniques |
| `$001BE0` | 8 cells | skills |

(A third hit at `$007456` reports 128 cells; that `lea` is a plane row stride,
not a budget. The scan needs a sanity filter.)

### The technique window

Three call sites share one (width, height) pair and must all be patched: the
erase at `$0017BF`, the frame build at `$0017D3`, the copy-out at `$00180F`.
Chrome accounting checks out against the stock ROM - borders 2 + cursor 1 +
indent 1 + TP 3 + name 5 = **12**, which is what all three hold.

**A blanket search for `moveq #12,d1 / moveq #9,d2` hits six sites.** Two of
them (`$001A24`, `$001ABA`) are the *skill* window, which is also 12x9 but has
an 8-cell name and no cost column (1+1+8 = interior 10, so it also fits
exactly). Patching all six would have silently broken it.

`widen_technique(rom, 8)` sets the three widths to 15 and the displacement to
`$10`. Four bytes.

## VRAM survey: battle, technique window open

Read out of an Exodus savestate (`.exs` is a ZIP; `MD1600.VDP - VRAM.bin` is
the full 64 KB, and `MD1600.VDP.Registers.bin` gives the table addresses).
Far more precise than scraping the hex viewer.

| region | address | tiles |
|---|---|---|
| tile art | `$0000-$BFFF` | 1536 |
| plane A nametable | `$C000-$CFFF` | - |
| low font bank `$680-$6FF` | `$D000-$DFFF` | 128 |
| plane B nametable | `$E000-$EFFF` | - |
| sprite table | `$F000-$F27F` | - |
| **gap** | `$F280-$F3FF` | **12** |
| hscroll table | `$F400-$F77F` | - |
| **gap** | `$F780-$F7FF` | **4** |
| high font bank `$7C0-$7FF` | `$F800-$FFFF` | 64 |

The map explains the code-space ceiling exactly: the low bank is 128 tiles
because `$D000-$DFFF` is all that sits between the two nametables, and the high
bank is 64 because `$F800` to the top of VRAM is 64 tiles. Codes `$C0`+ would
address past `$7FF`, which is why they are not glyphs.

**Free space, measured:**

* 103 of 1536 art tiles are referenced by a plane or sprite this frame
* **140 tiles are blank *and* unreferenced** = 4,480 bytes
* plus **16 tiles** of structural gap that no table can ever use
* **156 tiles / 4,992 bytes hard free**
* largest contiguous runs: **71** (`$4ED-$533`), 34 (`$4BA-$4DB`), 16 (`$54C-$55B`)
* `$B000-$BFFF` (the 16x16 dialogue glyph buffer, 128 tiles) holds stale data
  and is referenced by **nothing** during battle - reclaimable, but battle
  messages may want it back, so it is a timing dependency rather than free space

### What that buys a menu VWF

A VWF converts shared glyph tiles into **unique tiles per on-screen cell**, so
the cost scales with visible text, not vocabulary. For the widened technique
window: 4 entries x 8-cell names = **32 tiles**; the whole interior would be 52.
Either fits in the 71-tile run by itself.

VWF tiles need not be contiguous - every cell is an independent nametable entry
- so all 156 are usable; contiguity only decides how many DMAs it takes.
52 tiles is 1,664 bytes, comfortably inside a vblank (~7 KB in H40), and only
on text change rather than per frame.

**Caveat, and it matters.** "Blank now" is not "free always". 1,433 art tiles
are unreferenced this frame but hold art the battle uses as it animates, and
the 140 blank ones could be staging areas filled on demand for spell effects.
The honest test is to sample VRAM at several battle moments - menu open, spell
cast, enemy attack, victory - and intersect the blank sets. One savestate is a
starting point, not a budget.

### Five battle states: the scavenging budget collapses, and a better source appears

Sampling one moment was not enough, as suspected. Running the intersection of
blank-and-unreferenced art tiles as states are added:

| + state | free in all so far |
|---|---|
| battle1 | 140 |
| schnellcast | 69 |
| earthbindcast | 67 |
| rudyattack | **50** |
| victory | 50 |

It converges at 50 - the last state took nothing further - but the **71-tile run
at `$4ED-$533` that looked like the obvious home for VWF cells is spell
animation staging** and is gone the moment anything is cast. What survives all
five is `$4BA-$4DB` (34 tiles) plus about sixteen scattered singles.

`$B000-$BFFF` is also **not** reclaimable: `rudyattack` and `victory` each
rewrite 1,856 of its 4,096 bytes, so battle messages do stage 16x16 glyphs
there. No plane references them in the sampled frames - the references are from
the sprite table - but the buffer is live.

**The font banks are the real answer.** `$D000-$DFFF` is **byte-identical
across all five states**: a static, resident, contiguous 128-tile block that
nothing in battle competes for. And most of it is idle - counting every tile
any plane or sprite references across all five states:

| bank | referenced | resident but unused |
|---|---|---|
| low `$680-$6FF` | 43 of 128 | **85** |
| high `$7C0-$7FF` | 17 of 64 | **47** |

That is the point a VWF turns on: **it does not need a resident alphabet at
all.** Cells are composed from a 1bpp font in ROM and written as finished
tiles, so the bank it replaces becomes its own workspace. Keeping the window
frame codes (`$66-$77`, 18 tiles) resident still leaves **~110 contiguous
tiles at `$D000-$DFFF`**, immune to the animation contention that ate the
scavenged run, with the high bank's 64 available on top if all text moves over.

Against a need of 32 tiles for four 8-cell technique names, or 52 for the
window's whole interior, that is 2-3x headroom rather than the no-margin fit
scavenging offered. **The VWF pays for its own VRAM.**

## Bug: relocate8 rewrites pointers, but not immediates

Symptom: the in-battle item menu lists **GUARDNMAIL** and using it applies
**MONOMATE**. Reproduced and fixed.

Two inline copies of the name lookup do not count terminators from the start.
They skip straight to game index `$50` with a hardcoded **byte** displacement:

```
001F84/003CBA  lea    ($28A659).l,a0    <- rewritten by relocate8
001FC0/003CC0  cmpi.w #$50,d7
001FC6/003CC6  adda.w #$2DD,a0          <- NOT rewritten
001FCA/003CCA  subi.w #$50,d7
001FCE/003CCE  subq.w #1,d7
```

`relocate8` moved the 8x8 bank into the arena and correctly rewrote all 72
pointer operands - including both `lea`s. But `$2DD` is an **immediate**, not a
pointer, so the reference scan never saw it, and it still holds the byte
distance to entry `$50` in the *Japanese* data. English names are 81 bytes
longer over that span, so the shortcut lands short.

Simulating the routine confirms it exactly: game index 125 is MONOMATE, and
with `$2DD` it resolves to `$28AB1B`, which is GUARDNMAIL. **180 of 260 item
indices were wrong** - every item from `$50` up. Below `$50` the low path
counts terminators normally, which is why the bug is invisible in the early
game.

The fix recomputes the displacement from the actual data
(`layout.correct_item_disp`), giving `$32E`. All 260 indices then resolve to
the same entry ordinal as the stock ROM. It is wired into `en-build`, because
**hardcoding `$32E` would only move the bug**: the value is the encoded length
of the first 79 names and changes whenever any of them is edited.

**One deliberate deviation.** In the stock ROM `base+$2DD` is `$2AC1DD`, which
is two bytes *past* the start of ordinal 79 (`$2AC1DB`). For any index above
`$50` that is invisible, since the scan's first act is to run to the next
terminator, which absorbs the offset - so it only affects index `$50` itself,
whose name the Japanese ROM renders two characters short. There is no faithful
English analogue of "skip two bytes of a different string", so the fix points
at the entry start, which incidentally repairs index `$50`.

**The bug class matters more than the bug.** Any hardcoded offset into
relocated data has this property. A sweep of all 52 `lea (arena).l` sites for a
following `adda.w #imm` finds only these two, and no `$2DD` immediate survives
anywhere in the ROM - but the same check should be re-run whenever a new region
is relocated.

### Assurance, not just a fix

Calling `fix_item_disp()` from `en-build` makes the fix *run*. It does not make
it *guaranteed* - `relocate8` can be driven directly, a future path can forget,
and the failure is silent below index `$50`. What makes it an assurance is
`layout.verify_lookups(stock, built)`, wired into `en-build` as a hard gate.

The invariant: relocate8 never moves code, so for any code offset that loads a
name-table base, `base + displacement` must resolve to the **same entry
ordinal** in the built ROM as in the stock one. That is exactly what `$2DD`
violated, and the check does not care why an offset went stale.

Proven in both directions:

| ROM | result |
|---|---|
| `ps4en_4m_tw.bin` (unfixed) | **FAIL** - "names will be 8 entries out", at both sites |
| `ps4en_4m_tw_fix.bin` | clean |
| `ps4en_4m_full.bin` | clean |

and with `fix_item_disp` deliberately stubbed out, the build **printed the
diagnostic, refused to write the ROM, and exited 1**. A gate never seen to
fail is not a gate.

### The durable option: delete the shortcut

Recomputing the displacement manages the hazard. Removing it ends the hazard.

The shortcut exists only to skip the first 79 terminator scans. Forcing the
`blt` at `$001FC4` / `$003CC4` to an unconditional `bra` (**one byte each**,
`$6D` -> `$60`) sends every index down the counting path, after which
`adda.w #$2DD` is dead code that can never go stale again.

Verified: with the shortcut disabled, **every valid index (0-309) resolves to
the same ordinal as stock**. The disagreements begin at 310, past the table's
308 entries, where both walks run off the end and saturate.

The cost is real but small and bounded: the shortcut saves at most 79 entries
of scanning, roughly 800 bytes at ~18 cycles a byte, so ~14k cycles per name
drawn - about 0.1 frame. An eight-row item list pays ~1.5 frames once, on menu
open, not per frame.

Current default is recompute-plus-gate, which is free and now verified. Delete
the shortcut if the gate ever feels like something that has to be remembered.

## Menu VWF, step 1: the face

### The renderer's interface contract

Read off `$280564`, and it constrains the design more than expected:

```
28055A  movem.l d2/d3/d7/a0/a1,-(a7)   ; entry B, forces d0 = $E000
280564  movem.l d2/d3/d7/a0/a1,-(a7)   ; entry A, caller supplies d0
280568  moveq  #0,d2 / move.b (a0)+,d2 ; a0 = text
28058C  move.w d2,(a1)+                ; a1 = nametable dest, one WORD per cell
280590  movem.l (a7)+,d2/d3/d7/a0/a1   ; a0 and a1 RESTORED
280594  tst.w ($FFF43C).w / bsr $2805E6
```

* in: `a0` text, `a1` nametable destination, `d0` attribute, `d1` dakuten flag
* terminator is any byte `>= $FE`
* `d2/d3/d7/a0/a1` are saved and restored - which is precisely why the caller's
  `lea $A(a1),a1` arithmetic works
* two entry points, and a `$FFF43C` post-step that must survive

**The hard constraint:** callers position columns as byte offsets from the
name's start, so a VWF must still consume WHOLE nametable cells. It buys
narrower pixels *within* a cell budget, not fractional cells.

Call-site counts, which set the size of each job:

| routine | callers |
|---|---|
| renderer `$280564` | **9** |
| canonical lookup `$05CCB6` | 15 |
| base dispatcher `$28081E` | 10 |
| inline lookup copies | 2 |

So replacing the renderer is a 9-site job and replacing the addressing is a
27-site job. They are independent; the renderer is much the smaller.

### The value is in the font, not the renderer

Measured over the 304 translated item names:

| face | mean cells | max | saving |
|---|---|---|---|
| fixed 8 px (today) | 8.3 | 10 | - |
| VWF over `lowerfont.SMALLCAP` | 7.4 | 9 | **11%** |
| VWF over `lowerfont.NARROWCAP` | 4.8 | 7 | 42% |
| VWF over the new face | **5.4** | **7** | **35%** |

SMALLCAP is a near-uniform 6 px, so a VWF over it barely pays - 11% would not
justify the work. NARROWCAP reaches 42% but those forms were authored for
ligature interiors, where legibility is carried by the pair; standalone, its
1-px `i` is a stray dot.

[`vwffont.py`](tools/vwffont.py) is a standalone proportional small-caps face
at the same metrics (5 rows, top row 3, baseline row 7), widths 1-6 px, and it
lands at **35%** - the range originally hoped for. It covers every character
the current translations use, with nothing missing.

The number that matters for the ligature problem: item names fitting the old
5-cell technique budget go from **40 to 135** of 304.

`work/vwf_preview.png` renders it against the current fixed face with cell
boundaries marked.

### Correction: class names are an 8-cell field, not 4

The budget table elsewhere in this file lists party names at 4 cells. The
**class/vehicle** names share region 2 with them but are a separate 11-entry
set with their own, wider field. Derived the same way as every other budget -
from the widest original - the Japanese entries run to **8** cells (MOTAVIAN
and LANDMASTER are both 8). Assuming they inherited the party 4 was wrong and
made six English names look over-budget when they are not.

### Every table fits under the VWF

| table | budget | n | fixed 8px | VWF |
|---|---|---|---|---|
| player items | 10 | 156 | max 10, 0 over | max 7, **0 over** |
| techniques | 8 | 40 | max 9, 2 over | max 6, **0 over** |
| skills | 8 | 54 | max 10, 2 over | max 6, **0 over** |
| locations | 10 | 54 | max 10, 0 over | max 7, **0 over** |
| party names | 4 | 11 | max 6, **5 over** | max 4, **0 over** |
| class names | 8 | 11 | max 10, 3 over | max 7, **0 over** |

Party names are the headline: five of eleven exceed four cells at fixed width,
which is the entire reason the creep glyphs exist. Under the VWF the longest is
exactly 4, and none is over.

**That retires 55 of the 82 codes `slotmap` assigns** - 30 technique ligatures
and 25 party creep glyphs - and with them the whole packing policy in
`slotmap.pack()`. Text composed from a ROM face needs letters, digits and
punctuation, roughly 45 codes, and no pairs at all.

Two honest limits on this result:

* **Party names fit at exactly 4 of 4.** There is no margin. Any longer party
  name, now or later, breaks it and there is no ligature fallback left once the
  creep glyphs are gone.
* **Enemy names (152) and enemy skills (112) are not translated yet**, so 264
  of the 580 names are untested against this. Both budgets are 10 and the
  translated 10-cell tables top out at 7, so the projection is comfortable -
  but it is a projection.

## Menu VWF, step 2: the composer

### Colours were already decided

The stock 8x8 font tiles use `$E` for paper and `$F` for ink - confirmed by
histogramming the whole low bank out of a VRAM capture (5746 `$E`, 1966 `$F`,
almost nothing else). That is the same convention as the dialogue expander at
`$06AA30`, so composed tiles need no palette work to match. The capture also
confirms the metrics: code `$01` is small-cap `a` on rows 3-7, exactly
`lowerfont.SMALLCAP`.

### Where it lives

| what | where | why |
|---|---|---|
| font table | `$300000`, 2048 B | fourth megabyte, clear of the SRAM overlay |
| composer | `$300800`, 104 B | same |
| 1bpp scratch | `$FF5800`, 60 B | see below |
| 4bpp tiles | `$FF5880`, 384 B | 12 cells |

Entries are **8 bytes**, not 6 - width plus five 1bpp rows plus padding - so a
code indexes with `lsl #3` instead of a `mulu`. The routine runs per character
and a multiply is 38+ cycles against 8 for a shift; the 1 KB wasted is
meaningless in a spare megabyte. The table is flat across the whole byte range,
so lowercase (`$01-$1A`), the stored uppercase (`$80-$99`) and digits all index
the same glyphs with no mapping logic - the face *is* small caps.

**RAM choice.** `$FF5341-$FF5FFF` is quiet in all eight captured savestates -
five battle moments, the opening cutscene and two idle states, across both the
Japanese and English builds - and the disassembly declares no symbol inside it:
nearest are `Sound_Index` (`$FF500A`) below and `Chunk_Table` (`$FF6000`)
above. Basing at `$FF5800` leaves ~1.2 KB of margin below in case the sound
driver reaches further than those states show. This is evidence, not proof; the
honest test is a write-watchpoint over a long session.

### The routine

104 bytes. One glyph row is a byte with the leftmost pixel in bit 7, so placing
it at an arbitrary x means shifting it into a 16-bit window - `byte << 8` then
`lsr` by `(x & 7)` - after which the high byte belongs to `scratch[x >> 3]` and
the low byte to the cell after it. Everything else is bookkeeping.

### It was executed, not just read back

Existing practice here was to assemble a routine, disassemble it and read it
back. That catches encoding slips but not logic, which is why the half-width
patch is still recorded as never having run. [`emu68k.py`](tools/emu68k.py) is
a small 68000 interpreter covering only the instructions these patches use -
it raises on anything else rather than guessing, because a silent wrong decode
would give confident wrong verification.

Running the **assembled bytes** against `vwffont` as the oracle:

* **348 of 348** real translated names render **pixel-exact**, with matching
  widths. 0 mismatches.
* worst case **742 instructions** per name - roughly 7k cycles, about 0.06 of
  a frame, and four names to a menu.

Edge cases, all correct:

| case | width | consumed | scratch spill |
|---|---|---|---|
| empty (terminator first) | 0 | 1 | no |
| narrow `i` / wide `m` | 1 / 6 | 2 | no |
| space | 3 | 2 | no |
| leading + trailing space | 12 | 4 | no |
| undefined code `$7F` | skipped, no advance | 3 | no |
| `$FE` terminator | 4 | 2 | no |
| 11 cells of `m` | 83 | 13 | **no** |

The empty case is the one that mattered: without the `tst.w d3 / beq` guard it
would return width -1, since the routine subtracts the trailing gap.

Finding the emulator's own bug first was instructive - it trapped on
`lsl.w #3,d2` because the shift mask was wrong, not the composer. A verifier is
code too.

**Not yet wired in.** The composer produces 1bpp; still to come are the 1bpp ->
4bpp expansion, the tile pool against the ~110 tiles at `$D000-$DFFF`, the DMA,
and the nametable writes that replace `$280564`.

## Menu VWF, step 3: expansion, and the pool decision

### Pool: per window, not per screen cell

Keying tiles by nametable position needs no allocator state and makes redraws
idempotent, but it costs a tile for every screen cell that could **ever** hold
VWF text - across all menus that is far past the 110 available.

So the pool is scoped **per window**, reset at the window-build call site,
which is already a place this project patches (the technique widening touches
three such sites). The technique window needs 4 names x 7 cells = **28 tiles**
against 110, with the reset making reuse trivial.

That has a second consequence worth stating: this adds a **new** renderer used
only by converted call sites rather than replacing `$280564` globally. The
other eight callers keep working untouched, so conversion is window by window
and each step is separately testable. A global swap would have made the first
broken menu indistinguishable from the ninth.

### The expander

78 bytes at `$300900`. Rows 0-2 of every tile are paper - the face sits on rows
3-7, matching the stock font, so converted and unconverted text share a
baseline.

Expansion is a **1 KB lookup table** (`$301000`, byte -> eight nibbles) rather
than a bit loop: one table read is ~12 cycles against roughly 100 for shifting
nibbles out individually, and the table costs nothing in a spare megabyte.

### Verified by execution, again

`emu68k` grew three more encodings and ran the **assembled bytes** of both
routines back to back over all 348 translated names, comparing the finished
4bpp tile bytes against an independent oracle built from `vwffont`:

* **348 of 348 byte-exact.** 0 mismatches.
* worst case **1085 instructions** for compose + expand together - roughly
  11k cycles, under a tenth of a frame, and four names to a menu.

`work/vwf_tiles.png` is decoded straight from the tile bytes the 68000 produced
under emulation, not from the Python face - so it is a picture of the actual
output, not of the intent.

### Installed

`work/ps4en_4m_vwf.bin`:

| | address | bytes |
|---|---|---|
| font table | `$300000` | 2048 |
| composer | `$300800` | 104 |
| expander | `$300900` | 78 |
| expansion table | `$301000` | 1024 |

Nothing below `$300000` changes. Still to come: the tile pool and its reset,
the DMA queue call, and the nametable writes.

## Menu VWF, step 4: the renderer

`$300A00`, 104 bytes, plus a 10-byte pool reset at `$300B00`. Contract matches
`$280564`: `a0` text, `a1` nametable destination, `d0` attribute, and it saves
d0-d7/a0-a5 - a superset of the original's d2/d3/d7/a0/a1, so a caller's
`lea $A(a1),a1` arithmetic is untouched.

Flow: compose -> expand -> allocate -> queue DMA -> write nametable words.

`$0420D6` turned out to take a **plain VRAM address in d1**, not a pre-built
command - it does the `andi/ori/rol` itself - and it saves d0-d3/a0. Reading
that rather than trusting the earlier summary removed a whole block of
command-building code.

### Nothing live may cross a call

The composer uses **d1-d7** and a2/a3; the expander uses **d0-d5** and
a2/a3/a4. Between them almost every register is volatile. So the attribute
rides the stack across the composer and returns in d6, the cell count lives in
d7, the tile index is read only *after* the expander runs, and the nametable
pointer sits in a5 above everything either routine touches.

Three bugs were found by executing it, none of which reading would have caught,
and all three were **silent**:

| bug | symptom |
|---|---|
| `POOL_NEXT` at `SCRATCH+0x100` sat inside the 384-byte tile buffer | expander overwrote the allocator with `$EEEE` |
| nametable pointer parked in a4, which the expander clobbers | every write went to a stale pointer; no text at all |
| attribute in d6 and tile index in d5, both clobbered | right glyphs, wrong palette, wrong tiles |

Each register contract was already written in the docstring of the routine that
violated it. Documenting a contract is not the same as honouring one, and only
running the code told the difference. `check_layout()` now asserts the RAM
blocks cannot overlap, since that class of bug deserves a permanent guard
rather than a comment.

### Verified

Whole pipeline executed per name over all 348 translated names, checking DMA
parameters, nametable words, finished tile bytes against the `vwffont` oracle,
and register restoration:

* **348 of 348 correct**, 0 failures
* worst case **1148 instructions** end to end - roughly 12k cycles, about a
  tenth of a frame, four names to a menu
* pool exhaustion: the fifth 7-cell name is **refused**, drawing nothing and
  leaving the nametable untouched, rather than wrapping onto live tiles
* empty string: no DMA, no allocation, no nametable write
* `a0`, `a1` and `d0` restored on every path

### The pool's weak link, stated plainly

The pool is tiles `$4BA-$4D9`, borrowed from the art region because the low
font bank is still the live alphabet for the eight unconverted callers - in
battle the party status bar sits beside the technique window using it. Those 32
tiles rest entirely on the five-savestate survey. **Once a second window
converts, the pool should move into the freed low bank and that dependency
disappears.** It is isolated to two constants for exactly that reason.

### Installed, and still inert

| | address | bytes |
|---|---|---|
| font table | `$300000` | 2048 |
| composer | `$300800` | 104 |
| expander | `$300900` | 78 |
| renderer | `$300A00` | 104 |
| pool reset | `$300B00` | 10 |
| expansion table | `$301000` | 1024 |
| RAM | `$FF5800-$FF5A02` | 514 |

Nothing below `$300000` changes, so the ROM still behaves exactly as before -
no call site points at the new renderer yet. That last step is one `jsr`
redirect at `$001854` plus a reset call in the window build, and it is the
first change that can affect a running game.

## Menu VWF, step 5: wired

Two redirects, **8 bytes below `$300000`** (two of them the checksum):

| offset | was | now |
|---|---|---|
| `$001857` | `jsr ($280564).l` | `jsr ($300A00).l` - the VWF renderer |
| `$0017DF` | `jsr ($041C70).l` | `jsr ($300B10).l` - the trampoline |

There is no room to *insert* a pool reset in the window build; every byte is
spoken for and shifting code would move every later branch target. So the
build's existing `jsr ($041C70).l` is redirected to a trampoline that rewinds
the pool inline and continues to `$041C70` by `jmp`. Its own `rts` returns to
the original caller, the stack stays balanced, and `$041C70` sees exactly the
registers and stack it saw before, because the reset touches neither.

### The post-step, nearly dropped

The stock renderer ends with `tst.w ($FFF43C).w / bsr $2805E6` **after**
restoring a1. That routine re-skins the window-frame tile one plane row above
the name - `$E6F1/F2/EF` to `$E19D/9E/9B` - and only in vehicle battles.
Omitting it would have left the wrong frame corner in Landmaster and Hydrofoil
fights and nowhere else: a bug that surfaces months later in one specific
encounter. The VWF renderer now performs the same test and call. Verified both
ways: flag clear, `$2805E6` is not called; flag set, it is called exactly once.

### Verified against the wired ROM

Loading `work/ps4en_4m_vwf.bin` into the interpreter and running the real
installed bytes - trampoline, then four draws at the window's actual row
offsets (`$82`, `$182`, `$282`, `$382`, plus the 2-cell cursor indent):

```
SCHNELL   E4BA E4BB E4BC E4BD E4BE
SHIFTA    E4BF E4C0 E4C1 E4C2
FEUER     E4C3 E4C4 E4C5
MEGID     E4C6 E4C7 E4C8
```

Pool rewound to `$4BA` by the trampoline, 15 of 32 tiles used for four names.
`work/vwf_window.png` is rendered from the simulated nametable and VRAM, so it
is a picture of what those nametable entries actually point at.

Also still true after wiring: the 348-name sweep passes with the post-step in
place, and `layout.verify_lookups` is clean.

### What emulation cannot tell us

Everything above is functional correctness. Three properties remain untested
and all three need Exodus:

* **DMA timing.** Each name queues its own transfer. Four per window is well
  inside a vblank on paper, but the queue is shared and nothing here proves it
  is not overrun.
* **Pool safety.** Tiles `$4BA-$4D9` rest on the five-savestate survey. If the
  battle loads art there during an animation the text corrupts.
* **Reset placement.** The trampoline fires wherever `$041C70` was called from
  in the window build. If that call happens more or less often than once per
  window, the pool rewinds at the wrong time.

## The deferred-DMA bug, and why the harness missed it

**Symptom:** every row of the technique window showed fragments of the LAST
technique. FEUER, drawn third, appeared in rows 1 and 2 as well.

**Cause:** `$0420D6` only *queues* a transfer - the copy happens in vblank. All
four draws composed into one shared staging buffer at `$FF5880`, so by the time
the queue drained, that buffer held only the last name. Each queued DMA then
copied FEUER's bytes to its own destination, stretched over however many tiles
that row had claimed.

**Fix:** the tile buffer is now **one slot per pool tile**, 1024 bytes, and each
draw expands into the slice matching the tiles it just allocated. That forced a
reordering - allocation now happens BEFORE expansion, because the destination
depends on which tiles were claimed - which in turn changed what has to survive
which call. The expander takes its destination in `a1`; the DMA source address
rides the stack across it.

**Why verification missed it.** The harness stubbed `$0420D6` and performed the
copy *immediately*. That is not what the hardware does, and the difference is
precisely the bug. Emulating the call but not its deferral made a queue look
like a memcpy.

The harness now models it properly: `on_pc` appends to a queue and nothing moves
until an explicit `vblank()`. Re-run under those semantics the three sources are
distinct - `$FF5880`, `$FF5920`, `$FF59A0` - and every row shows its own name.

The general lesson is worth keeping: **an emulator verifies the model you gave
it.** Three earlier bugs were caught because the model was faithful about
register contracts. This one survived because the model was unfaithful about
timing. A stub that is more convenient than the hardware is a stub that hides
the bugs that matter.

### State after the fix

* 348-name sweep on the wired ROM, deferred queue: **0 failures**
* worst case **1160 instructions** per name
* **8 bytes** changed below `$300000` (two of them checksum)
* `layout.verify_lookups`: clean
* RAM `$FF5800-$FF5D02`, 1282 bytes - still inside the surveyed quiet region,
  which ends at `$FF5FFF`

## The allocator was the wrong shape

**Symptom:** each row showed its own name but with cells missing - SCHNELL as
"SLL", SHIFTA as "SHIF", FEUER intact. Other characters' shorter lists looked
fine.

**Cause:** the bump allocator needed rewinding once per window, and the reset
was not reliably firing there. The pool filled, and because a refused draw is
all-or-nothing, LONG names were rejected while short ones still fitted - and a
refused row keeps whatever stale nametable entries were already in the buffer.
That is exactly SCHNELL dropping out while FEUER survived, and exactly why a
list viewed earlier looked right.

**Fix: delete the allocator.** The four rows of the window sit 256 bytes apart,
so `(a1 >> 8) & 3` is a distinct slot per row and each row owns a fixed 8-tile
slice. No state, no reset, no trampoline, and redraws are idempotent no matter
how often or in what order the window rebuilds. The slot is a hash, not a row
number - all that matters is that four rows map to four different slices.

This also removed the second live-code change: **the patch is now a single
redirect**, 5 bytes below `$300000` including the checksum.

### The same mistake, three times

The slot was first computed *before* calling the composer, which uses d1-d7 and
promptly overwrote d6 with a shift count - the tile index came out as 6 instead
of `$4C2`. That is the third bug in this routine of exactly one kind: a value
living in a register across a call that clobbers it. The routine's own docstring
says "nothing live may cross a call".

Writing the rule down did not prevent breaking it. What caught it every time was
running the code - and specifically, tracing d6 instruction by instruction, which
took about a minute once I stopped reasoning about what the code should do and
looked at what it did.

### Verified

* **348 names x 4 row slots = 1392 draws, 0 failures** - DMA parameters, tile
  bytes against the `vwffont` oracle, nametable words, register restoration
* **idempotent**: correct after 1, 2 and 22 consecutive rebuilds
* worst case **1161 instructions**
* 0 names refused - nothing the face produces exceeds an 8-tile slice
* `layout.verify_lookups` clean; RAM `$FF5800-$FF5D02`, inside the surveyed
  quiet region

### What is still unproven

The pool is tiles `$4BA-$4D9`, resting on the five-savestate survey. That has
not changed and is now the last untested assumption - if the battle loads art
there during an animation, the text corrupts. The fix, once a second window
converts, is to move the pool into the freed low font bank.

## Root cause: the text still contained ligatures

The savestate settled it. The renderer was working; the **data** was wrong.

`slotmap.pack()` encodes technique names with ligature and creep codes to
squeeze them into the old 5-cell budget:

```
86 09 2a 15 27  =  G i [fe] u [er]   "Gifeuer"
91 01 17 21 27  =  R a  w  [at][er]  "Rawater"
```

The VWF font has no glyph for codes `$1C-$39`, so it gave them **width 0** and
skipped them silently. "Gifeuer" rendered as "Giu", two cells instead of four.
That is why the same picture survived two completely different allocator
designs: neither allocator was ever the problem.

**Fix:** tables drawn by the VWF are encoded as plain letters. Removing the
pairing is the entire point of the VWF, and the renderer simply cannot draw the
pairs. `english8.VWF_SEGMENTS` is set from `vwfpatch.VWF_SEGMENTS` inside
`en-build`, so the encoder and the renderer take the converted-table list from
one place and cannot drift apart again. `en-build` also refuses to write if any
converted name exceeds its 8-tile slice.

Cost: 40 technique names go from 195 bytes paired to 247 plain, against 12,719
free in the arena. Widest name **6 cells of 8**.

### What the savestate showed, and what it corrected

| assumption | reality |
|---|---|
| window buffer at `$FFFF3900` | rows at `$FF068E`, `$FF078E`, `$FF088E` |
| rows 256 bytes apart | confirmed |
| slot = `(a1 >> 8) & 3` distinct per row | confirmed - slots 2, 3, 0, matching VRAM exactly |
| pool tiles clobbered by the game | **no** - they held exactly what the renderer put there |

Both allocator designs were sound. The 256-byte row spacing meant the slot hash
worked regardless of the base I had wrong, which is why that assumption never
surfaced as a symptom.

### The lesson about the harness

Every emulation run fed the renderer text I encoded myself, with the font table
I wrote, so ligature codes never appeared. The oracle and the input came from
the same place, and a test whose input never exercises the failing case cannot
fail. Reading names **out of the built ROM** - which is what finally reproduced
it - should have been the test from the start.

## True capitals, and a lowercase set

### The format change was free

The font entry was `[width, 5 rows, 2 padding]`. It is now `[width, 7 rows]` -
same eight bytes, same 2 KB table. Glyphs occupy cell rows 1-7, row 0 is always
paper, and the baseline stays on row 7 so converted and unconverted text still
share a line.

Three alphabets now share the byte range, and the renderer needs no case logic
at all - the encoder picks the code and the glyph follows:

| codes | set | rows |
|---|---|---|
| `$01-$1A` | small caps (unchanged) | 3-7 |
| `$1C-$35` | **true lowercase** | x-height 4-7, ascenders from 2 |
| `$80-$99` | **true capitals** | 2-7 |

`$1C-$35` are the codes the ligature set used to occupy. The VWF made pairing
unnecessary, and that is precisely what freed the room for a third alphabet.

### Capitals

Six rows against the small caps' five, and **1 px wider on average** (0-2, mean
1.0) - enough to read as a capital beside small caps without the size jump the
stock 8x8 uppercase would give.

They cost nothing to adopt: `slotmap._code` already maps uppercase to `$80+`
and lowercase to `$01+`, so technique names picked up capitals with **no
encoder change at all**. Widest technique name went from 6 to 6 cells of 8;
one name gained a cell.

### Lowercase, and what party names still need

`vwfcase.LOW` has no descenders. The cell ends at row 7, and dropping the
baseline to make room would misalign every glyph against text that is not
converted; `lowerfont` reached the same conclusion for the fixed-pitch bank.
g j p q y sit on the baseline.

Mixed-case party names measure **4 cells against a 4-cell budget** - they fit,
with nothing to spare.

**They are not wired up, and cannot be until their draw sites are converted.**
Party names are still encoded with creep glyphs (`$3A-$52`), which the VWF font
gives width 0, so drawing one through the VWF renderer today produces nothing
at all - the identical failure the ligature codes caused. Feeding all 348 names
through the renderer surfaces exactly 22 such refusals, all of them party and
class entries.

That is the same lesson twice: **converting a table means converting its
encoding, not just pointing the call site somewhere new.** The build already
enforces it for VWF segments via `english8.VWF_SEGMENTS`; party names simply are
not in that set yet.

### Verified

* 204 draws (40 technique + 11 mixed-case party, across all four row slots):
  **0 failures**, tiles compared against a glyph-map oracle
* worst case 1314 instructions
* item-lookup gate clean

## Converting the rest: the tile budget decides the order

All nine callers of `$280564`, and what each draws:

| site | draws | source |
|---|---|---|
| `$001854` | techniques | `$2AC4E6` |
| `$001BE0` | skills | `$2AC5D6` |
| `$001FF2`, `$003CF2` | items (field menus) | `$2ABF00`, via the `$2DD` shortcut |
| `$004DA8` | battle item list | RAM |
| `$004DEC` | dispatched battle text | RAM |
| `$005048`, `$005094` | enemy / target names | RAM |
| `$007456` | field text | RAM |

### Mutually exclusive windows cost nothing

Techniques and skills are alternative battle commands - never on screen
together - and both draw into the same buffer at the same row addresses, with
the same `cmpa.l #$FFFF0700,a1` bound and the same `lea (130,a3),a1` row
layout. The destination-derived slot hash therefore hands them **the same
tiles**, and converting skills cost **zero VRAM**.

That generalises: the battle item list is a third alternative sub-window, and
the field item menus are never up during battle. Every mutually exclusive menu
can share one 32-tile pool.

What genuinely needs its own tiles is text visible *at the same time*: the
party status bar, enemy names, and battle messages.

### The budget, honestly

| | tiles |
|---|---|
| free in all five battle states | 50 |
| structural gaps | 16 |
| **usable now** | **66** |
| committed to the shared menu pool | 32 |
| **remaining** | **34** |

The low font bank would add 110 more, but only once **every** caller is
converted - any unconverted one still needs the resident alphabet, so the bank
cannot be reclaimed incrementally.

That fixes the order:

1. the mutually exclusive menus (techniques done, skills done, items next) -
   free
2. party names, 5 slots x 4 cells = 20 tiles of the remaining 34
3. enemy names and battle messages - these need the low bank, so they come
   last, together, and unlock it as they land

### Skills

Wired at `$001BE2`. Skill names were already encoded plain, so no encoding
change was needed; `'00:003'` joins `VWF_SEGMENTS` so the build still checks
the width. 54 names, widest **6 cells of 8**.

### Correction: items are NOT free

The claim that every mutually exclusive menu can share the technique pool was
right about *when* windows are visible and wrong about *where* they draw. Two
independent problems, both fatal to the current slot scheme:

**The field item sites draw at column offsets inside one row.** `a1` is
`$FFFF0600` plus a byte from the table at `$002034` - `$08 $20 $14 $14 $20 $00`
- so six different positions all sit within the same 256-byte row and
`(a1 >> 8) & 3` maps **all six to slot 2**. Total collision.

**The battle item list has five rows**, `$FFFF0516` stride 256, so slots come
out `1 2 3 0 1` and rows 0 and 4 collide.

Fixing either needs more slots, and there is nowhere to put them:

| | tiles | |
|---|---|---|
| 4 slots x 8 | 32 | fits the 34-tile contiguous run |
| 5 slots x 8 | 40 | does not fit |
| 8 slots x 8 | 64 | does not fit |
| 8 slots x 7 | 56 | does not fit |

The pool must be contiguous - the slot index is `POOL_START + slot * 8` - and
the largest contiguous free run in the art region is **34 tiles**. Techniques
and skills fit because they are four rows in one buffer; nothing else is.

### The chicken-and-egg, and how it breaks

Everything further needs the low font bank's 110 contiguous tiles at
`$D000-$DFFF`, and the bank only frees once **every** caller is converted,
because any unconverted one still needs the resident alphabet.

So the remaining work cannot be incremental. It is one step: convert all seven
remaining call sites and move the pool to the low bank together.

The budget for that step is comfortable, and it is comfortable *because*
player menus and battle notifications are never on screen at the same time -
so the pool needs the widest single window plus whatever is permanently
visible, not the sum of everything:

| | slots x tiles | |
|---|---|---|
| widest single window (battle item list) | 5 x 8 | 40 |
| party status bar, always visible | 5 x 4 | 20 |
| **total** | | **60 of 110** |

Techniques and skills stay as they are until that step, drawing from the art
region, and move to the low bank with the rest.

## A condensed face for party names

**Current implementation:** party names are composed with the standard menu
VWF.  They consume only their actual ink width (2-4 transient pool cells per
name).  The 32x8 strip experiment was not wired because a fixed four-cell
strip increases, rather than reduces, live VRAM demand.

The creep glyphs pack two condensed letters into one fixed cell. What gives
party names their texture is not the pairing - it is that every letter is
narrow and tightly set. The pairing was only ever the mechanism for fitting
four cells.

[`vwfcreep.py`](tools/vwfcreep.py) keeps the texture and drops the mechanism: a
condensed alphabet at natural widths, drawn standalone. Capitals average 1.0 px
narrower than the normal VWF face, lowercase 0.8 px. Same metrics - baseline
row 7, capitals from row 2, x-height 4-7 - so party names sit on the same line
as everything else.

It also buys margin, which the normal face does not have:

| face | widest party name | budget |
|---|---|---|
| normal VWF | 4 cells | 4 |
| **condensed** | **3 cells** | 4 |

Six of eleven names drop a cell against the normal face. That matters more than
it sounds: at 4/4 any future party name breaks the field, and there is no
ligature fallback left once the creep glyphs are retired.

`work/vwf_creep.png` compares all three - today's pairs, the normal face, and
the condensed one.

**Not wired.** Party names need their own tile pool (they are the one thing
permanently on screen), and that pool does not exist until the low font bank is
reclaimed.

## Creep, set proportionally

An earlier comparison here rendered the creep column from `lowerfont.PARTYLIG`,
which holds only six bespoke pairs - everything else falls through to
`ligature()`, so the picture was mostly empty and not a fair comparison. The
real glyphs are in [`creepfont.py`](tools/creepfont.py) (creep, by romeovs, MIT).

### The letters were already there

`creepfont` stores creep as PAIRS baked into 8x8 cells at fixed x=0 and x=4, so
every individual letterform is present and only needs splitting out. That
recovers **22 letters** - F H L P R S T a d e h i j k l m n o r s u y - and,
checked across every pair containing them, **no letter disagrees with itself**.
The split is lossless, and those 22 cover every letter the eleven current party
names use.

[`vwfcreep.py`](tools/vwfcreep.py) does the split and sets them proportionally.

### Tracking is zero, not one

Creep letters span all four columns of their slot with no side bearings - its
spacing is inside the glyph. Setting it with the 1 px gap the rest of the VWF
face uses makes it **wider** than the fixed pairs it replaces:

| rule | widest party name |
|---|---|
| fixed pairs (today) | 3 cells |
| proportional, gap 1 | 4 cells |
| proportional, gap 2 | 5 cells |
| **proportional, gap 0** | **3 cells** |

`creepfont`'s own warning that trimming bearings made `n` read as `r` is the
same fact from the other side: there are no bearings to trim.

### What it actually buys, honestly

**Not cells.** At gap 0 the eleven names total 27 cells either way, and the
widest is 3 in both. Creep at 4 px packed two per cell is already as dense as a
4 px face gets, and the narrow letters (T i j l) do not save enough to cross a
cell boundary.

What it does buy:

* **freedom from pairing** - a name no longer has to decompose into pairs that
  exist as glyphs, so any name works from the 22 letters
* **25 codes back**, since the pair glyphs are retired
* the look kept exactly, including creep's baseline on row 6 and the true
  descender on y that keeps Pyke from reading as Puke

Creep keeps its own vertical metrics, one row above the small-caps baseline.
Party names therefore sit 1 px higher than other text - which is already true
on screen today.

## Items, and the reset that was wrong all along

### Every draw site is preceded by a window build

`Battle_SetupWindow` (`$2804BE`) is called before **all nine** renderer call
sites, 98-400 bytes earlier in the same routine. That is the per-window reset
point the first design needed and never had: it hooked `$041C70`, which is not
the window build, so the pool drifted across redraws until long names were
refused while short ones survived.

That finding makes window geometry irrelevant. Sequential allocation handles
rows, columns, pages and any entry count uniformly, and it packs far better
than fixed slots because a string takes only the tiles it needs.

Two attempts to derive each window's geometry from the disassembly were wrong -
first the technique buffer base, then the battle item list's row count. The
destination-derived slot scheme depended on getting that right every time.
Sequential allocation does not depend on it at all.

Wired: **5 draw sites** (techniques, skills, both field item menus, the battle
item list) and **5 pool resets** at their window builds.

### The budget, measured

Item names are much wider than techniques or skills - mean **7.6 cells**,
max 8 - because they are ten-character abbreviations like `HUNTER KNF`.

| | tiles used of 34 | refused |
|---|---|---|
| 4 rows of the four WIDEST item names | 32 | **0** |
| 5 rows of the widest | 32 | 1 |
| 5 rows of typical names | 28 | 1 |

So a four-row item window fits with nothing to spare, which is only viable
because the battle item menu has four rows and its five pages fully overlap -
no page leaves characters visible behind another, so they can reuse the tiles.
If a fifth row is ever drawn it goes **blank**, which is visible and harmless
rather than corrupting.

### A guard that was measuring the wrong thing

`en-build` checked name widths with `vwffont.cells`, which assumes every letter
is a small cap. Capitals are a pixel wider, so it under-measured any name
containing one - it reported the widest item name as 7 cells when it is 8. It
now measures the **encoded bytes** through `cells_for`, which is what the
renderer actually sees.

## Correction: the nametable outlives the allocation

The battle item menu's pages showed row 1 as the first six cells of a name
drawn for a *different* page, its last two cells spilling into row 2 -
`MONOMA` above `TE IRSHIELD`.

Sequential allocation caused it, and the reason is a property I had not
identified: **a nametable entry outlives the allocation that produced it.** A
row that is not redrawn keeps its old entries, and if the pool has since been
rewound and refilled with different-width text, those entries index tiles that
now hold something else at a different offset. Page 2 redraws only the rows it
has items for; every row it skips is left aliasing into page 2's tiles.

That is not a bug in the reset. The `Battle_SetupWindow` reset point was
correct and does fire once per window. Sequential allocation is simply the
wrong shape for a display where entries persist.

**Deriving the slot from the destination removes the failure by construction.**
Row R always owns the same eight tiles, so a stale entry shows row R's own most
recent content - which is what that row should be showing. It also needs no
reset, so the five window-build redirects and the trampoline are gone: the
patch is back to **one redirect per converted call site and nothing else**.

Verified against the exact scenario - draw four rows, then redraw only the
first two with different widths:

| row | redrawn | tiles |
|---|---|---|
| 1 | yes | `$4C2-$4C8` |
| 2 | yes | `$4CA-$4D1` |
| 3 | **no** | `$4D2-$4D8`, unchanged |
| 4 | **no** | `$4BA-$4C1`, unchanged |

Every stale row still indexes only its own slice, and the four rows map to four
distinct slices. Under sequential allocation row 1 would have started at `$4BA`
and run into row 2's tiles, which is precisely the spill.

I removed this scheme a turn earlier on the grounds that it needed window
geometry I kept getting wrong. That was the wrong trade: the geometry is one
fact to check per call site, and stale-entry safety is a property nothing else
provides.

## The battle item list needs more slots than exist

The spill is gone, but page 1 still showed page 2's names. The cause is the
list's shape: it is **one long run, not four rows**. `$004D70` sets
`lea ($FFFF0516).l,a1` once and each entry advances 256 bytes, continuing past
the four visible ones through the whole inventory. "Pages" are a window onto
that run, not separate buffers.

With four slots, item *i* and item *i+4* map to the same slice - and item 5 is
exactly "page 2, row 1". Whichever drew last wins, so page 1 inherits page 2's
name wherever the two share a slot.

Covering it needs **one slot per item drawn** - up to 20 - which is 160 tiles
against the 34 that exist. No hash helps: the collisions are not accidental,
they are the pool being smaller than the working set.

So `$004DAA` is reverted to the stock renderer and waits for the low font bank.
Converted now: **techniques, skills, and the two field item menus** - four call
sites, one redirect each, 43 code bytes below `$300000`.

### What this says about the order of work

Three windows have now been converted cheaply because each draws a small,
bounded number of strings into a fixed set of rows. The battle item list is the
first that does not, and it will not be the last - anything scrolling has a
working set larger than a screenful.

That is the real reason the remaining conversions have to happen together with
reclaiming the low font bank, and not one at a time: it is not that the tiles
are merely tight, it is that a scrolling list's working set is bounded by the
data, not the display.

## Correction: the list draws five, not twenty

The previous entry claimed the battle item list draws the whole inventory as
one long run and therefore needed 160 tiles. That was wrong. `$004D78` is
`moveq #4,d7` against a `dbf` - **five draws per build**, four visible plus one
off-screen, redrawn on every page change.

So the working set was never larger than five. The collision was arithmetic:
under `(a1 >> 8) & 3` the five rows `$05-$09` map to slots `1 2 3 0 1`, so
entry 0 and entry 4 share a slice - and entry 4 is the first item of the next
page. That is exactly "page 1 inherits page 2's names".

### Period five

A power-of-two period is the obvious choice and the wrong one. Period 5 makes
any five consecutive rows distinct:

| rule | rows `$05-$09` | |
|---|---|---|
| `& 3` | 1 2 3 0 1 | collide |
| **period 5** | 0 1 2 3 4 | distinct |

It costs a table lookup instead of a shift, and it buys freedom from
contiguity, which is what makes it fit at all: slices no longer have to be one
run, so the fifth lives in the **structural VRAM gap at `$794`** that no table
can ever use. 5 x 8 = 40 tiles where only 34 were contiguous.

```
ROWTAB  $301400  256 bytes  (a1>>8)&$FF -> slot*2
SLOTTAB $301600  5 words    04BA 04C2 04CA 04D2 0794
```

Verified: the battle item list, the technique menu and the skill menu each draw
five consecutive rows with **no overlapping slices and distinct DMA sources**.

This also answers the pagination problem directly. Technique and skill menus
paginate later in the game and will draw the same five-row shape; period 5
covers them for the same reason it covers items, rather than needing a separate
fix when they do.

**The margin is zero.** Row `$0A` wraps to slot 0, so a window drawing six
consecutive rows would collide. Nothing observed does, but a sixth slice needs
eight more contiguous tiles and the remaining gap (`$79C-$79F`, `$7BC-$7BF`) is
two runs of four. That is a reason to reclaim the low font bank, not a reason
to redesign.

## The real cause: stale nametable entries are fatal for a VWF

Period 5 was correct and did not fix the item menu, because slots were never
the problem. Read out of a savestate with the menu open, all four displayed
rows already had distinct slices:

| row | tiles | slice |
|---|---|---|
| 0 | `$4C2-$4C6` (5) | slot 1 |
| 1 | `$4CA-$4D1` (8) | slot 2 |
| 2 | `$4D2-$4D8` (7) | slot 3 |
| 3 | `$794-$79B` (8) | slot 4 |

The window buffer at `$FF069A` held **seven** entries for slot 1 while the
displayed plane copy at `$FF869A` held only **five**. The buffer had been
redrawn with a longer name; the plane copy kept the shorter entry list. Five
cells then indexed a seven-cell name - `MONOMA`.

**Under the stock renderer that is harmless.** Its tiles are a fixed alphabet,
so an entry written for old text still renders that old text correctly, however
stale. A VWF's tiles belong to a string, so a stale entry renders whatever now
occupies them. Every place the game leaves a nametable entry behind is a
latent fault that only a VWF can trip.

### Fixed-length runs

Every draw now emits **the full slice** - eight nametable cells and eight tiles
- however short the name. The tail is blank because the composer clears the
scratch before it starts.

That makes the entry list length-invariant, so a stale copy has the same eight
entries as a fresh one and shows the slot's current contents rather than a
truncation of them. Verified: a ten-character name and a six-character one
write byte-identical nametable runs.

Cost: the DMA is always 256 bytes rather than 160-256, and a name always
occupies eight cells of nametable. Both fields are at least eight cells wide,
so nothing is displaced.

### What this cost, and what it teaches

Three separate fixes went in before this one - deferred-DMA aliasing,
destination-derived slots, period 5 - and each was a real bug, but none was
*the* bug. The through-line is that a VWF changes what the surrounding engine
is allowed to do: it may no longer leave stale nametable entries, reuse a tile
between strings, or let a queued DMA outlive its source. The stock renderer
tolerated all three.

## What the draw trace settled

Four rounds of inferring the item menu's behaviour from leftover RAM produced
four wrong answers. Instrumenting the renderer - 30 bytes recording every
draw's destination and slice into a ring buffer at `$FF5E00` - produced the
right one in two captures.

The first capture recorded only the destination's low word, which was not
enough: the slot uses bits 8-15, so two addresses differing above bit 15 look
identical in both. **Recording a truncated field to save two instructions cost
a round trip.** The second capture recorded the full 32 bits.

What it showed:

* draws land in **two** address groups, `$FFFF06A6..09A6` and
  `$FFFF069A..099A`, twelve bytes apart - two contexts sharing one buffer. Every
  address I had "confirmed" from residue was one of these mistaken for the
  other.
* **the same address is drawn repeatedly with different content** -
  `$FFFF06A6` appears four times in eighteen records.

### The bind

| scheme | stale nametable entries | same-address redraw |
|---|---|---|
| destination-derived slices | **safe** | shares tiles: an older plane copy shows newer content |
| sequential allocation | breaks | **safe** |

Neither works alone, and every fix this round was a real bug in one column or
the other:

* deferred-DMA aliasing - a shared staging buffer
* destination slices - stale-entry safety
* period 5 - slice collisions within a build
* fixed-length runs - length-invariant entries

None of them addressed the diagonal, because the diagonal needs **double
buffering**: two generations per destination, alternating, so a redraw lands on
a fresh slice while an older plane copy still points at the previous one.

That is 5 slots x 2 x 8 = **80 tiles** against the 50 that exist. This is the
point where the low font bank stops being an optimisation and becomes a
prerequisite.

### Current state

Converted: **techniques and skills**. Both redraw the same destination too, but
with the same content, so they are unaffected - and they are confirmed working
in game.

Reverted to the stock renderer: all three item sites. Item menus render
fixed-width, and correctly.

The trace instrumentation stays in. It is inert, it cost 30 bytes, and it has
already been worth more than every static inference in this file.

## Full conversion: the scope is 66 sites, not 9

The 8x8 renderer has **two** entry points, and every count in this file until
now used only one:

| entry | behaviour | callers |
|---|---|---|
| `$280564` | caller supplies the attribute in d0 | **9** |
| `$28055A` | forces `d0 = $E000`, falls into the same loop | **57** |

So the text system is **66 call sites**. That makes the implementation *easier*
- patch the two entry points rather than 66 redirects, since both are four to
ten bytes and a `jmp` fits - but it means a full conversion changes every piece
of 8x8 text in the game at once.

### The tile budget

Counting nametable cells that reference letter tiles in either bank, across
every savestate captured so far:

| | cells |
|---|---|
| worst observed (battle1) | **53** |
| typical battle | 29-43 |

At 35% narrower under the VWF that is roughly **35 cells**, so **70 tiles**
double-buffered against the **~102** the low bank yields. It fits, with margin.

Two caveats, and they are the whole risk:

* every state sampled is a **battle**. Field menus, shops and the status screen
  are unmeasured and could be worse.
* the allocation scheme has to separate **~35 simultaneous strings** at
  destinations from 66 call sites. Period 5 handles five. A hash over that many
  arbitrary addresses cannot be validated by inspection, and a collision is
  silent corruption of whichever string drew first.

### Measure before converting

The draw trace already in the ROM is the tool for this. Hooking **both** entry
points to record `(destination, text pointer)` and then fall through to the
stock renderer gives a build that plays completely normally while logging every
draw in the game.

Playing through the menus that matter and reading the log back yields the real
destination set, which is what an allocation scheme has to be designed against -
rather than inferred, which has failed six times in this file.

## The trace-only build

[`tracerom.py`](tools/tracerom.py). Both renderer entry points are redirected to
a stub that records `(destination, text pointer)` into a 256-entry ring and then
performs the instructions it displaced before rejoining the stock renderer at
`$28056A`. **Drawing is unchanged** - the VWF is not wired in this build, so all
66 call sites use the stock renderer and every one of them is logged.

```
$28055A  jmp ($300C60).l    entry B, replays movem + move.w #$E000,d0 + moveq
$280564  jmp ($300C00).l    entry A, replays movem + moveq
ring     $FF5400  256 x 8 bytes: dest.l, text.l
index    $FF5C00
```

A `jmp (xxx).l` is six bytes, so entry A's patch also swallows the `moveq #0,d2`
and entry B's swallows half its `move.w`; both stubs replay what they covered.
The VWF's absence frees the whole work-RAM block, which is why the ring holds
256 draws rather than 32.

Verified on all four paths - entry A, entry B, greyed attribute, repeat call:
rejoins at `$28056A`, `d0` carries the caller's attribute on A and `$E000` on B,
`d2` is zeroed, `a0` and `a1` are untouched, and the five-longword `movem` is on
the stack exactly as the stock entries left it.

**An encoding bug worth recording.** `move.l An,(Am)` is `$2088`; I first wrote
`$2080`, which is `move.l Dn,(Am)` - the log would have quietly recorded `d0`
instead of the text pointer. Address-register-direct is mode 001, not 000, and
nothing about the wrong encoding looks wrong.

## The trace build crashed, and why

Entering a battle produced an address error with the PC executing out of the
plane-B buffer. The savestate's call stack named the culprit precisely:

```
$007456   JSR  -> $280564        the field-text draw site
$280584   Exception -> $000404   vblank, during the draw
$FFFF9E75 Exception -> $000200   address error
```

**$280568 is a branch target.** Three branches point at it - the renderer's main
loop-back at `$28058E`, the dakuten path at `$2805E0`, and entry B's own `bra`.
A six-byte `jmp (xxx).l` planted at `$280564` swallows `$280568`, so every
character after the first branched into the middle of a jump operand.

I checked that nothing *referenced* the patched span as a longword, and that
was the wrong check: PC-relative branches do not appear as address constants.
Scanning `bra`/`bsr` displacements in the surrounding kilobyte finds all three
in a second, and would have caught it before the build shipped.

**Fix:** entry A is left completely untouched and its **nine call sites** are
redirected instead; only entry B, whose span nothing branches into, is patched
in place. Verified after rebuilding that `$280568` still holds `moveq #0,d2`
and both loop-back branches still resolve to it.

### The other capture

`trace-stackedmenu` recorded **zero** draws with the status screen open, which
is itself a finding: with entry A broken, only entry B's callers could log, and
they evidently did not run. Re-capturing on the fixed build will say whether the
status screen uses these entry points at all - if it still logs nothing, its
text comes from somewhere this project has not found yet.

## The party status bar redraws every frame

The first working capture saturated the 256-entry ring with exactly three
draws, repeating:

```
$FFFF8B30 <- $FFFFF600
$FFFF8B22 <- $FFFFF580
$FFFF8B14 <- $FFFFF500     Character_Stats, three party members
```

The party name bar is redrawn **every frame**. A ring therefore holds about 85
frames of nothing else, and everything the player did before saving has already
scrolled out.

That is worth knowing beyond the diagnostics: per-frame redraw means those three
strings always have fresh tiles, and it costs three DMA queue entries a frame
before any menu is open.

### A table, not a ring

The trace is now keyed by destination:
`((dest >> 1) ^ (dest >> 9)) & $FF`. Repeats collapse onto their own slot, so
what accumulates is the **set** of draws performed rather than the most recent
few. Verified: 120 party redraws plus four menu draws yield seven entries, not
124.

Folding two shifted copies is necessary, not decorative - `dest >> 1` alone
collides item rows `$069A` with `$089A`, and `$079A` with `$099A`. Collisions
are visible rather than silent, since the stored destination is kept and can be
rehashed.

### An assembler bug worth the guard

`lsr.l #9` is not encodable - immediate shift counts are 1-8, with 8 encoded as
0 - and `n & 7` silently turned 9 into 1. The hash then XORed a value with
itself, every draw hashed to slot 0, and the table held exactly one entry.

`Asm.lsr_l` now raises on an out-of-range count. Every hand-rolled encoding
helper in this project takes its operand on trust; this is the second one to
produce plausible, wrong code (`move.l An,(Am)` as `$2080` was the first).

## The destination set, measured at last

`trace-menuflow`, taken across the status screen, a battle and an item menu:
**19 distinct destinations, zero hash collisions.**

```
$FF0106                            singletons
$FF0308  $FF0408  $FF0508
$FF068E  $FF069A  $FF06A6          4 rows x 3 columns
$FF078E  $FF079A  $FF07A6
$FF088E  $FF089A  $FF08A6
$FF098E  $FF099A  $FF09A6
$FF8B14  $FF8B22  $FF8B30          party names, redrawn every frame
```

**The menu draws three columns per row, 12 bytes - six cells - apart.** That is
the structure six rounds of inference never found. Every "two address groups
twelve bytes apart" and "stale run at $FF068E" in the entries above was two
columns of the same row, read as evidence of something else.

It also bounds the strings: a column cannot exceed **six cells** without running
into the next one.

### The budget, finally arithmetic rather than guesswork

| slice size | single-buffered | double-buffered |
|---|---|---|
| 6 tiles (a full column) | **114** | 228 |
| 8 tiles (current) | 152 | 304 |

Against **~102** tiles from the low bank, or **~166** if the high bank's digits
and punctuation convert too.

So:

* **single-buffered, both banks reclaimed: 114 of 166. Fits.**
* double-buffered: 228 of 166. Does not fit, at any slice size.

Double buffering was the fix for the item menu showing a stale plane copy's
content. It is not affordable, so that problem has to be solved another way or
accepted - and it is worth noting the party bar redraws every frame, which means
plane copies are refreshed constantly in battle. Whether the stale-copy case
survives a full conversion is a question for a build, not for more analysis.

19 destinations is also an upper bound rather than a simultaneous count: the
capture is the union across three screens.

## There is a SECOND text engine

The shop and sell captures traced **zero** draws while showing **82 text cells**
from the font bank. The text is real; the renderer is not the one instrumented.

Searching for every site that adds a font tile base to a register finds four,
not two:

| site | |
|---|---|
| `$280586` / `$280580` | the name renderer, already known - 66 callers |
| **`$069B88`** | **a window/tilemap renderer**, entered at `$069B78` |
| `$010840` | a one-off single glyph, not a general path |

`$069B78` is the engine the US disassembly calls `LoadWindowTiles`: it walks a
string, dispatches `$F0`+ control codes through its own jump table, and writes
into a plane buffer with `addi.w #$680,d2`. It is a **separate text system** with
its own control codes - and it is what draws shop and sell screens.

So the map is:

* `$280564` / `$28055A` - names: items, techniques, skills, party, enemies
* `$069B78` - menu layout and shop text

### What this does to the plan

The scope has now grown twice from the same mistake - measuring one path and
assuming it was the system. Nine call sites became 66 when the second entry
point turned up; 66 became "and a whole second engine" here.

A full conversion needs both. The window renderer is the harder of the two: it is
tilemap-driven and control-code-driven rather than a simple byte loop, so
converting it is a larger job than the name renderer was, and its destination set
is unmeasured because the instrumentation does not cover it.

The sell screen also raises the peak: **82 text cells**, against the 53 that the
battle captures suggested.

Budgeting it honestly requires instrumenting `$069B78` as well and capturing
again. That is a third trace round before any conversion work starts.

## Should the work move to the US ROM?

Checked rather than guessed. The disassembly:

* **assembles cleanly** - 379,719 lines, 441,083 with macros, **0 errors, 0
  warnings, 3.2 seconds** - and links to a complete 3 MB image whose header and
  checksum (`$05CB`) are self-consistent
* **stores the script as editable source** - 43 `script/dialogue N.asm` files,
  ~33,000 lines of plain English with a `charset` and a `compress_script.py`
  that packs them into the same `$FF3000` RAM buffer the Japanese build uses

That last point is the whole argument. Every category of work that has cost this
session disappears:

| on the JP ROM | on the disassembly |
|---|---|
| relocation arenas, first-fit packing | the assembler lays out addresses |
| hunting ~200 pointer sites | labels |
| `adda.w #$2DD` going stale | computed at build time |
| "which routine is this?" | `Battle_SetupWindow`, `TechniqueNames`, `LoadWindowTiles` |
| six rounds of trace-and-capture to find a menu's geometry | read the source |

Both text engines found the hard way here are already named there.

### What transfers, and what does not

**Transfers** - and it is the valuable half:

* the entire Japanese script decode: 26 streams, 2131 messages, 126,917
  characters, 1157 kanji, 0 unmapped, byte-exact round-trip
* every font: `vwffont`, `vwfcase`, `vwfcreep`, and the measurements behind them
* the VWF design - composer, expander, slice model - and `emu68k`
* the glossary and translation work itself

**Does not transfer** - all of it address-bound to the Japanese build:

* `relocate.py`, `relocate8.py`, `layout.py`, the item-shortcut fix, the VWF
  wiring, `tracerom.py`
* the 4 MB expansion, though that is a one-line change to the padding loop

### The honest costs

* the US script is **43 dialogue trees**, the Japanese one **26 LZSS streams** -
  different segmentations of the same game, so mapping messages across is real
  work, though a matching problem rather than a reverse-engineering one
* the US release differs in content in places, so some entries will not
  correspond one to one
* the VWF still has to be built: the VDP constraints are identical and none of
  the tile budget changes. What changes is that finding the renderers and their
  callers becomes grep instead of six capture rounds

### The one thing still unverified

It assembles, but that does not prove the image is faithful - a disassembly can
build cleanly and still not boot. That is cheap to settle: build it and run it.

## Moving to the disassembly: the four open questions

### 1. The Bugfix v1.5 ROM is the wrong base - use the flag instead

`Phantasy Star IV [Bugfix v1.5].bin` is **not** this disassembly with its flags
on: 1,210,524 bytes differ from a vanilla rebuild, and still 1,080,193 with
`bugfixes=1`. Much of that is inserted code shifting everything after it, so the
byte count overstates the divergence - but the lineage is clearly separate.

It does not matter, because **the disassembly carries its own fix set**: 46
`if bugfixes` blocks and 4 `if optional_fixes`, covering the same classes the
readme lists - softlocks, level-up stat updates, the input-skip bug, losing
Telepipe/Escapipe on battle use, collision and palette fixes.

Taking the binary as a base would put the project straight back into binary
patching, which is the entire thing the move escapes. Build with `bugfixes = 1`
instead. The two sets may not be identical, so any specific fix that matters
should be checked against the 46 blocks.

### 2. Akasha / Shadow Mirage - one flag

`restore_unused_enemies = 1` in `ps4.options.asm`. No bit-hunting. (The
disassembly spells it "Acacia"; worth confirming the same enemy is meant.)

### 3. The VWF is easier here, not harder

The VDP constraints are identical and none of the tile arithmetic changes. What
changes is that **the VRAM layout is source-defined**: `Title_ArtPtrs` and its
siblings assign tile indices as `dc.w $680 / dc.l ArtNem_Font`, so reclaiming the
font bank stops being archaeology and becomes an edit. Code can be inserted
rather than squeezed into `$FF` filler, and the slice pool no longer has to be
scavenged from whatever tiles a savestate showed idle.

`vwffont`, `vwfcase`, `vwfcreep`, the composer and the expander all transfer as
designs; only the wiring was ever JP-address-bound.

### 4. The script fits

| | |
|---|---|
| US script | 43 trees, 127,072 bytes compressed, 9,905 strings, 214,834 characters |
| per-tree decompressed limit | 7,887 bytes (`$FF3000-$FF4ECF`) |
| total headroom | 339,141 bytes |
| our Japanese-source translation | ~182,000 decoded bytes |

So a full replacement fits with room to spare, and the goal that nothing of the
US script survives is achievable rather than aspirational.

The real work is **mapping 26 Japanese LZSS streams onto 43 US dialogue trees** -
different segmentations of the same game. That is a matching problem against two
fully decoded, human-readable scripts, not a reverse-engineering one.

## Baseline: the US disassembly with bugfixes

`ps4.options.asm` now has `bugfixes = 1`. `optional_fixes` is left at 0 - it is
described as the "larger" set and is a separate decision.

Build: 379,719 lines, **0 errors, 0 warnings**, linked and passed through
`fixheader`, which recomputed the checksum to `$0830` (verified: stored equals
computed).

```
work/ps4us_bugfix.bin   3 MB, GM MK-1307 -00, ROM end $2FFFFF, reset $000220
```

Against a vanilla rebuild, 463,164 bytes differ across **14 regions**. All but
one are small - 1 to 314 bytes, the individual fixes. The exception spans
`$000861-$07A9A5`, and that is not half a megabyte of changes: it is inserted
code shifting everything after it.

That shift is the point. On the Japanese ROM, inserting a single instruction
meant finding filler, trampolining to it, and hoping nothing branched into the
bytes displaced - the `$280568` crash was exactly that going wrong. Here the
assembler relocates half the image and fixes every reference, in three seconds,
and the only evidence is that the diff is large.

## The VWF, ported to source

`ps4disasm/vwf/` now holds the font and the two routines, assembled as part of
the tree rather than patched into filler.

```
vwf/vwf.asm      VWF_Compose, VWF_Expand, and the table includes
vwf/font.bin     2048 bytes - 256 entries x 8: advance width, then rows 1-7
vwf/expand.bin   1024 bytes - 256 longwords: one 1bpp byte -> eight nibbles
```

`ps4.constants.asm` gains `VWF_RAM_Base = ramaddr($FFFF5400)` with `VWF_Scratch`
and `VWF_Tiles` under it. Declared in the map, not squatted on: `Sound_Index`
(`$FF500A`) is the last symbol below and `Chunk_Table` (`$FF6000`) the first
above, and the Japanese-ROM savestates independently showed the region quiet
across fifteen captures.

Build: **0 errors, 0 warnings**, 379,861 lines. The assembler placed
`VWF_Compose` at `$2F4A14`, `VWF_Expand` at `$2F4A76` and the tables after them
- no filler hunting, no trampolines, no addresses to re-derive if anything
moves.

**Verified from the built ROM**, executing the linked bytes under `emu68k`
against the same `vwffont` oracle used on the Japanese side:

* **326 names, 0 mismatches**
* worst case 1457 instructions for compose plus expand

### What the move already bought

The Japanese version of this needed a Python assembler, hand-checked opcode
encodings, a scavenged RAM address justified by savestate surveys, and a search
for `$FF` filler large enough to hold the code. Two of those hand encodings were
wrong in ways that produced plausible output (`move.l An,(Am)` as `$2080`,
`lsr.l #9` silently becoming `#1`).

Here the same routines are ordinary source. The assembler encodes them, places
them, and resolves every reference.

Next: the renderer itself - tile pool, DMA queue call, nametable writes - and
hooking `loc_27DB9C`, which is what draws the truncated item names.

## Pool layout, designed fresh

The Japanese design was shaped entirely by scarcity: 34 contiguous tiles
scavenged from art that savestates happened to show idle. Every awkward part of
it - period-5 slot cycling, non-contiguous slice bases, the unaffordable double
buffer - existed to fit that. None of those constraints survive the move.

### What is actually available

VRAM, from the register table in source (`$8230`, `$8407`, `$8578`, `$8D3D`):

| region | VRAM | tiles |
|---|---|---|
| tile art | `$0000-$BFFF` | 1536 |
| plane A nametable | `$C000-$CFFF` | - |
| **font bank (low)** | **`$D000-$DFFF`** | **128** |
| plane B nametable | `$E000-$EFFF` | - |
| sprite table | `$F000-$F27F` | - |
| gap | `$F280-$F3FF` | 12 |
| hscroll table | `$F400-$F77F` | - |
| gap | `$F780-$F7FF` | 4 |
| **font bank (high)** | **`$F800-$FFFF`** | **64** |

**208 tiles**, once all text is VWF - and in source it can be, because both
engines are one routine each. The low bank's 128 are contiguous. Window-frame
tiles currently occupying codes `$66-$77` move into the high-bank region, whose
capitals and digits the VWF supplies from ROM; those are named constants in
named routines, so moving them is an edit rather than a hunt.

### The rule: a cell owns its tile

**Allocate positionally, not per string.** A screen cell is permanently bound to
one pool tile.

That single choice removes every failure mode the Japanese attempt hit, by
construction rather than by patching:

| failure | why it cannot happen |
|---|---|
| stale nametable entries showing another string | a cell's tile only ever holds that cell's content |
| same-destination redraw with different content | rewrites that cell's own tile |
| slice collisions between rows, columns or pages | no slices |
| pool drift needing a per-window reset | no allocator state |
| a queued DMA outliving its RAM source | one staging slot per cell |

It needs no reset, no trampoline, no knowledge of any window's geometry - which
is what six rounds of trace-and-capture were spent failing to establish.

### Does it fit

| | cells |
|---|---|
| full-width dialogue box, 38 x 4 | 152 |
| widest menu screen measured (shop sell) | 82 |
| **pool** | **208** |

Dialogue and menus are never on screen together, so they share the pool rather
than summing.

152 of 208 is comfortable but not lavish, and the dialogue figure is a
worst-case estimate rather than a measurement. Confirming it wants one capture
of the widest dialogue box in the US build - and unlike the Japanese ROM, adding
that instrumentation is a few lines of source that the assembler places safely.

### Measured: the box is 32 x 2, not 38 x 4

The dialogue box holds **32 cells per row, two rows - 64 cells**, confirmed
against the game rather than estimated. My 152-cell figure was a guess derived
from 40-cell mode and an assumed box height, and it was wrong in the direction
that mattered: dialogue is the *smaller* consumer, not the larger.

| | cells |
|---|---|
| dialogue box, 32 x 2 | **64** |
| widest menu screen measured | 82 |
| **pool** | **208** |

2.5x headroom over the larger of the two. Double buffering, which was
unaffordable on the Japanese ROM at 228 tiles against 50, would fit here at
**164 of 208** - so it stays available as a fallback rather than being designed
out. The positional scheme should not need it.

### What the face actually buys

Mean advance over 15,677 characters of the translated script, using the real
font table: **4.59 px against a fixed 8.**

A 32-cell row therefore holds about **56 characters instead of 32 - a 74%
increase**. That is the whole point of the exercise: the US script truncated
names and clipped lines to fit 32, and this is the room that removes the need.

It also retires a bug rather than working around it. There is a line near the
end of the US script that runs 33 characters and overflows the box; at 4.59 px
average, 33 characters is about 152 px of the available 256, so the overflow
cannot occur.

**The pool layout is settled.** Next is the renderer.

## The dialogue engine is not the menu engine

`TextCtrlCodesJmpTbl` turned out to belong to `RunText` - the dialogue
engine, and a third text path after the two menu ones.  Checking it before
committing the pool arithmetic was worth it, because it does not use the
tile pool at all:

* `Art_DiaFont` is a **1bpp 8x16** face, 16 bytes a glyph, 80 glyphs -
  not the 8x8 menu font.
* Dialogue owns a private **128-tile region at VRAM $B000** with a full
  4096-byte RAM shadow at `Text_Buffer` ($FFFF7000).  Offsets in the two
  are identical, so a shadow offset doubles as a VRAM offset.
* `GetFontGraphics` -> `ParseText` -> `TextCharacterToVRAM` already
  expands 1bpp to 4bpp per character and DMAs it.

So dialogue was **already most of the way to a VWF**: it composes glyphs
into RAM and moves them itself.  It needs no pool, no allocation, and no
nametable churn - the 208-tile pool is for the menus alone.

`andi.w #$1F, d1 ; limit of 32 characters per line` sits in the source,
confirming the measured 32 cells independently.

### The composite is a plain OR

Paper is $E and ink is $F, so `$E | $1 = $F`: setting the low bit of a
nibble turns paper into ink.  `FillTextBackground` pre-fills the shadow,
so a glyph composites with a plain OR and no read-modify-write, and
drawing the same glyph twice is harmless.  `VWFDia_NibExp` (16KB) holds,
for each (byte, shift) pair, the two longs to OR into the two cells a
glyph can straddle.

### Widths are measured, not redrawn

Advances come from the existing artwork's ink extents plus 1px tracking,
so every letterform is untouched - only the spacing changes.  Uppercase
stays at 8 and loses nothing; the gain is in lowercase (7), `i` (3),
`l` (4), `I` (5).  `Q` and `Y` measure 9 and get *wider*: at a fixed 8
they currently touch the following glyph.

Over the 9,905 lines of US script (214,834 characters, none unmapped):

| | fixed | VWF |
|---|---|---|
| mean advance | 8.00 px | **6.11 px** |
| characters per 32-cell row | 32 | **41.9** (+31%) |

Correcting the earlier entry: the +74% figure applied the *menu* face to
a dialogue row.  Dialogue uses `Art_DiaFont`, and the honest number is
**+31%**.

The script's longest line is **33 characters, and exactly one line is
over 32** - the end-of-game overrun, found in the data without looking
for it.  Rendered proportionally it is 216px of the available 256.

### The dispatch pins the loop size

The first build failed on *stock* code:

    ps4.asm(140550): error: addressing mode not allowed on 68000
        jmp TextCtrlCodesJmpTbl(pc,d5.w)

PC-relative **indexed** mode has an 8-bit displacement, +/-127 bytes, and
the stock loop already sat near that limit.  Growing it by 4 bytes pushed
the table out of reach.  So `VWFDia_DrawGlyph` does the wrap test itself
and returns "room left" in d5, which trades 8 bytes of inline test for 4
and keeps both call sites at exactly their stock size.  Worth remembering:
**these two loops cannot grow.**

### Buffer edge

Cell 32 of line 1 is offset $1000 - one byte past the shadow buffer.  A
glyph landing at cell 31 therefore has its spill write suppressed.
Verified with a canary immediately past the buffer.

### Verified by execution

`emu68k` ran the *assembled* `VWFDia_DrawGlyph` against a simulated
shadow buffer (five opcodes added to the interpreter, which refuses
unknown ones rather than guessing):

* real strings match an independent reference **bit-for-bit**, both lines
* wrap fires at exactly 256px; cursor resets; the room flag clears
* the canary past the buffer survives a straddling glyph, whose visible
  half is still drawn
* mid-line glyphs straddle two cells as intended

A line longer than 256px is clipped and wrapped rather than overrunning.
That case is an authoring error, and belongs in the proofreading tool as
a hard limit - not in the engine.

## Regression: the narration shares the font

Normalising `Art_DiaFont` in place was wrong.  A fourth text path draws
from the same art at a fixed 8px pitch, so stripping each glyph's left
bearing left the slack piled on the right - visible as a gap after `i`
and `l` in the attract-mode and pre-Piata narration.

**Fixed by decoupling rather than compromising.**  `Art_DiaFont` is
restored byte-for-byte to the shipped art, and `VWFDia_DrawGlyph` reads
its own left-normalised copy at `VWFDia_Font`, deriving the glyph index
from the `a1` that `GetFontGraphics` returned.  Costs 1280 bytes and
lets the two paths move independently.

### Why the fourth path was missed

`RunText2` *is* the narration engine, and I had called it a dispatcher.
Two independent reasons:

* it calls `jsr (GetFontGraphics).l` - absolute long, so a sweep for the
  `(pc)` form did not see it;
* its loop ends `cmpi.w #$20, d1`, not `andi.w #$1F, d1`, so the
  32-column signature sweep did not see it either.

Two greps, two blind spots, same routine.  The lesson is that a sweep
for one encoding of an idiom is not a census.

### What the narration engine does differently

| | dialogue (`RunText`) | narration (`RunText2`) |
|---|---|---|
| buffer | `Text_Buffer` $FFFF7000 | `RAM_Start` $FFFF0000 |
| paper | $E (opaque box) | **0** (transparent over scenery) |
| writer | `ParseText` | `loc_6AC54` |
| flush | whole box, or one cell | `count * $20` words |

The buffer is pre-cleared to zero by `loc_6AA86` (512 longs = 32 cells),
so OR-compositing still works - but against paper 0 the mask must carry
$F per pixel, not $1.  That needs no second table: each nibble of the
existing mask holds $1, so `v |= v<<1; v |= v<<2` widens $1 to $F with no
carry across nibble boundaries.

### The blocker to solve first

`($FFFFED5A).w` carries **two** meanings:

* in the `d4==2` single-character path it is loaded into d1 as the *draw
  position*;
* in both flushes it is the *DMA length in cells* (`mulu.w d0,d2`).

Under a VWF those diverge - position becomes pixels, length stays cells -
so they must be split before the narration can be converted.  `RunText2`
is also dispatch-pinned (`jmp loc_6AA44(pc,d5.w)`), though its loop
*shrinks* under the change, which is safe.

## The narration split turned out not to exist

The blocker was that `($FFFFED5A).w` looked like it carried two meanings:
a *cell index* (the draw position, and the source/destination of the
single-cell flush) and a *cell count* (the DMA length in `loc_6AC98`).
Splitting them would have been fiddly.

It was unnecessary.  Every use of ED5A as an index lives in the `d4==2`
path - `loc_6AA14` and the routines reached only from it, `loc_6AAB2`,
`loc_6AB2E`, `loc_6ACC4`.  That path is **dead**:

* all sixteen `RunText2` call sites pass `moveq #1, d4`;
* the only writes to d4 anywhere in the region are inside `loc_6AC54`'s
  bit loop, which saves and restores d4 through its own `movem`.

So ED5A has exactly one live role - the DMA length - and the conversion
only had to keep it meaning *cells covered* rather than *characters
drawn*.  `VWFNar_DrawGlyph` recomputes it as `ceil(cursor/8)`, clamped to
32 so the DMA can never run past the buffer.

This also explains the earlier confusion where `loc_6AAB2` derived a tile
number from `ED5A*2` but a RAM offset from `ED5A<<7`.  Those two never
had to agree, because nothing reaches them.

### The trap in converting it

With `d4=1` the per-character flush is skipped, and every control code
lands on `loc_6AA84`, which was a bare `rts`.  The **only** DMA was
`loc_6AA10`, reached when the character count hit 32 - so the narration
worked because its lines are exactly 32 characters.

Proportionally, 32 characters is about 195px.  The cursor would never
reach the 256px wrap, `loc_6AA10` would never fire, and the narration
would have rendered **nothing at all** - a blank screen, not a subtle
misalignment.  `loc_6AA84` now flushes before returning.

Worth keeping: *a wrap condition can be load-bearing for something other
than wrapping.*

### Transparent paper

The narration composites over scenery, so its paper is 0 and its ink $F -
unlike the dialogue box's $E/$F.  The OR still works because `loc_6AA86`
pre-clears the buffer to zero, but the mask must carry $F per pixel.
That needed no second table: each nibble of `VWFDia_NibExp` holds $1, and
a nibble shifted left by 1 then by 2 cannot carry into its neighbour, so
`v |= v<<1; v |= v<<2` widens $1 to $F in place.

Both loops shrink under the change (RunText2's by 8 bytes), which is safe
for the `jmp tbl(pc,d5.w)` dispatch - only growth is dangerous.

### Verified by execution

`VWFNar_DrawGlyph` was run from the assembled ROM against a simulated
`RAM_Start`, with a canary past the 32-cell buffer:

* strings match an independent reference bit-for-bit
* cells-covered matches `ceil(width/8)` on every case
* untouched cells stay 0, so the scenery still shows through
* the canary survives a glyph at cell 31
* the 256px wrap fires exactly at the boundary

Four more opcodes were added to `emu68k` along the way (`lsl.l`,
`move.b Dn,(xxx).w`, `move.l Dn,Dm`, `or.l Dm,Dn`).  It refuses unknown
encodings rather than guessing, which is why each gap surfaced as a clean
trap instead of a wrong answer.

## Menus: the blocker is the face, not the tiles

Tile scarcity killed the VWF on the Japanese ROM, so that was the expected
enemy here.  It is not.  Measuring the shipped 8x8 face:

| | mean advance | saving vs fixed 8 |
|---|---|---|
| uppercase | 7.85 px | 1.9% |
| lowercase | 7.46 px | 6.8% |

The glyphs are drawn 7px wide inside an 8px cell, so there is almost no
slack to reclaim.  A VWF over the stock artwork buys about 7% - a 10-cell
item field would go from 10 characters to 10.7.  That is a great deal of
risky engine surgery for nothing, and it would not fix truncation.
The gain lives in the *face*, not the renderer.

### Two corrections along the way

`wincharset.asm` numbers are **decimal**, not hex: `charset 'a','z',57`
puts lowercase at $39-$52, not $57-$70.  Reading them as hex made
lowercase look absent from the font and produced a nonsense width table
(`b=4`, `x=3`, `i=7`).  The decimal reading cross-checks exactly against
glyphs verified by eye: `-`=$31, `!`=$32, `.`=$53, `,`=$55.

The bank is also built from **two** blobs, not one:

    dc.w $680 / ArtNem_WindowTiles   ; 128 tiles, lays down the bank
    dc.w $7C0 / ArtNem_Font          ; 87 tiles
    dc.w $681 / ArtNem_Font          ; 87 tiles, over the top

`WindowTiles` supplies the blank at $680 (the space, code $00) and
whatever survives at $6D8-$6FF; `Font` overwrites $681-$6D7, which is why
its tile 0 is `A` and not the space.

### The chosen face

Small caps with true capitals: uppercase draws `vwfcase.CAPS` (6 rows
from top 2), everything else draws `vwffont.G` (5 rows from top 3).  Both
bottom-align on row 7, which is what makes them read as one face.

| | mean advance |
|---|---|
| true capitals | 6.08 px |
| small capitals | 5.08 px |

A 10-cell field holds **15.5 characters** against 10 today.  `Titanium
Shield` renders 68px, `titanium shield` 65px, `TITANIUM SHIELD` 85px -
three distinguishable forms, which was the requirement.

Note that all-caps is now the *widest* form: 85px still overflows the
80px field, though it beats the 120px the stock font needs.  Long names
only land fully inside the field once they are mixed-case, so the
planned case pass is what closes the last of the gap rather than being
cosmetic.

`tools/menuvwf.py` emits `menufont.bin` (128 x 8 bytes, 1bpp, indexed by
charset code) and `menuwidth.bin`.  69 glyphs placed, widest advance 8px.

## Menu pool: measured, and tighter than hoped

Rather than infer the pool size from window geometry - the mistake that
sank the Japanese attempt - it was read straight out of Exodus savestates.
Plane A's nametable is at VRAM $C000, so counting entries pointing into
the font range ($681-$6D7) *is* the live-text-cell count.
`tools/menucount.py` does this; no build or instrumentation needed.

| screen | fixed cells | VWF cells (all-caps) | VWF cells (title case) |
|---|---|---|---|
| **field item menu** | 126 | **86** | **78** |
| shop sell | 91 | 60 | 52 |
| battle item menu | 72 | 51 | 45 |

Supply is **87 tiles** ($681-$6D7), freed by converting the font.  Against
a worst measured demand of 86, that is a margin of one tile - and only
three screens were sampled.

Note the current script is all-caps, which in the new face is the *widest*
form (true caps 6.08px vs small caps 5.08px).  The planned case pass drops
the worst screen to 78, which is still 90% utilisation.

### Three dead ends, each found by measurement

* **dialogue box $580-$5FF (128 tiles).**  Looked free - dialogue and menus
  seemed mutually exclusive.  The shop sell screen references all 128 of
  them while the menu is open.  Reusing them would have corrupted it.
* **$700-$7BF (192 tiles).**  Showed zero references, which looked like a
  windfall.  It is not tile art at all: tile $700 is VRAM $E000, Plane B's
  nametable, and $780+ is the sprite and HScroll tables.  Nothing
  references it as tiles because nothing can.
* **$7C0-$7FF (64 tiles).**  A second copy of the font, only 13 of 64
  referenced.  But those references are *on-screen* during menus - 18
  cells in the field menu, 22 in battle.  Live.

"Unreferenced in this frame" is not "free", and a region with no
references at all may simply not be tile memory.

### Also: two renderers must convert together

`loc_27DB9C` (9 callers) writes nametable entries off the same $680 base
as `LoadWindowTiles` (330 callers).  Freeing the font breaks both, so both
have to be converted in one step.

## The shop overlap: a third line in a two-line box

Reported as unidentifiable text overlapping row 0 of the sell offer.
It is the same failure mode as the narration flush, in the other
direction.

`Win_ShopSellConfirm` assembles one string in RAM at $FFFFE300 from
four pieces - item name, a `"?" $FC` fragment, the converted price, and
a `" meseta." $FC "How about that?"` fragment - then calls `RunText`
with d4=0.  That is **three lines for a two-line box**.

The box-full check lives *only* in the auto-wrap path:

    addq.w  #1, d2
    ...
    andi.w  #1, d2
    beq.w   TextCtrlCode_Interrupt   ; prompt, clear, continue

`TextCtrlCode_Newline` never had it - it just does `moveq #0,d1;
addq.w #1,d2`.  Stock reached the check because auto-wrap fired on
character count; proportional text never reaches the 256px wrap, so d2
ran to 2, and the line mask in the renderer folded line 2 back onto
line 0.  Because the composite is an OR, the third line accumulated on
top of the first instead of replacing it - hence text that looked like
nothing in particular.

**Corrected after testing against the unmodified ROM.**  The first fix
added the box-full check to both newline handlers, which produced a page
prompt and then the third line.  Stock shows no prompt: it goes straight
from the two-line offer to the YES/NO cursor, and the third line never
appears at all.

The reason is that stock lets d2 run to 2 and `TextCharacterToVRAM`
writes the glyph to $B000 + 2*2048 = $C000 - an off-screen corner of
Plane A's nametable.  The line is composed, sent nowhere visible, and
silently lost.

So the missing check was never the bug.  **Masking d2 was.**  Folding
line 2 onto line 0 is what put "all right?" on top of the item name;
stock simply threw it away.  The renderer now drops any glyph whose line
is past the second: same result on screen as stock, without the stray
write into the nametable.  `VWFDia_FlushGlyph` skips a zero-length span
so a dropped glyph queues no DMA.

**This is the second time a wrap condition turned out to be load-bearing
for something other than wrapping** - first the narration's only DMA, now
this.  Worth assuming there are more: any behaviour that hung off "we
reached 32 characters" is suspect, because that event no longer happens
where it used to.

And a lesson about fixing: the first attempt made the engine *more*
correct than the original - a two-line box overflowing by a line really
should page.  But the goal is to match the game, not to improve it, and
only testing against the stock ROM showed the difference.  Verified by
execution: lines 0 and 1 compose, lines 2 and 3 touch nothing, and a
dropped glyph still advances the cursor.

### Not a bug: Exodus does not persist SRAM

Saving appeared broken - the slot menu showed save files that were never
made, the title screen reported no data, and saving claimed success but
did not stick.  It reproduces identically on `ps4us_bugfix.bin`, and
saving works correctly in BlastEm.  An Exodus setup issue, not the hack.

The RAM dump had already exonerated the ROM before the cross-check:

* the VWF block at $FFFF5400-$FFFF5485 held exactly three nonzero bytes,
  its own dirty variables, and $FFFF5486-$FFFF5FFF was entirely zero -
  the region really is dead space, and the sound area ends before it;
* the save image in RAM was **valid**: the "PHANTASY STAR 4" signature was
  intact, `Save_Slot` was 2, and the stored per-slot checksum ($7699)
  matched an independent recomputation of `SumSRAMBytes` over
  `Event_Flags`.  The game had assembled a correct save; only the write to
  cartridge SRAM went nowhere.

Two tells: the savestate has no SRAM section at all, and no `.srm` exists
anywhere under `Exodus_2.1`.

**Use BlastEm to test anything save-related.**  Exodus stays the tool for
savestate analysis, since `tools/menucount.py` and the VRAM work depend on
its `.exs` dumps.

## A full menu VWF does not fit

Measured across eight screens, against a reliable pool of 87 tiles
($681-$6D7, freed by converting the font):

| screen | VWF cells, all-caps | title case |
|---|---|---|
| **status, all windows open** | **97** | **93** |
| field item menu, full inventory | 86 | 78 |
| shop sell | 60 | 52 |
| field, many windows | 55 | 45 |
| battle, 4 party members | 31 | 30 |

The status screen is over budget **as measured**, with a level-4
character showing two techniques.  Extrapolating the largest real
technique list - 14 battle and 6 camp, capped by the window showing
about nine entries at a time - puts it near **143 cells**.  The pool
cannot reach that: even relocating every frame tile at $6D8-$6FF only
gets to 127.

The dialogue box's 128 tiles are not a way out.  Their use is
contended and unpredictable: across the five sampled screens the count
was 0, 53, 0, 128 and 0.  Anything built on them would corrupt the shop.

So the Japanese outcome repeats, for a different reason.  There the pool
was too small (34-50 tiles).  Here the pool is comfortable for four
screens out of five and impossible for the fifth.

### What is worth doing instead

Widening the fields costs **no VRAM at all** - it changes the nametable
layout, not the tile budget - and gets most of the way there:

| | characters in an item field |
|---|---|
| today, 10 cells fixed | 10 |
| widened to 14 cells, fixed | **14** |
| 10 cells with VWF | 15.5 |
| 14 cells with VWF | 21.7 |

Widening alone lands within a character and a half of what a full VWF
would have bought, for none of the risk, and the same technique already
worked on the Japanese ROM's technique window.

The dialogue and narration VWF stay as they are: they were never
constrained this way, because the dialogue box owns a private 128-tile
region with a RAM shadow and needs no pool.

### Confirmed: the status screen can never fit

The technique list is **two columns and does not paginate** - all 14
battle entries and 6 camp entries are on screen together.  So the worst
case is the upper estimate, confirmed rather than extrapolated:

| status screen | VWF cells | vs pool 87 |
|---|---|---|
| chrome only, no list at all | **88** | over by 1 |
| technique character (14 + 6) | 162 | over by 75 |
| skill character (7 + 1, with use counts) | 150 | over by 63 |

The **chrome alone exceeds the pool**.  Name, class, level, stat labels
and equipment come to 88 cells before a single list entry is drawn.  No
scoping, no case pass and no frame-tile reclamation changes that.

The content is also the wrong content.  Technique names top out at five
characters and are transliterations, not truncations - they do not want
more room.  The real truncations are elsewhere:

| | max | truncated |
|---|---|---|
| techniques | 5 | no |
| equipment on the status screen | 6 | yes |
| skills | 8 | yes |
| items | 10 | yes |

Twenty technique entries consume the pool while the names that actually
need help sit in the item, skill and equipment fields.

**Widening is therefore the right answer, and not merely the cheaper
one.**  It costs no VRAM, so it works on the status screen too - the one
place a pool can never reach.

### Correction: the 97-cell screen was not the status screen

`ps4us_restastresstest` is the field **healing** screen - party list,
"WHO", "RES is used!", "fully recovered!".  The status screen is
`ps4us-fieldstresstest` (Rune, WIZARD, LV, STRNGTH/MENTAL/AGILITY,
SKILL BTL / SKILL CAMP), and it measures **55** VWF cells, not 97.  The
claim that "the chrome alone is 88 cells" was measured on the wrong
screen and is withdrawn; the status screen's chrome is **46**.

Corrected worst cases against the 87-tile pool:

| screen | VWF cells | |
|---|---|---|
| status, populated, technique character | 113-120 | over by 26-33 |
| status, populated, skill character | 102-108 | over by 15-21 |
| field healing (measured) | 97 | over by 10 |
| field item menu, full inventory | 86 | fits |
| shop sell | 60 | fits |
| battle, 4 party | 51 | fits |

Still over, but by far less than the 75 previously claimed.  With the 28
reclaimable frame tiles at $6D8-$6FF the pool reaches about 115, at which
point title case brings the skill character (102) inside and leaves the
technique character (113) marginal.

So the menu VWF is **not** clearly infeasible.  It is marginal, and
depends on three things that were being treated as independent: the case
pass, frame-tile reclamation, and how long technique names need to be.

### Technique names are truncated too

The field is not the constraint - the window is about 11 cells wide, and
`FLAELI` leaves 5 cells free before the frame.  The constraint is that
the window **splits into two columns** once the list is long, giving each
name roughly 5 cells.  Several US names are clipped to fit that: `Gires`
and `Nares` for seven-character originals.  So widening cannot be scoped
to items and skills; the technique window needs it too, and there the
two-column split, not window width, is what has to give.

## Reuse changes the answer: the menu VWF fits

Two savings, both computable rather than estimated.  Fields are
cell-aligned, so every name starts at pixel phase 0 and identical strings
compose to byte-identical tiles - dedup needs no phase bookkeeping.

**Name-level:** the same string drawn twice costs one copy.  The camp
technique list is a subset of the battle list, and a full inventory holds
many repeated items.

**Tile-level:** identical 8x8 tiles recur across *different* names, since
shared prefixes at the same phase compose identically (`Res` and `Rever`
share their first tile).

Measured from the savestates, counting only name fields as pool
(labels, numbers, LV/HP/TP stay on the shared fixed font):

| screen | naive | name-dedup | tile-dedup |
|---|---|---|---|
| field healing | 71 | 59 | **37** |
| field item menu, full inventory | 77 | 28 | **24** |
| shop sell | 57 | 18 | **18** |
| battle, 4 party | 31 | 31 | **31** |
| status screen (sparse) | 20 | 19 | **18** |

Modelling the populated technique list - 14 battle plus 6 camp, clipped
forms restored, longest `Rasaresta`:

| | cells |
|---|---|
| naive | 77 |
| name-dedup | 53 |
| **tile-dedup** | **46** |

So the worst case on any screen is roughly **64 tiles** (populated
technique status screen, list plus chrome), against a pool of 79 with
digits and uppercase fixed, or 105 with digits alone.  It fits with
headroom, which is the first time that has been true.

### Correcting the earlier figure

The 112-132 estimate that made this look impossible was wrong.  It priced
every technique at `Rasaresta` length; the real list is mostly short
(`Zan`, `Anti`, `Tsu`), and composing it properly gives 77 naive before
any dedup at all.  Modelling a uniform worst case instead of the actual
distribution overstated the demand by about 60%.

### What it costs to implement

Dedup means allocating by **content** rather than by destination: hash the
composed tile, reuse the slot if it is already resident, otherwise take
the next free one.  That is the same hash-table shape as the trace
build's destination-keyed allocator, keyed differently.

Name-level dedup alone leaves the worst case near 71 against a pool of
79 - workable but thin.  Tile-level is what buys the headroom.

The open question is invalidation: when the table is reset.  Reset too
eagerly and dedup stops paying; too late and a stale tile survives into a
screen that no longer draws that string.  Resetting per screen transition
is the obvious answer and needs checking against how windows are torn
down.

## Menu VWF: the design, with real numbers

Using the actual technique list (14 battle, 6 camp, longest `Rasaresta`
at 9 characters):

| | tiles |
|---|---|
| naive | 85 |
| name-dedup | 60 |
| **tile-dedup** | **52** |

The camp window costs **nothing**: all six of its names already appear in
the battle list, so every one of its tiles is a reuse.  Prefix sharing
does the rest - `Giresta`, `Giglanz` and `Gizan` share their first tile;
`Raresta`, `Razan` and `Reversa` share theirs.

Worst case across every measured screen, with name-level dedup and only
name fields drawn from the pool, is about **70 tiles against a pool of
79**.  Tile-level dedup takes it to about 62.

### Invalidation: mirror the window stack

`Window_Create` pushes a saved plane map onto a bump allocator
(`Win_Saved_Plane_Maps_End`, starting at $6040) and increments
`Windows_Opened_Num`; `Window_Destroy` pops it and **restores the
nametable underneath**.  A strict LIFO.

The pool follows the same discipline: record the pool's high-water mark
on create, roll back to it on destroy.  A restored nametable can then
never reference a freed tile, because everything the restored window drew
lies below its own mark.  This is the same structure the engine already
uses for its plane maps, and it removes the stale-entry problem that sank
the Japanese attempt by construction rather than by care.

### LoadWindowTiles cannot grow

Like `RunText`, it dispatches control codes through
`jmp Win_CtrlCodesJmpTbl(pc,d7.w)` - an 8-bit displacement with about 30
instructions already inside it.  The call site has to stay the same size
or shrink, so the work goes in the called routine and the result comes
back in a register, exactly as `VWFDia_DrawGlyph` returns its wrap flag
in d5.

### Order of work

String-level dedup first: it is simple, verifiable, and 70-of-79 fits.
The table is keyed so tile-level can be added later without redesign, and
that is the fallback if an unmeasured screen overruns.

### Tile-level dedup is required, not optional

Adding `Ruckkehr` and `Hinaus` to the camp list changes the conclusion.
Both are new strings, so name-level dedup cannot touch them:

| | tiles | + chrome | vs pool 79 |
|---|---|---|---|
| name-dedup | 70 | ~80 | over by 1 |
| **tile-dedup** | **61** | ~71 | fits, 8 spare |

Two names were enough to push string-level dedup past the pool.  So the
allocator keys on composed tile content from the start rather than on the
string, and the earlier plan to add that later is dropped.

### The allocator

`vwf/vwfmenu.asm`.  Allocation is by content: `VWFMenu_Alloc` takes a
tile's 8 bytes of 1bpp source, scans the resident keys, and either
returns the existing slot or appends a new one.  The first long rejects
almost every miss, so the scan is cheap in practice.

Exhaustion returns **-1** rather than wrapping.  Handing back a tile that
belongs to another string would corrupt text somewhere unrelated to the
cause; a missing glyph points straight at the pool.

`VWFMenu_Mark` and `VWFMenu_Release` mirror the window stack -
`Window_Create` records the pool's high-water mark before incrementing
`Windows_Opened_Num`, `Window_Destroy` rolls back to it after
decrementing.  Nothing a restored nametable references can have been
freed.

Verified by executing the assembled code: dedup hits, keys differing only
in their last byte stay distinct, the pool fills to exactly 79, resident
keys still resolve when full, and the 80th allocation returns -1.

### Still outstanding before the renderer

`VWFMENU_TILE0 = $6A5` with 79 slots spans $6A5-$6F3, which **overlaps
the frame graphics at $6D8-$6FF**.  Only 12 of those 40 tiles were seen
in use, so relocating them to the top of the bank frees the range - but
that relocation is a prerequisite, not a detail, and the constants
currently assume it has happened.

### $7C0 is the numeric font, and that helps

Decoding the on-screen references into $7C0-$7FF shows what they are:
`10`, `3`, `7`, `4` and `:` separators - the HP/TP readouts in battle and
the stat values on the status screen.  It is a live font copy, not a
spare one, so it cannot host anything.

But it settles a question in our favour.  **Numbers never come from the
$680 bank at all.**  The bank's fixed-font requirement is therefore only
the uppercase letters that labels use - 22 glyphs measured across every
screen, not the 36 previously reserved for uppercase plus digits.

### Frame audit, 32 savestates

19 of the 40 frame tiles are used, scattered across the range:
$6D9-$6DA, $6DD-$6DE, $6E3, $6E6-$6EA, $6F1, $6F3-$6F5, $6F7-$6FA, $6FE.
Compacted to the top of the bank they occupy $6ED-$6FF.

### Resulting layout

| range | contents | tiles |
|---|---|---|
| $680 | blank, the space | 1 |
| $681-$696 | label glyphs, packed via a code->tile map | 22 |
| **$697-$6EC** | **pool** | **86** |
| $6ED-$6FF | frames, compacted | 19 |

86 against a worst-case demand of about 72 - roughly 16% headroom, which
is the first configuration with real margin rather than a tile or two.

Two things this depends on, both flagged rather than assumed: the frame
set is 19 across 32 savestates but unsampled screens could use more of
the 21 never seen, and every frame tile that turns up shrinks the pool
one-for-one.  And packing the label glyphs needs a code->tile map in the
renderer, since codes cannot be compacted without one.

### Pool wired into the window lifecycle

`VWFMenu_Mark` is called from `Window_Create` after the plane map is
backed up and before `Window_Draw` runs, while `Windows_Opened_Num` still
holds the depth this window will occupy.  `VWFMenu_Release` is called
from `Window_Destroy` immediately after the depth is decremented, so it
reads the same index its matching Mark used, and before the nametable
underneath is restored.

Verified by execution: marks land at the right depth, release rolls the
pool back to the matching mark, and a nesting depth beyond the tracked
range leaves the pool untouched rather than corrupting a slot.

The allocator was re-verified at the settled pool size of 86.  An earlier
run reported a failure that was the test holding a stale slot count of
79, not a fault in the code - worth noting because the symptom looked
identical to a real overflow bug.

### Remaining before the menu VWF renders anything

1. the fixed map - which label glyphs are needed, packed into $681-$696
2. frame relocation into $6ED-$6FF, freeing the pool range
3. the composer: build a string's tiles, allocate each, queue the DMA,
   write the nametable entries
4. hook `LoadWindowTiles` and `loc_27DB9C` together, byte-neutrally

### The fixed label set, and the final layout

Extracting label text needed care: more than half the savestates in the
folder are from the **Japanese** ROM, and decoding those with the US
charset produces convincing nonsense (`frw`, `eq`, `8?LL`).  Filtering to
the twelve US states, and separating chrome from content - `MONOMATE`,
`ANTIDOTE`, `FLAELI` are names that will be drawn proportionally, not
labels - gives the real set.

22 glyphs cover every label seen: `A B C E G H I K L M N O P Q R S T U V
W Y :`.  They are packed into 26 slots, leaving 4 spare for labels not
yet sampled, and they keep the **shipped artwork**, so chrome renders
exactly as it always has.

| range | contents | tiles |
|---|---|---|
| $680 | blank, the space | 1 |
| $681-$69A | packed label glyphs (22 used, 4 spare) | 26 |
| **$69B-$6EC** | **pool** | **82** |
| $6ED-$6FF | frames, compacted | 19 |

82 against a worst case near 72.  `tools/menufixed.py` emits the packed
art and a 128-byte code->slot map; `$FF` marks a code that is not drawn
fixed-width, which is how the renderer will tell chrome from content.

All four suites - dialogue, narration, allocator, window marks - pass
against this layout.

## Labels go proportional too, and the colon settles the alignment

Keeping labels fixed-width looked necessary because padded labels align
their colons.  The better framing: **the colon belongs to the numeric
field, not the label.**  The numbers allow three digits and the colon
sits against the third digit, so a left-aligned proportional label beside
a right-aligned fixed colon-and-digits keeps every column.

Expanding the abbreviations is then not merely free but cheaper, because
small caps are 5.08px against 6.08 for true caps:

| | | |
|---|---|---|
| `STRNGTH` 6 cells | -> | `Strength` 5 |
| `MOTAVIAN` 7 cells | -> | `Berserker` 6 |
| `WIZARD` 5 cells | -> | `Wizard` 4 |

So the design drops the fixed-label region entirely: the colon stays
fixed, everything else through `LoadWindowTiles` is proportional, and
there is no chrome-versus-content distinction for the renderer to make.

### Frame relocation is not contained

The window frame itself is only **four** tiles - $6E9, $6EA, $6F3 and the
blank at $680 - with V and H flip bits generating every corner and edge.
But the 19 frame-range tiles seen in VRAM come from 16 distinct tiles
across **86 immediate sites**, and the lowest ones in use ($6D9, $6DA,
$6DD, $6DE, $6E3) appear in neither immediates nor `dc.w` data, so they
are computed at runtime.  Relocating them is not a contained edit and
would risk breaking window furniture everywhere.

### The budget is one tile short

| | tiles |
|---|---|
| **needed**: status screen, maximum techniques, labels expanded | **89** |
| pool with frames untouched, $682-$6D7 | 86 |
| + colon moved to the $7C0 numeric font | 87 |
| + $6D8, never referenced across 32 savestates | 88 |

One short, on the worst screen in the game.  Options, none of which need
the relocation: trim a label or two, shorten one technique name, or let
the allocator's -1 stand and accept a missing glyph on that one screen.

## The composer

`VWFMenu_DrawString` composes a run 1bpp into `VWFMenu_Scratch`, then for
each cell gathers the eight row bytes, allocates by content, and - only
when the slot is newly taken - expands to 4bpp and pushes the tile
**straight to VRAM through the data port**.  Nothing is staged, so no
buffer can be overwritten before a queued DMA reads it.  That is the bug
that broke the Japanese attempt, and here it cannot arise.

Expansion reuses `VWFDia_NibExp`: the shift-0 entry for a byte gives one
`$1` per ink pixel, and `$EEEEEEEE | mask` turns paper into ink because
`$E | $1 = $F`.  The same trick as the dialogue box, the same table.

Pool exhaustion writes the blank tile rather than reusing a slot that
belongs to another string.  A gap points at the pool; a wrong tile points
anywhere.

### Two register-contract bugs, caught before testing

The first draft saved `a0-a4` and restored them, which would have thrown
away `a1`'s advance - the caller's whole result.  It also clobbered `a6`,
the VDP port, which `LoadWindowTiles` does not save either, so it belongs
to a caller further out.  Both are the same class of mistake that cost
three debugging rounds on the Japanese ROM.  `a0` and `a1` are now
declared results and excluded from the save; `a6` is saved; `a0` is
parked on the stack across the cell loop because `VWFMenu_Alloc` needs
it.

### Verified by execution

Composed tiles match an independent reference bit-for-bit; a redraw of
the same string allocates nothing new and yields identical nametable
entries; `a0` is left on the terminator.

The sharing rule is confirmed empirically, and it is the one the budget
depends on: `Gizan` reuses a tile from `Giresta` because both begin `Gi`
at phase 0, while `Giresta` shares nothing with `Resta` - same letters,
different phase, different tiles.

### What is left

Hooking `LoadWindowTiles` and `loc_27DB9C`.  They must change together,
byte-neutrally, since both draw off the $680 base.

## Hooked: the menu VWF renders

Both renderers now hand their runs to `VWFMenu_DrawString`.  The split is
the one both of them already made: a code below $80 is text and composes
proportionally, a code at $80 or above is window furniture and takes the
stock fixed path.  Conveniently both callers map a high code to tile
$740, and d2 already carries +$680, so +$C0 reaches it from either.

`LoadWindowTiles` shrank from 12 bytes to 8 at the call site, so its
pc-relative control-code table moved **closer**, never further - the
constraint that has bitten this project three times now.

Three branches had to widen to `.w` as code shifted around them,
including one pre-existing `bra.s` in `loc_27DB9C` that had been
comfortably in range until 14 bytes appeared in front of it.

### A latent RAM overlap, caught by a stale test

The allocator suite failed after the rebuild.  The immediate cause was
the test holding a stale slot count - the same false alarm as before -
but checking it surfaced a real bug: `VWFMenu_Keys` holds
`VWFMENU_SLOTS * 8` bytes, and raising the pool from 82 to 107 grew the
array from $290 to $358, pushing its end from +$3D0 to +$498 and **over
`VWFMenu_Scratch` at +$400**.

That would only have shown up once about 82 slots were allocated - on the
busiest screen in the game, with composition and allocation corrupting
each other.  The scratch now starts at +$500.

Worth noting the shape of it: no test could have caught this, because the
allocator and the composer were each verified in isolation and the
overlap needs both, at depth.  It came from re-reading a constant, not
from a failing assertion.

All six suites pass on the hooked build: composer, allocator, window
marks, dialogue bit-exact, dialogue edges, narration.

## The pool is too small, measured rather than modelled

The status screen renders with text missing - HP/TP labels, technique
names, the slash in skill counts, the equip arrows.  Reading the
savestate settles the cause: `VWFMenu_PoolTop` is **87 of 87**, and the
window marks show **eight nested windows** open at once
(0, 26, 32, 33, 39, 39, 48, 75).  Every missing glyph is the
`DrawString_Full` path emitting a blank instead of stealing a tile from
another string.

Nothing is unhooked.  `$681` is referenced zero times on that screen, so
no renderer is still reading stock font tiles.  The design works; the
budget does not.

**And it is wrong by a wide margin.**  That screen is Chaz at level 1,
about as empty as a status screen gets, and it exhausts the pool.  The
earlier figures of 72 and 89 came from modelling single screens in
isolation; no measurement was ever taken of a screen with eight windows
stacked, which is what the status screen actually builds.  Estimating
per-screen and never checking the nesting was the error.

The bank cannot absorb it: $680 is the blank, $6D9-$6FF is frame
furniture across 86 immediate sites plus runtime-computed references, and
that leaves the 87 tiles the pool already has.

## The pool was leaking, not too small

Instrumenting real demand - dedup keys for 200 tiles while only 87 have
VRAM - gave the answer:

| screen | peak | vs VRAM 87 |
|---|---|---|
| main menu | 102 | over by 15 |
| status | 107 | over by 20 |
| battle items, field items, shop sell | **200+** | saturated the counter |

The item lists were unbounded, and the window marks showed why: all eight
read 200, so the pool was already full before those windows opened.

**Tiles were released only when a window was destroyed, but content
changes inside a window.**  Scrolling a list redraws it, allocating for
each newly revealed name and freeing nothing, because no window closes
while scrolling.  Every scroll leaked.  What looked like a capacity
crisis was mostly that.

### Reference counting

A tile is now freed when the last nametable cell referring to it is
overwritten.  `VWFMenu_Deref` reads the outgoing entry before each write
and drops its reference; `VWFMenu_Alloc` prefers a slot whose count has
fallen to zero before growing the pool, and never takes one below the
current window's mark, so an inner window cannot evict an outer one's
tiles.  `VWFMenu_Release` clears the counts it owned when a window is
destroyed.

The pool now holds what is on screen rather than everything ever drawn.

Verified by execution: sixty redraws of fifteen different strings into
the same cells peak at **six** tiles.  Before, that pattern grew without
limit until it saturated.

### A silent no-op, worth recording

One edit in that change did nothing: the search text said `bmi.w` where
the file said `bmi.s`, and `str.replace` does not complain when it
matches nothing.  The build still assembled, so only an undefined symbol
elsewhere revealed that the deref had never been wired in.  Every
replacement in that script now asserts first.

## A second font copy nobody was using

The pool was carrying its own labels.  `HP`, `TP`, `EX`, `NX`, `LV`,
`MST` and `AGE` were being composed into pool tiles like any other
string, at a measured cost of **sixteen slots** — sixteen per cent of the
bank — for seven words that never change.

They did not need to be there.  Charset codes 1-64 have a permanent
second copy of the font at VRAM `$7C0`-`$7FF`, holding `A`-`Z`, `0`-`9`,
`-`, `!`, `?` and `:`.  It is the copy the numeric fields already draw
from, and it is byte-identical to `Font.bin` in the stock ROM and in
every VWF savestate captured so far.  Decoding the status screen's plane
against it reads back the actual stat values, which is what confirmed the
mapping:

    tile = $7C0 + code - 1

So those labels cost nothing at all.  Drawing them from `$7C0` hands
sixteen slots back to the pool without spending a single tile in the
`$680` bank, and removes sixteen allocations from every status draw —
which also shrinks the save/remap record sets and the sweep pressure
behind the slowdown.

`/` was already free: the uses separator comes from the same bank, drawn
by the numeric path, not the pool.

### The test is on length, not on case

The obvious rule is "all capitals means a label".  It is wrong.
`HUNT-KNIFE` and `LTHR-HELM` are all capitals too, and the rule would
re-truncate the very names this project exists to fix.

The rule is instead **at most three non-space characters, all in codes
1-64**.  That selects the seven labels and provably nothing else: no item
or technique name is that short.  Lowercase is not resident past code 64
(`a`-`h` only), so a mixed-case label such as `Combat` never qualifies
and keeps its proportional path.  Drawing is one cell per character,
which is stock's own layout, so no column can shift.

Gated behind `vwf_menu_fixedlabels`.

### The interpreter was lying about N

The first run of the test said `HP` took the compose path.  It had not:
`emu68k.py`'s `move.b (An)+,Dn` set `Z` but never `N`, so the `bmi` that
ends the scan could not fire on the `$FF` terminator.

An audit for the same shape found `N` is essentially **never** computed
anywhere in the interpreter.  Two forms are fixed here because this test
needed them.  The rest is a real gap: any earlier result that turned on
`bmi`/`bpl` after a move may have been wrong, and the honest repair is a
validity flag on `N` so the interpreter raises on an uncomputed branch
rather than guessing — which is the rule it already follows for opcodes.
