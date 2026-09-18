"""ROM expansion to the full Mega Drive cartridge window.

The Japanese ROM is 3 MB ($300000). The Mega Drive maps cartridge ROM at
$000000-$3FFFFF, so a fourth megabyte is addressable with no mapper, no bank
switching, and no change to how anything is pointed at - `lea $3xxxxx.l,a0`
already works today. The 4 MB ceiling is the cartridge address decode, not the
68000, which has a 24-bit bus and could reach 16 MB.

Past 4 MB needs the SSF2 mapper at $A130F3-$A130FF. This game is a poor
candidate for it: it already drives $A130F1 to overlay SRAM at $200001-$203FFF,
so mapper state would be entangled with save handling, and bank state is global
while the game fires DMA from ROM in vblank.

What this changes, and nothing else:

    pad          old end .. new end, filled with $FF
    $1A4-$1A7    header ROM-end longword
    $18E-$18F    header checksum

The game reads neither field - there is no boot-time checksum test anywhere in
the disassembly - so both are hygiene. A wrong ROM-end mainly confuses external
tools; a wrong checksum confuses ROM databases.

Hazard worth recording: SRAM is overlaid over $200001-$203FFF whenever
$A130F1 bit 0 is set, so reads there do not reach ROM while a save is in
progress. Data placed above $300000 is clear of that window, which is a second
reason to expand rather than keep scavenging the ~95 KB of filler left below.
"""

CART_WINDOW = 0x400000     # $000000-$3FFFFF, the whole plain-cartridge window
ROM_END_FIELD = 0x1A4      # header longword: address of the last ROM byte
CHECKSUM_FIELD = 0x18E
FILL = 0xFF                # matches the assembler's own tail padding


def checksum(rom: bytes) -> int:
    """Mega Drive checksum: sum of every word from $200 to the end of ROM."""
    s = 0
    for i in range(0x200, len(rom) - 1, 2):
        s = (s + ((rom[i] << 8) | rom[i + 1])) & 0xFFFF
    return s


def fix_checksum(rom: bytes) -> bytes:
    out = bytearray(rom)
    s = checksum(out)
    out[CHECKSUM_FIELD] = s >> 8
    out[CHECKSUM_FIELD + 1] = s & 0xFF
    return bytes(out)


def rom_end(rom: bytes) -> int:
    return int.from_bytes(rom[ROM_END_FIELD:ROM_END_FIELD + 4], 'big')


def expand(rom: bytes, size: int = CART_WINDOW, fill: int = FILL) -> bytes:
    """Pad `rom` to `size`, updating the ROM-end field and the checksum.

    Idempotent: a ROM already at `size` is returned with its header fields
    corrected but no other change.
    """
    if rom[0x100:0x104] != b'SEGA':
        raise ValueError('not a Mega Drive image: no "SEGA" at $100')
    if size > CART_WINDOW:
        raise ValueError(
            f'{size:#08x} is past the plain-cartridge window; anything above '
            f'{CART_WINDOW:#08x} needs the SSF2 mapper, which this ROM cannot '
            f'take cheaply - see the module docstring')
    if size % 0x4000:
        raise ValueError('size must be a whole number of 16 KiB blocks')
    if len(rom) > size:
        raise ValueError(f'refusing to shrink {len(rom):#08x} -> {size:#08x}')

    out = bytearray(rom)
    out += bytes([fill]) * (size - len(rom))
    out[ROM_END_FIELD:ROM_END_FIELD + 4] = (size - 1).to_bytes(4, 'big')
    return fix_checksum(out)


def verify(old: bytes, new: bytes, fill: int = FILL) -> dict:
    """Prove the expansion touched only the pad and the two header fields.

    Returns a report; raises on anything it cannot account for.
    """
    if len(new) < len(old):
        raise ValueError('expanded image is smaller than the original')

    header_fields = set(range(ROM_END_FIELD, ROM_END_FIELD + 4)) | \
                    {CHECKSUM_FIELD, CHECKSUM_FIELD + 1}
    unexpected = [i for i in range(len(old))
                  if old[i] != new[i] and i not in header_fields]
    if unexpected:
        raise ValueError(f'{len(unexpected)} byte(s) changed outside the '
                         f'header, first at {unexpected[0]:06X}')

    pad = new[len(old):]
    if any(b != fill for b in pad):
        bad = next(i for i, b in enumerate(pad) if b != fill)
        raise ValueError(f'pad is not uniform, first at {len(old) + bad:06X}')

    stored = int.from_bytes(new[CHECKSUM_FIELD:CHECKSUM_FIELD + 2], 'big')
    actual = checksum(new)
    if stored != actual:
        raise ValueError(f'checksum {stored:04X} does not match {actual:04X}')

    return {
        'old_size': len(old),
        'new_size': len(new),
        'gained': len(pad),
        'rom_end': rom_end(new),
        'checksum': stored,
        'header_bytes_changed': sorted(i for i in header_fields
                                       if old[i] != new[i]),
    }
