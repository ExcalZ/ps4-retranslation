"""Battle window geometry and menu text-field budgets, for the JAPANESE ROM.

Addresses here are derived from `work/rom.bin` by scanning for instruction
patterns, NOT taken from `ps4disasm`. That disassembly is of the **US** build
(`SEGA GENESIS`, `GM MK-1307 -00`, checksum $5CB); this project targets the
Japanese one (`SEGA MEGA DRIVE`, `GM G-5524  -00`, checksum $7667). The two
share an engine but not an address map, and the delta is not constant - the
8x8 name renderer is `loc_27DB9C` in the disassembly and `$280564` here. Use
the disassembly to understand structure and this module to find offsets.

Two levers, both plain immediates rather than data tables:

`Battle_SetupWindow` at $2804BE takes **d1 = width, d2 = height in cells**, set
by `moveq` at each of its 31 call sites. `$2806CC` copies the built window out
and takes the same pair, so a window has TWO width immediates that must agree.

A menu text field's budget is the displacement of the `lea (d,a1),a1` that
follows the name draw. The renderer at $280564 opens with
`movem.l d2-d3/d7-a1,-(sp)` and restores `a1`, so after it returns `a1` is back
at the start of the name; the displacement alone decides how many cells the
name gets before the next column is drawn over it. Two bytes per cell.
"""

SETUP = 0x2804BE       # Battle_SetupWindow   d1 = width, d2 = height (cells)
COPYOUT = 0x2806CC     # window copy-out      same d1/d2 pair
RENDERER = 0x280564    # 8x8 name renderer, restores a1


def _calls(rom, target):
    """Offsets of every `jsr (target).l`."""
    pat = b'\x4e\xb9' + target.to_bytes(4, 'big')
    out, i = [], rom.find(pat)
    while i != -1:
        out.append(i)
        i = rom.find(pat, i + 1)
    return out


def _moveq_before(rom, call, reg_op, span=12):
    """Offset of the `moveq #n,dX` immediate byte in the `span` bytes before a
    call, or None. moveq is `0x7X nn` with the low bit of the opcode clear."""
    lo = max(0, call - span)
    found = None
    for k in range(lo, call - 1):
        if rom[k] == reg_op:
            found = k + 1          # the immediate byte
    return found


def windows(rom):
    """Every Battle_SetupWindow call site with its dimensions."""
    out = []
    for c in _calls(rom, SETUP):
        w = _moveq_before(rom, c, 0x72)     # moveq #n,d1
        h = _moveq_before(rom, c, 0x74)     # moveq #n,d2
        out.append({
            'call': c,
            'width_at': w, 'width': rom[w] if w is not None else None,
            'height_at': h, 'height': rom[h] if h is not None else None,
        })
    return out


def copyouts(rom):
    out = []
    for c in _calls(rom, COPYOUT):
        w = _moveq_before(rom, c, 0x72)
        h = _moveq_before(rom, c, 0x74)
        out.append({
            'call': c,
            'width_at': w, 'width': rom[w] if w is not None else None,
            'height_at': h, 'height': rom[h] if h is not None else None,
        })
    return out


def fields(rom, span=40):
    """`jsr (RENDERER).l` sites followed by a `lea (d,a1),a1` budget."""
    out = []
    for c in _calls(rom, RENDERER):
        w = rom[c:c + span]
        j = w.find(b'\x43\xe9')            # lea (d16,a1),a1
        if j == -1:
            continue
        at = c + j + 2
        d = int.from_bytes(rom[at:at + 2], 'big')
        out.append({'draw': c, 'lea_at': at, 'bytes': d, 'cells': d // 2})
    return out


def patch(rom: bytes, edits: dict) -> bytes:
    """edits maps offset -> int (1 byte) or (value, 2) for a word.

    Every edit states the value it expects to replace, so a wrong offset or an
    already-patched ROM fails loudly instead of corrupting something.
    """
    out = bytearray(rom)
    for off, spec in edits.items():
        want, new, size = spec
        cur = int.from_bytes(out[off:off + size], 'big')
        if cur != want:
            raise ValueError(f'{off:06X}: expected {want:#x}, found {cur:#x}')
        out[off:off + size] = new.to_bytes(size, 'big')
    return bytes(out)


# --------------------------------------------------- the technique window

# Three call sites share one (width, height) pair and must stay in agreement:
# the erase at $000E9E, the frame build at $2804BE, and the copy-out at
# $2806CC. Patching fewer than all three leaves the window half-resized.
#
# NOTE the same 12x9 dimensions are used by the SKILL window at $001A24 and
# $001ABA, which has an 8-cell name and no cost column. A blanket search for
# `moveq #12,d1 / moveq #9,d2` hits six sites across the ROM; only these three
# are the technique menu.
TECH_WIDTH_SITES = (0x0017BF, 0x0017D3, 0x00180F)
TECH_LEA = 0x00186C          # displacement word of `lea (d,a1),a1`

# interior = cursor + indent + name + TP cost column
TECH_CHROME = 2 + 1 + 1 + 3  # borders, cursor, indent, TP


def tech_width_for(name_cells: int) -> int:
    return name_cells + TECH_CHROME


def widen_technique(rom: bytes, name_cells: int,
                    from_cells: int = 5) -> bytes:
    """Give technique names `name_cells` cells instead of `from_cells`.

    The formula is checked against the stock ROM: tech_width_for(5) == 12,
    which is what the three sites actually hold, so the chrome accounting is
    not a guess.
    """
    old_w, new_w = tech_width_for(from_cells), tech_width_for(name_cells)
    if not 1 <= new_w <= 40:
        raise ValueError(f'window width {new_w} is not a sane cell count')
    edits = {off: (old_w, new_w, 1) for off in TECH_WIDTH_SITES}
    edits[TECH_LEA] = (from_cells * 2, name_cells * 2, 2)
    return patch(rom, edits)


# ------------------------------------------- the hardcoded item-name shortcut

# Two inline copies of the name lookup skip straight to game index $50 with a
# hardcoded BYTE displacement instead of counting terminators:
#
#   001F84/003CBA  lea    ($28A659).l,a0   <- rewritten by relocate8
#   001FC0/003CC0  cmpi.w #$50,d7
#   001FC6/003CC6  adda.w #$2DD,a0         <- NOT rewritten: an immediate, not
#   001FCA/003CCA  subi.w #$50,d7             a pointer, so relocate8's
#   001FCE/003CCE  subq.w #1,d7               reference scan never saw it
#
# relocate8 moves the region and rewrites every genuine pointer operand, but
# $2DD is the byte distance to entry $50 in the *Japanese* data. English names
# are longer, so the shortcut lands short and every item from index $50 up
# shows a name from several entries earlier - an item listed as GUARDNMAIL
# that behaves as MONOMATE.
#
# MUST be recomputed, never hardcoded: the value is the encoded length of the
# first 79 names, so it changes whenever any of them is edited.
#
# One deliberate deviation. In the stock ROM base+$2DD is $2AC1DD, which is
# TWO BYTES PAST the start of ordinal 79 ($2AC1DB). For any index above $50
# that is invisible - the scan's first act is to run to the next terminator,
# which absorbs the offset - so it only affects index $50 itself, whose name
# the Japanese ROM therefore renders two characters short. There is no faithful
# English analogue of "skip two bytes of a different string", so this points at
# the entry start, which is correct and incidentally fixes index $50.

ITEM_DISP_SITES = (0x001FC8, 0x003CC8)   # immediate word of `adda.w #d,a0`
ITEM_BASE_SITES = (0x001F84, 0x003CBA)   # the `lea (imm32).l,a0` before each
ITEM_SHORTCUT_ORDINAL = 79               # measured against the stock ROM
STOCK_DISP = 0x2DD


def item_base(rom: bytes) -> int:
    """The name-table base both shortcuts use, read from their `lea`."""
    bases = set()
    for off in ITEM_BASE_SITES:
        if rom[off] != 0x41 or rom[off + 1] != 0xF9:
            raise ValueError(f'{off:06X}: expected lea (imm32).l,a0')
        bases.add(int.from_bytes(rom[off + 2:off + 6], 'big'))
    if len(bases) != 1:
        raise ValueError('shortcut sites disagree on the base: '
                         + ' '.join(f'{b:06X}' for b in bases))
    return bases.pop()


def correct_item_disp(rom: bytes, base: int = None,
                      terminator: int = 0xFE) -> int:
    """Byte distance from `base` to the entry game index $50 names."""
    base = item_base(rom) if base is None else base
    a = base
    for _ in range(ITEM_SHORTCUT_ORDINAL):
        while rom[a] != terminator:
            a += 1
        a += 1
    return a - base


def fix_item_disp(rom: bytes):
    """Rewrite both shortcut displacements. Returns (rom, olds, new)."""
    new = correct_item_disp(rom)
    if not 0 <= new <= 0x7FFF:
        raise ValueError(f'displacement {new:#x} will not fit adda.w')
    out = bytearray(rom)
    olds = set()
    for off in ITEM_DISP_SITES:
        if out[off - 2] != 0xD0 or out[off - 1] != 0xFC:
            raise ValueError(f'{off:06X}: expected adda.w #imm,a0')
        olds.add(int.from_bytes(out[off:off + 2], 'big'))
        out[off:off + 2] = new.to_bytes(2, 'big')
    return bytes(out), olds, new


# ------------------------------------------------------ regression guard

# Calling fix_item_disp() from en-build makes the fix happen. It does NOT make
# it guaranteed: relocate8 can be driven directly, a future path can forget,
# and the failure is silent in the early game because indices below $50 take
# the terminator-counting path. What makes it an assurance is a check that
# compares the BUILT rom against the STOCK one and fails when they disagree.
#
# The invariant: relocate8 never moves code, so for any code offset that loads
# a name-table base, the base+displacement pair must resolve to the SAME entry
# ordinal in the built rom as it does in the stock one. That is exactly the
# property $2DD violated, and it does not care why the offset went stale.

ADDA_OPCODES = {0xD0, 0xD2, 0xD4, 0xD6, 0xD8, 0xDA, 0xDC, 0xDE}


def _ordinal(rom, base, pos, terminator=0xFE):
    """How many entry terminators lie between `base` and `pos`."""
    if pos < base:
        return -1
    return rom[base:pos].count(terminator)


def shortcut_sites(rom, lo, hi, window=128):
    """`lea (imm32).l,aN` into [lo,hi) followed by `adda.w #imm,aN`.

    Yields (lea_off, base, adda_imm_off, displacement).
    """
    out = []
    for i in range(0, len(rom) - 6, 2):
        if rom[i] != 0x41 or rom[i + 1] != 0xF9:
            continue
        base = int.from_bytes(rom[i + 2:i + 6], 'big')
        if not lo <= base < hi:
            continue
        w = rom[i + 6:i + 6 + window]
        for k in range(0, len(w) - 3, 2):
            if w[k] in ADDA_OPCODES and w[k + 1] == 0xFC:
                out.append((i, base, i + 6 + k + 2,
                            int.from_bytes(w[k + 2:k + 4], 'big')))
                break
    return out


def verify_lookups(stock: bytes, built: bytes,
                   arena=(0x28A658, 0x290000), terminator=0xFE):
    """Every relocated name shortcut must resolve to its stock entry ordinal.

    Returns a list of human-readable problems; empty means clean.
    """
    problems = []
    sites = shortcut_sites(built, *arena)
    if not sites:
        problems.append('no relocated name shortcuts found - either nothing '
                        'was relocated, or the arena bounds are wrong')
    for lea_off, base_b, imm_off, disp_b in sites:
        if stock[lea_off] != 0x41 or stock[lea_off + 1] != 0xF9:
            problems.append(f'{lea_off:06X}: stock rom has no lea here; the '
                            f'code offsets no longer line up')
            continue
        base_s = int.from_bytes(stock[lea_off + 2:lea_off + 6], 'big')
        disp_s = int.from_bytes(stock[imm_off:imm_off + 2], 'big')
        ord_s = _ordinal(stock, base_s, base_s + disp_s, terminator)
        ord_b = _ordinal(built, base_b, base_b + disp_b, terminator)
        if ord_s != ord_b:
            problems.append(
                f'{lea_off:06X}: shortcut resolves to entry {ord_b}, stock '
                f'resolves to {ord_s} (base ${base_b:06X} disp ${disp_b:X}; '
                f'stock base ${base_s:06X} disp ${disp_s:X}) - '
                f'names will be {ord_s - ord_b} entries out')
    return problems
