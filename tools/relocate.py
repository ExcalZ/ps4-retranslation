"""Stream relocation by remapping at the decompressor, not by repointing.

Every script stream must currently fit the exact compressed span it already
occupies, because nothing repoints. The obvious fix - find every pointer and
rewrite it - is unsafe here: stream addresses are not in a table. They appear
as literals in event code (`move.l #<stream>,d0 ; jsr ($05402C).l`), as inline
longwords after `jsr ($05402A).l`, and as the first field of area descriptors
reached through `$FFECF8`. A scan finds ~200 candidate sites, but a single
missed reference crashes the game and a single false positive corrupts data.
One stream ($1D9436) has no findable reference at all.

So this does not repoint anything. It intercepts the LZSS decompressor at
$041BA0 - the one place every stream address is actually *used* - and swaps the
source address through a lookup table. All 22 callers of $041BA0 funnel through
it, including graphics; anything not in the table passes straight through.

That makes relocation independent of how a reference is stored or computed.

Layout
------
Because a relocated stream frees its original span, the arena is the whole
original script region PLUS the unused blocks elsewhere in the ROM. Streams are
packed into it by first fit, largest first.
"""
import hwpatch
from hwpatch import Asm, D0, A0, A1

DECOMP = 0x041BA0          # LZSS entry: a0 = source, a1 = destination

# Placed after the half-width patch, in the same $FF filler at $0E7130-$0E7FFF.
REMAP_CODE  = 0x0E7300
REMAP_TABLE = 0x0E7360     # 26 entries x 8 bytes (old, new)
MAX_ENTRIES = 32

# Regions the relocator may write streams into.
#   - the original script region: every byte of it is script, and each stream
#     that moves out frees its own span
#   - $FF filler blocks elsewhere in the ROM
# $28A658 is deliberately absent: relocate8 reserves it for the 8x8 bank, so
# the two relocators cannot quietly overwrite each other.
ARENAS = [
    (0x1CC476, 0x1E27A8),   # original script extent
    (0x2F4FCE, 0x300000),   # 45106 bytes of $FF at the end of the 3 MB image
    (0x300000, 0x400000),   # the fourth megabyte - only in an expanded ROM
]


def assemble_remap():
    """Intercept $041BA0 and substitute a0 when it names a moved stream.

    The first six bytes of the decompressor are replaced by a jmp here, so the
    two displaced instructions are re-executed before returning to $041BA6:

        041BA0  558f        subq.l #2,a7
        041BA2  1f580001    move.b (a0)+,(1,a7)
    """
    a = Asm(REMAP_CODE)
    a.movem_push((1 << 15) | (1 << 6))       # d0 / a1
    a.lea_abs(REMAP_TABLE, A1)
    a.moveq(MAX_ENTRIES - 1, D0)
    a.label('loop')
    a.cmpa_l_ind(A1, A0)                     # cmpa.l (a1),a0
    a.beq('hit')
    a.lea_disp(8, A1, A1)
    a.dbf(D0, 'loop')
    a.bra('done')
    a.label('hit')
    a.movea_l_disp(4, A1, A0)                # a0 = new address
    a.label('done')
    a.movem_pop((1 << 0) | (1 << 9))         # d0 / a1
    a.subq_l_sp(2)                           # displaced: subq.l #2,a7
    a.move_b_postinc_disp_sp(1)              # displaced: move.b (a0)+,(1,a7)
    a.jmp_abs(DECOMP + 6)
    return a


def hook():
    """The six bytes that replace the head of $041BA0."""
    a = Asm(DECOMP)
    a.jmp_abs(REMAP_CODE)
    return a.build()


def free_space_ok(rom: bytes) -> str:
    end = REMAP_TABLE + MAX_ENTRIES * 8
    if set(rom[REMAP_CODE:end]) - {0xFF}:
        return f'REFUSING: {REMAP_CODE:06X}-{end-1:06X} is not $FF filler'
    return f'{REMAP_CODE:06X}-{end-1:06X} is $FF filler'


def layout(sizes, arenas=None):
    """Assign each stream an address. sizes maps old address -> new byte count.

    First fit, largest first. Returns {old: new} and the leftover free list.
    Raises if anything does not fit, rather than silently dropping a stream.
    """
    free = sorted(list(arenas or ARENAS))
    out = {}
    for old, n in sorted(sizes.items(), key=lambda kv: -kv[1]):
        for i, (lo, hi) in enumerate(free):
            if hi - lo >= n:
                # keep streams word-aligned; the decompressor reads words
                base = (lo + 1) & ~1
                if hi - base < n:
                    continue
                out[old] = base
                free[i] = (base + n, hi)
                break
        else:
            raise ValueError(f'stream {old:06X} ({n} bytes) does not fit; '
                             f'largest gap {max(h-l for l, h in free)}')
    return out, [(l, h) for l, h in free if h > l]


def arenas_for(rom: bytes, arenas=None):
    """ARENAS clipped to the image actually being patched.

    The fourth megabyte exists only in a ROM that expand.py has padded out to
    the full cartridge window. It must never be offered for a 3 MB image:
    writing past the end of a Python bytearray silently APPENDS rather than
    raising, so an unclipped arena would grow the ROM instead of failing, and
    the streams would land at addresses the cartridge does not answer for.
    """
    n = len(rom)
    source = ARENAS if arenas is None else arenas
    return [(lo, min(hi, n)) for lo, hi in source if min(hi, n) > lo]


def apply(rom: bytes, packed: dict, arenas=None):
    """packed maps old stream address -> new compressed bytes.

    Returns (rom, mapping, report).
    """
    sizes = {old: len(b) for old, b in packed.items()}
    active_arenas = arenas_for(rom, arenas)
    mapping, leftover = layout(sizes, active_arenas)
    out = bytearray(rom)

    # blank the whole arena inside the original script region first, so any
    # stale bytes cannot be mistaken for script later
    for lo, hi in active_arenas[:1]:
        out[lo:hi] = b'\xff' * (hi - lo)

    for old, blob in packed.items():
        new = mapping[old]
        out[new:new + len(blob)] = blob

    # remap table: 8 bytes per entry, unused slots point at 0 so they can
    # never match a real address
    tbl = bytearray()
    for old in sorted(packed):
        tbl += old.to_bytes(4, 'big') + mapping[old].to_bytes(4, 'big')
    while len(tbl) < MAX_ENTRIES * 8:
        tbl += bytes(8)
    out[REMAP_TABLE:REMAP_TABLE + len(tbl)] = tbl

    code = assemble_remap().build()
    out[REMAP_CODE:REMAP_CODE + len(code)] = code
    out[DECOMP:DECOMP + 6] = hook()

    report = {
        'moved': sum(1 for o in packed if mapping[o] != o),
        'in_place': sum(1 for o in packed if mapping[o] == o),
        'bytes': sum(sizes.values()),
        'free': sum(h - l for l, h in leftover),
        'largest_gap': max((h - l for l, h in leftover), default=0),
        'code_bytes': len(code),
    }
    return bytes(out), mapping, report
