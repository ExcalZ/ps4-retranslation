"""Relocation for the 8x8 system-font bank (item names, descriptions).

This bank is uncompressed and bounded by anchors - addresses that appear as
operands of real instructions in code. Messages inside a segment are found by
counting $FE terminators from its anchor ($05CCB6), so message sizes may change
freely, but the segment total is capped by the next anchor.

Unlike the LZSS streams, there is no single choke point to intercept: text is
reached by `lea (anchor).l,a0` followed either by the terminator scan or by
direct indexing. So this does rewrite pointers - which is only safe because
every reference is a genuine instruction operand and can be enumerated exactly.

regions.references() requires the preceding word to be an opcode that takes a
32-bit absolute operand. Two weaker tests were tried first and both produced
phantom anchors; see regions.py. After rewriting, verify() re-scans for any
surviving reference into the old range, so a missed one is reported rather
than shipped.
"""
import regions

# Reserved for this bank alone. The LZSS streams use the original script region
# plus $2F4FCE; keeping the two apart means neither can quietly overwrite the
# other.
ARENA = (0x28A658, 0x290000)      # 22952 bytes of $FF filler


def apply(rom, entries, tbl, en_encode=None):
    """Rebuild both regions at new addresses and repoint every reference."""
    from collections import defaultdict
    out = bytearray(rom)
    by_seg = defaultdict(list)
    for e in entries:
        by_seg[(e['region'], e['seg_start'])].append(e)

    built = {i: (lo, hi, term, anchors)
             for i, lo, hi, term, anchors in regions.build(rom)}
    cursor = ARENA[0]
    mapping, report = {}, {'written': 0, 'kept': 0, 'problems': [], 'refs': 0}

    for ri in sorted(built):
        lo, hi, term, anchors = built[ri]
        base = cursor
        blob = bytearray()
        pts = sorted(anchors) + [hi]
        for k in range(len(pts) - 1):
            s, e = pts[k], pts[k + 1]
            mapping[s] = base + len(blob)
            ents = sorted(by_seg.get((ri, s), []), key=lambda x: x['offset'])
            if not ents:
                blob += rom[s:e]
                continue
            for en in ents:
                text = en.get('en', '').strip()
                enc = None
                if text:
                    try:
                        # en_encode takes the entry as well as the text: the 8x8
                        # bank picks its packing per table (party / technique /
                        # plain), which cannot be read off the string alone.
                        enc = (en_encode(text, en) if en_encode
                               else tbl.encode(text))
                    except (KeyError, ValueError) as ex:
                        report['problems'].append(f'{en["id"]}: {ex}')
                if enc is None:
                    enc = bytes.fromhex(en['hex']); report['kept'] += 1
                else:
                    report['written'] += 1
                blob += enc + bytes([term])
        out[base:base + len(blob)] = blob
        cursor = base + len(blob)
        if cursor > ARENA[1]:
            raise ValueError(f'region {ri}: {cursor - ARENA[0]} bytes needed, '
                             f'{ARENA[1] - ARENA[0]} available')

    # repoint. The region start is synthetic (regions.build seeds it with lo)
    # and has no references of its own, so rewriting it is a no-op.
    for old, new in mapping.items():
        for site in regions.references(bytes(rom), old):
            out[site:site + 4] = new.to_bytes(4, 'big')
            report['refs'] += 1
    report['used'] = cursor - ARENA[0]
    report['free'] = ARENA[1] - cursor
    return bytes(out), mapping, report


def verify(rom_before, rom_after, mapping):
    """No reference into an old region may survive the rewrite."""
    dangling = []
    for old in mapping:
        left = regions.references(rom_after, old)
        if left:
            dangling.append((old, left))
    return dangling
