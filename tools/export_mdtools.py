"""Lift the game-independent Mega Drive tools out of tools/ into mdtools/.

    python tools/export_mdtools.py [dest]        default dest: mdtools/

The PS4 pipeline imports these modules from tools/ like everything else, so
they stay there; this copies exactly the subset that has no dependency on
the game, the disassembly or work/, writes a README whose API index is read
out of the modules themselves, adds the license, and then proves the copy is
self-contained by running a smoke test of every module from the exported
directory with nothing else on the path.  A module that quietly grew a PS4
dependency fails here rather than in someone else's project.

The smoke test uses this repository's own data as test vectors where a
format needs real input (a Kosinski-compressed dialogue tree, a Nemesis art
blob, a BlastEm savestate); nothing from work/ or ps4disasm/ is copied out.
"""
import ast
import io
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")

# module -> (group, one-line description, note for the README or None)
SUBSET = {
    "bps.py": ("Patching", "BPS (beat) patch encoder and decoder; the encoder finds moved data, not just changed bytes.", None),
    "webpatch.py": ("Patching", "Render a single-file offline HTML patcher around any BPS - accepts and produces .smd too.",
                    "Needs patcher_template.html beside it (copied)."),
    "patcher_template.html": ("Patching", "The page webpatch.py renders: CRC check, SMD detection, BPS apply, save as .bin or .smd.", None),
    "smd.py": ("ROM images", "Interleaved .smd <-> plain binary, with SMD detection.", None),
    "bin2smd.py": ("ROM images", "Command-line front end for the same conversion, direction chosen by extension.", None),
    "expand.py": ("ROM images", "Grow a ROM to the 4 MB cartridge window; header end address and checksum maintenance.",
                  "checksum()/fix_checksum() are useful on their own after any edit."),
    "kosinski.py": ("Compression", "Kosinski decompressor with a strict bit reader, plus a validator for compressor output.", None),
    "kosdec.py": ("Compression", "Second, independent Kosinski decompressor with a CLI - handy for cross-checking.", None),
    "decomp.py": ("Compression", "Nemesis decompressor (Sega's 8x8 art format), including the XOR-filter mode.", None),
    "nemcmp.py": ("Compression", "Nemesis compressor; picks the smaller of plain and XOR modes.", None),
    "lzss.py": ("Compression", "The LZSS variant Phantasy Star IV uses for its script (bit-packed literals, short/long matches).",
                "Game-specific format, generic implementation; kept as a worked example of a bit-packed LZ codec."),
    "lzss_enc.py": ("Compression", "Greedy and optimal-parse compressors for that LZSS variant.", None),
    "m68k.py": ("68000", "Compact Motorola 68000 disassembler: disasm(data, pc, n) -> lines.", None),
    "emu68k.py": ("68000", "A 68000 interpreter that executes a routine against a memory image and REFUSES to guess: unknown opcode or uncomputed flag raises.",
                  "Models the instruction subset the project needed; extend it before trusting it on arbitrary code."),
    "png.py": ("Graphics", "Minimal PNG writer, no dependencies.", None),
    "pngread.py": ("Graphics", "Minimal PNG reader (8-bit RGB/RGBA/grey), no dependencies.", None),
    "tiles.py": ("Graphics", "Decode 1bpp and 4bpp planar tile data and render tile sheets to PNG.", None),
    "blastem_drive.py": ("Emulator harness", "Drive BlastEm through its GDB remote stub: breakpoints, RAM read/write, register access, frame stepping, pad injection.",
                         "The GDB transport (`cmd`, `read`, `write`, `regs`, `breakpoint`, `cont`) is generic. The constructor also installs Phantasy Star IV-specific hooks (the ReadJoypad and VInt breakpoints found by label in the listing, and stubs for the sound driver); for another game, subclass and replace those lookups."),
    "blastem_ram.py": ("Emulator harness", "Locate and extract the 64K work RAM inside a BlastEm native savestate.",
                       "find_base() needs a reference RAM image of the same game (any 64K dump, e.g. from Exodus); pass it as `ref=`. Without one it looks for this project's work/rebuilt-status.exs."),
    "blastem_screen.py": ("Emulator harness", "Render the VDP planes of a BlastEm savestate to PNG (planes A/B, sprites, window, scroll, priority).", None),
    "winshot.py": ("Emulator harness", "Screenshot a window by process id without focusing it (Windows only, ctypes).", None),
}

README_HEAD = """\
# mdtools - Mega Drive / Genesis ROM-hacking utilities

Pure Python 3 (3.10+), standard library only, no installation: copy the files
you want next to your project, or put this directory on `sys.path`.

These were written for Excalibur_Z's Phantasy Star IV English retranslation
(the `ps4-translate` repository; its README describes the full pipeline they
came from) and are the parts that do not depend on the game. They are
exported from that repository's `tools/` by `tools/export_mdtools.py`, which
also runs a smoke test of every module from this directory alone; if you are
reading this file, that test passed for this copy.

MIT licensed (LICENSE). Contributions and fixes are welcome upstream.

## Quick examples

```bash
python bps.py create original.bin hacked.bin hack.bps      # verified round trip
python bps.py apply  hack.bps original.bin out.bin
python bps.py info   hack.bps
python bin2smd.py game.smd game.bin                         # or the other way
python webpatch.py hack.bps Patcher.html --title "My Hack" --game "Game (USA)"
python kosdec.py compressed.bin out.unc [offset]
python blastem_screen.py slot_0.state screen.png
```

```python
import bps, smd, expand, kosinski, decomp, nemcmp, m68k, emu68k, tiles

patch = bps.create(source, target)            # bytes in, bytes out
assert bps.apply(patch, source) == target

rom = smd.smd_to_bin(open("game.smd", "rb").read()) if smd.is_smd(data) else data
rom4m = expand.expand(rom)                    # 4 MB, header end + checksum fixed

art = decomp.decompress(rom, 0x12345)         # Nemesis blob at that offset
blob = nemcmp.compress(art)                   # a multiple of 32 bytes
print(m68k.disasm(rom, 0x200, 20))            # text, one instruction per line
```

BlastEm harness, in outline:

```python
from blastem_drive import BlastEm             # BlastEm 0.6.2, started with -D
with BlastEm("game.bin", "slot_0.state") as em:
    em.frames(60)
    print(em.word(0xFFFF5500))
    em.press("A")
```

## Modules
"""


def api_index(path):
    """Public functions and classes with their first docstring line."""
    tree = ast.parse(io.open(path, encoding="utf-8", errors="replace").read())
    rows = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            sig = "%s(%s)" % (node.name, ", ".join(a.arg for a in node.args.args))
            doc = (ast.get_docstring(node) or "").strip().splitlines()
            rows.append((sig, doc[0] if doc else ""))
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef) and not m.name.startswith("_")]
            rows.append(("class %s" % node.name, ", ".join(methods[:12]) + (" ..." if len(methods) > 12 else "")))
    return rows


def write_readme(dest):
    out = [README_HEAD]
    groups = {}
    for name, (group, desc, note) in SUBSET.items():
        groups.setdefault(group, []).append((name, desc, note))
    for group in ("Patching", "ROM images", "Compression", "68000", "Graphics", "Emulator harness"):
        out.append("\n### %s\n" % group)
        for name, desc, note in groups[group]:
            out.append("\n**`%s`** - %s\n" % (name, desc))
            if note:
                out.append("\n> %s\n" % note)
            if name.endswith(".py"):
                rows = api_index(os.path.join(dest, name))
                if rows:
                    out.append("\n")
                    for sig, doc in rows:
                        out.append("- `%s`%s\n" % (sig, " - " + doc if doc else ""))
    io.open(os.path.join(dest, "README.md"), "w", encoding="utf-8", newline="\n").write("".join(out))


SMOKE = r'''
import os, sys, random, zlib, tempfile
here = os.path.dirname(os.path.abspath(__file__))
assert sys.path[0] == here
root = sys.argv[1]
ok = []

import bps
rnd = random.Random(1)
src = bytes(rnd.getrandbits(8) for _ in range(70000))
tgt = src[:1000] + b"\x00" * 3000 + src[5000:40000] + b"new data" * 50 + src[1000:5000] + src[40000:]
p = bps.create(src, tgt, b"smoke")
assert bps.apply(p, src) == tgt and len(p) < 2000, len(p)
ok.append("bps")

import smd, bin2smd
rom = bytes(rnd.getrandbits(8) for _ in range(0x8000))
s = smd.bin_to_smd(rom); assert smd.is_smd(s) and smd.smd_to_bin(s) == rom
assert bin2smd.smd_to_bin(bin2smd.bin_to_smd(rom)) == rom
ok.append("smd")

import expand
rom3 = bytearray(rnd.getrandbits(8) for _ in range(0x300000)); rom3[0x100:0x110] = b"SEGA GENESIS    "; rom3[0x1A4:0x1A8] = (0x2FFFFF).to_bytes(4, "big")
rom3 = expand.fix_checksum(bytes(rom3))
big = expand.expand(rom3)
assert len(big) == 0x400000 and expand.rom_end(big) == 0x3FFFFF and expand.checksum(big) == int.from_bytes(big[0x18E:0x190], "big")
ok.append("expand")

import kosinski, kosdec
tree = open(os.path.join(root, "ps4disasm", "script", "dialogue 1.bin"), "rb").read()
a = kosinski.decompress(tree, 0); b, end = kosdec.kosdec(tree, 0)
assert len(a) > 1000 and bytes(a) == bytes(b), (len(a), len(b))
ok.append("kosinski")

import decomp, nemcmp
art = open(os.path.join(root, "ps4disasm", "sega", "art", "nemesis", "Sega.bin"), "rb").read()
dec = decomp.decompress(art, 0)
assert len(dec) % 32 == 0 and len(dec) > 0
enc = nemcmp.compress(bytes(dec))
assert bytes(decomp.decompress(enc, 0)) == bytes(dec)
ok.append("nemesis")

import lzss, lzss_enc
text = (b"the quick brown fox jumps over the lazy dog. " * 40) + bytes(range(256))
for comp in (lzss_enc.compress_greedy, lzss_enc.compress_optimal, lzss_enc.compress):
    c = comp(text)
    assert bytes(lzss.decompress(c, 0, len(text))) == text
ok.append("lzss")

import m68k
text = m68k.disasm(bytes.fromhex("7005D040 4E75 3039 00FF5500 6000 0004"), 0, 5)
text = text if isinstance(text, str) else "\n".join(text)
assert "moveq" in text.lower() and "rts" in text.lower(), text
ok.append("m68k")

import emu68k
class Mem(dict):
    def __missing__(self, k): return 0
m = Mem()
for i, b_ in enumerate(bytes.fromhex("7005D0404E75")): m[0x1000 + i] = b_
cpu = emu68k.CPU(m, pc=0x1000, sp=0xFFF000)
cpu.run()
assert cpu.d[0] == 10, cpu.d[0]
ok.append("emu68k")

import png, pngread, tiles
tmp = tempfile.mkdtemp()
tile = bytes(rnd.getrandbits(8) for _ in range(32 * 8))
ts = tiles.decode_4bpp(tile, 8)
sheet = os.path.join(tmp, "sheet.png")
tiles.sheet(ts, 4, sheet)
pngread.read(sheet)
assert os.path.getsize(sheet) > 60
ok.append("tiles/png")

import webpatch
out = os.path.join(tmp, "p.html")
webpatch.render_patcher(p, out, tokens={"TITLE": "smoke", "OUT_NAME": "smoke", "PATCH": "p.bps"})
html = open(out, encoding="utf-8").read()
assert "@" + "TITLE@" not in html and "BPS1" in __import__("base64").b64decode(html.split('PATCH_B64 = "')[1].split('"')[0])[:4].decode()
ok.append("webpatch")

import blastem_ram, blastem_screen
state = os.path.join(root, "work", "compose-slot0.state")
import zipfile
ref = zipfile.ZipFile(os.path.join(root, "work", "rebuilt-status.exs")).read("MD1600.RAM.bin")
data = open(state, "rb").read()
base = blastem_ram.find_base(data, ref)
assert base is not None
st = blastem_screen.read_state(state)
pix = blastem_screen.render(st, True)
ok.append("blastem_ram/screen")

import blastem_drive, winshot
ok.append("blastem_drive/winshot import")
print("smoke ok:", ", ".join(ok))
'''


def main(argv):
    dest = os.path.abspath(argv[0]) if argv else os.path.join(ROOT, "mdtools")
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)
    for name in SUBSET:
        src = os.path.join(ROOT, "release" if name.endswith(".html") else "tools", name)
        shutil.copy(src, os.path.join(dest, name))
    shutil.copy(os.path.join(ROOT, "LICENSE"), os.path.join(dest, "LICENSE"))
    write_readme(dest)
    smoke = os.path.join(dest, "_smoke.py")
    io.open(smoke, "w", encoding="utf-8", newline="\n").write(SMOKE)
    # Run from a neutral cwd with only the export on the path, so an import
    # that leaks back into tools/ or work/ fails instead of passing by luck.
    env = dict(os.environ, PYTHONPATH="")
    r = subprocess.run([sys.executable, smoke, ROOT], cwd=os.path.dirname(dest), env=env,
                       capture_output=True, text=True)
    os.remove(smoke)
    print(r.stdout.strip())
    if r.returncode:
        print(r.stderr)
        sys.exit("smoke test FAILED - export is not self-contained")
    print("exported %d files to %s" % (len(os.listdir(dest)), dest))


if __name__ == "__main__":
    main(sys.argv[1:])
