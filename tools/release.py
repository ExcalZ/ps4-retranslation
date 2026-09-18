"""Package the retranslation for distribution: BPS patch + readme + zip.

    python tools/release.py 1.0 [--rom ps4en_retranslation.bin]

Produces, under release/:

    PS4_Retranslation_v1.0/PS4_Retranslation_v1.0.bps
    PS4_Retranslation_v1.0/Patcher.html
    PS4_Retranslation_v1.0/readme.txt
    PS4_Retranslation_v1.0.zip

The patch is created with Flips (flips/flips.exe) when it is present - its
encoder finds more matches than tools/bps.py (235 KB against 300 KB for
v1.0) - and with tools/bps.py otherwise.  Either way tools/bps.py re-applies
the result and the ROM must come back byte for byte.

Patcher.html is a single-file offline patcher rendered from
release/patcher_template.html with the BPS embedded as base64.  It exists
because most players' dumps are interleaved .smd files that Flips cannot
convert, and a BPS whose source is an .smd is either 2.5 MB (against a plain
target, since interleaving defeats the delta encoder) or emits a 4 MB .smd
whose header block count overflows a byte.  The page deinterleaves in the
browser, applies the one canonical patch, and offers the result as .bin or
re-interleaved .smd (the 4 MB .smd loads in BlastEm and Genesis Plus GX,
which size the data from the file rather than the header; verified 2026-09-17).

The readme is rendered from release/readme_template.txt.  Every number a
player can check - sizes, CRC32/MD5/SHA-1 of both ROMs, the internal Mega
Drive checksum, the release date - is a @TOKEN@ filled in from the files
themselves, so the text can never disagree with the patch beside it.  Edit the
template, not the rendered readme.

The source ROM is the stock US release (No-Intro "Phantasy Star IV (USA)",
CRC32 FE236442).  It is regenerated bit-exact by the unmodified upstream
disassembly with every option at 0; the copy this script expects is
work/ps4us_stock.bin, and its CRC32 is checked before anything is written.

Refuses to package if:
  - the ROM being shipped differs from ps4disasm/ps4built.bin (a stale copy
    was about to go out), unless --allow-stale is given
  - the stock ROM's CRC32 is wrong
  - re-applying the freshly written patch does not reproduce the ROM
"""
import datetime
import hashlib
import os
import re
import subprocess
import sys
import tempfile
import zipfile
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bin2smd
import bps
import webpatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "PS4_Retranslation"
STOCK = os.path.join(ROOT, "work", "ps4us_stock.bin")
STOCK_CRC = 0xFE236442
BUILT = os.path.join(ROOT, "ps4disasm", "ps4built.bin")
TEMPLATE = os.path.join(ROOT, "release", "readme_template.txt")
PATCHER = os.path.join(ROOT, "release", "patcher_template.html")
FLIPS = os.path.join(ROOT, "flips", "flips.exe")
OUTDIR = os.path.join(ROOT, "release")


def hashes(data: bytes) -> dict:
    return {
        "SIZE": "{:,}".format(len(data)),
        "CRC32": "%08X" % zlib.crc32(data),
        "MD5": hashlib.md5(data).hexdigest(),
        "SHA1": hashlib.sha1(data).hexdigest(),
    }


def md_checksum(rom: bytes) -> int:
    return sum(int.from_bytes(rom[i:i + 2], "big") for i in range(0x200, len(rom), 2)) & 0xFFFF


def make_patch(stock: bytes, rom: bytes, label: str) -> bytes:
    if not os.path.exists(FLIPS):
        return bps.create(stock, rom, label.encode())
    with tempfile.TemporaryDirectory() as tmp:
        s, t, p = (os.path.join(tmp, n) for n in ("s.bin", "t.bin", "p.bps"))
        open(s, "wb").write(stock)
        open(t, "wb").write(rom)
        subprocess.run([FLIPS, "--create", "--bps", s, t, p], check=True,
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        return open(p, "rb").read()


def render(template: str, tokens: dict) -> str:
    text = open(template, encoding="utf-8").read()
    for k, v in tokens.items():
        text = text.replace("@%s@" % k, v)
    left = re.findall(r"@[A-Z][A-Z0-9_]*@", text)
    if left:
        sys.exit("%s: unfilled token(s): %s" % (os.path.basename(template), ", ".join(sorted(set(left)))))
    return text


def main(argv):
    if not argv or argv[0].startswith("-"):
        sys.exit(__doc__)
    version = argv[0]
    rom_path = os.path.join(ROOT, "ps4en_retranslation.bin")
    if "--rom" in argv:
        rom_path = argv[argv.index("--rom") + 1]
    allow_stale = "--allow-stale" in argv

    stock = open(STOCK, "rb").read()
    if zlib.crc32(stock) != STOCK_CRC:
        sys.exit("%s: CRC32 %08X, expected %08X - not the stock US ROM"
                 % (STOCK, zlib.crc32(stock), STOCK_CRC))
    rom = open(rom_path, "rb").read()
    if os.path.exists(BUILT) and open(BUILT, "rb").read() != rom and not allow_stale:
        sys.exit("%s differs from %s - copy the fresh build over first, or pass --allow-stale"
                 % (rom_path, BUILT))
    stored = int.from_bytes(rom[0x18E:0x190], "big")
    if md_checksum(rom) != stored:
        sys.exit("internal checksum %04X does not match stored %04X" % (md_checksum(rom), stored))

    stem = "%s_v%s" % (NAME, version)
    folder = os.path.join(OUTDIR, stem)
    os.makedirs(folder, exist_ok=True)

    patch = make_patch(stock, rom, "%s v%s" % (NAME.replace("_", " "), version))
    if bps.apply(patch, stock) != rom:
        sys.exit("patch does not reproduce the ROM")
    patch_name = stem + ".bps"
    open(os.path.join(folder, patch_name), "wb").write(patch)

    tokens = {"VERSION": version, "PATCH": patch_name,
              "DATE": datetime.date.today().strftime("%d.%m.%Y"),
              "MDCHK": "%04X" % stored,
              "ROMEND": "0x%08X" % int.from_bytes(rom[0x1A4:0x1A8], "big")}
    for k, v in hashes(stock).items():
        tokens["SRC_" + k] = v
    for k, v in hashes(rom).items():
        tokens["OUT_" + k] = v
    for k, v in hashes(bin2smd.bin_to_smd(rom)).items():
        tokens["SMD_" + k] = v
    text = render(TEMPLATE, tokens)
    readme = os.path.join(folder, "readme.txt")
    # BOM + CRLF: Notepad-friendly, like the reference readme.
    open(readme, "wb").write(("\ufeff" + text.replace("\r\n", "\n").replace("\n", "\r\n")).encode("utf-8"))

    patcher = os.path.join(folder, "Patcher.html")
    webpatch.render_patcher(patch, patcher, PATCHER, {
        "TITLE": "Phantasy Star IV: The End of the Millennium",
        "SUBTITLE": "English Retranslation v%s" % version,
        "GAME": "Phantasy Star IV (USA)",
        "PATCH": patch_name,
        "OUT_NAME": "Phantasy Star IV - English Retranslation v%s" % version,   # + .bin / .smd
        "README_NOTE": " See readme.txt.",
        "HINT": " See readme.txt, section 2.",
    })

    zip_path = os.path.join(OUTDIR, stem + ".zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(os.path.join(folder, patch_name), patch_name)
        z.write(patcher, "Patcher.html")
        z.write(readme, "readme.txt")

    print("source  %s  CRC32 %s" % (tokens["SRC_SIZE"], tokens["SRC_CRC32"]))
    print("target  %s  CRC32 %s  MD checksum %s" % (tokens["OUT_SIZE"], tokens["OUT_CRC32"], tokens["MDCHK"]))
    print("patch   %d bytes (%s), verified by re-applying"
          % (len(patch), "Flips" if os.path.exists(FLIPS) else "tools/bps.py"))
    print("wrote   %s" % folder)
    print("wrote   %s" % zip_path)


if __name__ == "__main__":
    main(sys.argv[1:])
