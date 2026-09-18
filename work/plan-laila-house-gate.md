# Task: Laila greets you at her own house after she is gone

## Outcome (2026-09-10) - FIXED, player-confirmed on BlastEm

The hypothesis below was wrong: `treeport` dropped nothing. The US text has no
`$FA` gate either - US tree 10 `$31` begins `f4 02`, identical to the JP.

What the US actually does is `Event_ChazHouse` (ps4.asm, event `$3B`): if
`EventFlag_Zio` is set it calls `GetDialogueByID($31)` and pokes `$01` into
byte 1 of the message - the `$F4` operand - **in the RAM copy of the tree**.
Two BlastEm states on the Bugfix ROM (Alys alive / gone) differ in exactly
that one byte of `$FF3000+$DE6`.

Root cause in our build: with `dialogue_uncompressed = 1`, `GetDialogueByID`
returns a pointer into ROM (`Current_Dialogue_Tree`), so that poke is a write
to ROM and vanishes. Not a text bug and not a pipeline bug.

Fix: `Event_ChazHouse` under `if dialogue_uncompressed = 1` copies messages
`$31`+`$32` (the YesNo "no" branch) into the otherwise unused `Dialogue_Trees`
RAM buffer, patches the copy, and runs it via `Event_RunDialogue`. No text,
treeport, or `dialogue_full.json` change. It is the only site in the engine
that writes into a dialogue tree, so there is no second instance.

Build `77BE3D8666485BDFA3F85A9BE31C4695ED3DF0D42A08C780405AB6CA6A654BE2`,
11/11 tests, checkbuild clean. `tools/kosdec.py` (new) decompresses the US
`script/dialogue N.bin` trees; step 1 route (a) no longer needs writing.

Two corrections to the model below:

  1. `$FA` / `$F5` targets are RELATIVE, not absolute ids. `GetOffsetByID`
     counts `$FF` terminators forward from the current position, so
     `{ctl.FA:4201}` means "if flag $42 is set, skip to the NEXT message" -
     which is why `#0013`/`#0014` pair up. The "diverts to message $01, which
     is empty" reading is wrong, and the open sub-question dissolves:
     `{ctl.F5:0001}` = yes continues inline, no jumps to the next message.
     `tools/dialogue.py`'s comments are corrected accordingly.
  2. The forbidden speculative `$FA $42 $01` would have jumped to `$32`
     ("keep going a little longer?"), not to an empty message - still wrong,
     for a different reason.

The pipeline constraints (editing `dialogue N.asm` or `dialogue_full.json`
alone does not survive `treeport --write`) remain true and were not needed.

---

Phantasy Star IV JP->EN translation, `C:\Users\Mark\Claude Projects\ps4-translate`.
Assume no prior context. This task is confined to the DIALOGUE pipeline; it does
not touch the VWF tile pool, which another session owns. Do not edit
`ps4disasm/vwf/*`, `tools/menupool.py`, or `VWFMENU_*` constants.

## Symptom

Visiting Laila's house in Aiedo shows her portrait and "Home at last! / Shall we
rest for today?" - a free rest point - even after she has been struck by Zio's
Black Wave, and even after she dies. Player-confirmed on build `17335F08`.

The US release does NOT do this. In the US (`Phantasy Star IV [Bugfix v1.5].bin`
in the project root), the scene shows Alys while she is in the party and Chaz
once she is not, keeping the rest point either way. Player-confirmed by walking
the same save into the same house on that ROM.

Repro: any save after the Zio fight; enter Laila's house in Aiedo.

## What is established

**The gate idiom.** `TextCtrlCode_CheckEventFlag` (`$FA`) in ps4.asm:

    move.b (a0)+, d0        ; operand 1 = event flag id
    jsr (EventFlags_Test).l
    beq -> skip operand 2, keep drawing this message
    move.b (a0), d0         ; operand 2 = message id
    jsr (GetOffsetByID).l   ; flag SET -> jump to that message

So `{ctl.FA:4201}` = "if flag $42 is set, show message $01 instead".
NOTE `tools/dialogue.py`'s comment claiming `$FA` "ends the text and the two
bytes after it are read by the event interpreter" is WRONG. Fix that comment.

**The flag.** `EventFlag_Zio = $42` (ps4.constants.asm) - "Set when you fight Zio
for the first time", i.e. exactly when Laila leaves the party. Laila can never be
dismissed by the player, so this doubles as "not in the party".

**The pattern.** Thirteen messages in the Aiedo stream `lz1D1256` gate on `$42`:
`#0000 #0003 #0005 #0007 #0011 #0013 #0022 #0043 #0047 #0053 #0057 #0086` divert
to message `$01`; `#0029` diverts to `$02`. `#0013`/`#0014` are the clearest
pair: `#0013` carries `{ctl.FA:4201}` and is the Laila-present line, `#0014` is
the Rudy variant of the same NPC.

`lz1D1256#0049` - the house scene - has NO gate. Its raw JP bytes, from
`work/dialogue_full.bak.json`, begin `f4 02`, so the JP text never had one.

## The live hypothesis (NOT yet proven)

The missing gate is probably OURS, not the JP's.

`ps4disasm/script/dialogue N.asm` is the US tree structure (the US build
re-partitioned 26 JP streams into 43 trees - see `tools/usimport.py`).
`tools/treeport.py --write` writes our JP-derived English OVER the US message
bodies, and `tools/sourcebuild.py` runs it as its FIRST step.

`treeport` has an asymmetry:

  * it reports controls WE have that the US lacks ("dropped to match it" - 22
    rows, all `$F9`/`$F4`/`$F2`/`$F7`, never an `$FA`);
  * nothing reports controls the US HAS that we lack. That case normally causes
    a skip, but only when a US counterpart exists to compare against.

`#0049` has `us: None` - `usimport` never paired it, because the US rewrote the
scene rather than translating it. So `theirs` was empty, `treeport`'s
"portraits against a blank US message" path accepted the port, and our ungated
text was written over the US slot. A gate there would vanish with no trace.

## Step 1: settle it

Get the US tree 10 message `$31` raw bytes and see whether it carries an `$FA`.

`compress_script.py` only compresses; there is no decompressor in the tree, and
the `script/dialogue N.bin.unc` files `koschk.asm` references do not exist.
Two routes:

  a. Write a decompressor for the tree format (see `ps4disasm/script/compress_script.py`
     for the encoder, and `koschk.asm` for how the game reaches the streams).
  b. Cheaper: have the player take a BlastEm savestate on the US ROM with that
     text on screen, and read the message bytes out of work RAM.
     `tools/blastem_ram.py` extracts the 64K work RAM from a BlastEm `.state`;
     `tools/poolpeak.py` shows the pattern for using it.

## Step 2: fix, once the US bytes are known

If the US gates it, mirror the US exactly - same flag, same target. If the US
uses a second message, append it at the END of the tree so no existing message
id shifts, and point the gate at it.

Intended shape (VERIFY the operands against the US first):

    ; $31
        dc.b $FA
        dc.b EventFlag_Zio, <target>
        dc.b $F4
        dc.b $02
        ... existing Laila text ...

    ; <target>  - appended at the end of the tree
        dc.b $F4
        dc.b $01                      ; Rudy
        ... same words ...

Put both under `if bugfixes=1` (already 1 in `ps4disasm/ps4.options.asm`), where
this project keeps its fixes to original bugs.

DO NOT apply a speculative `$FA $42, $01`. The siblings divert to message `$01`,
which is `dc.b $FF` - empty - so the house would go SILENT and lose its rest
point, where the US keeps the scene with Chaz. That trades a wrong portrait for
a lost feature.

## Pipeline constraints - both verified the hard way

  1. Editing `ps4disasm/script/dialogue 10.asm` DOES NOT WORK. `treeport --write`
     rewrites message bodies and `sourcebuild` runs it first, so the edit is
     silently reverted before assembly and the ROM hash does not move. Verified:
     a marker line inserted into `$31` was gone after `treeport --write`.
  2. Editing `work/dialogue_full.json` DOES NOT WORK either, on its own.
     `treeport` ports a message only while its engine-token count matches the US
     reference; adding `{ctl.FA:...}` changes that count and the message is
     skipped, leaving the old body. Verified the same way.

So landing any gate needs a `treeport` change - most likely an explicit
allowlist of message ids permitted to diverge from the US token profile. Add a
test pinning that the override applies to exactly the listed ids, so it cannot
become a general escape hatch.

## Open sub-question

`#0049` contains `{ctl.F5:0001}` and `TextCtrlCode_YesNo` reads those two bytes
as message ids - but `$00`/`$01` are the empty messages, which would make the
inline "Yeah, good idea..." unreachable. The scene demonstrably works, so this
is misread somewhere. Worth resolving before authoring a copy of the message;
building the new message by COPYING `$31` byte-for-byte (changing only the
portrait) sidesteps it.

## Build and verify

    python tools/sourcebuild.py          # regenerates, assembles, writes ps4en.bin
    for t in tools/test_*.py: python $t  # 11 files, all must pass
    python tools/checkbuild.py           # static invariants

Current baseline: `17335F08D47882B621E13DF27DD29F90EC25D0D2B24A6B2F3CB101FB08658A60`,
all tests green, nothing half-applied.

Build-tree trap: `sourcebuild.py` runs `checkbuild.py` BEFORE `build.bat`, and
checkbuild validates the PREVIOUS build's `ps4built.bin` against `ps4.lst`. An
interrupted build leaves those inconsistent and later runs fail inside checkbuild
with a misleading error. Recovery: copy `ps4disasm/ps4built.prev.bin` over
`ps4built.bin`, assemble once via Python `subprocess` (`cmd /c build.bat` from a
bash shell only prints the banner and does nothing), then run `sourcebuild.py`.

## Ground rule

Do not claim an emulator symptom fixed from static or harness evidence alone.
The player tests on BlastEm; a fix is not done until the house shows Rudy after
the Zio fight and Laila before it.
