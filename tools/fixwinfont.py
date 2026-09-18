"""Install the menu face's u-diaeresis in unused stock window-font code $57."""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decomp, nemcmp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, "ps4disasm", "general", "art", "nemesis", "Font.bin")
MENU = os.path.join(ROOT, "ps4disasm", "vwf", "menufont.bin")
CODE = 0x57


def main():
    packed = open(FONT, "rb").read()
    art = bytearray(decomp.decompress(packed + bytes(32), 0))
    glyph = open(MENU, "rb").read()[CODE * 8:(CODE + 1) * 8]
    at = (CODE - 1) * 32              # Font.bin code 1 begins at tile zero
    if at + 32 > len(art):
        raise SystemExit("Font.bin has no code $%02X tile" % CODE)
    for y, bits in enumerate(glyph):
        for x in range(0, 8, 2):
            hi = 0xF if bits & (0x80 >> x) else 0xE
            lo = 0xF if bits & (0x80 >> (x + 1)) else 0xE
            art[at + y * 4 + x // 2] = (hi << 4) | lo
    out = nemcmp.compress(bytes(art))
    if decomp.decompress(out + bytes(32), 0) != bytes(art):
        raise SystemExit("patched Font.bin failed its Nemesis round trip")
    open(FONT, "wb").write(out)
    print("Font.bin: code $57 is u-diaeresis (%d compressed bytes)" % len(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
