#!/usr/bin/env python
"""PS4 translation toolchain driver.

  ps4tool.py extract    <rom.smd|rom.bin> <script.json>
  ps4tool.py insert     <rom.smd|rom.bin> <script.json> <out.smd|out.bin>
  ps4tool.py check      <script.json>
  ps4tool.py decompress <rom.smd|rom.bin> <hex-offset> <out.bin>

  ps4tool.py dlg-extract <rom.smd|rom.bin> <dialogue.json>
  ps4tool.py dlg-insert  <rom.smd|rom.bin> <dialogue.json> <out.smd|out.bin>
  ps4tool.py dlg-check   <rom.smd|rom.bin> <dialogue.json>

  ps4tool.py font-export <rom.smd|rom.bin> <kana|kanji> <sheet.png>
  ps4tool.py font-import <rom.smd|rom.bin> <kana|kanji> <sheet.png> <out.smd>
  ps4tool.py font-sheet  <rom.smd|rom.bin> <kana|kanji> <preview.png>
  ps4tool.py font-check  <rom.smd|rom.bin>

  ps4tool.py hw-patch <rom.smd|rom.bin> <out.smd>          apply half-width support
  ps4tool.py hw-set   <rom.smd|rom.bin> <out.smd> <codes>  mark codes half-width
  ps4tool.py hw-list  <rom.smd|rom.bin>                    show half-width codes

  ps4tool.py expand   <rom.smd|rom.bin> <out.bin> [size-mb]
      pad to the full cartridge window (default 4 MB) and fix the header

  ps4tool.py en-build <rom.smd|rom.bin> <dialogue.json> <out.smd> [script.json] [--source-build]
      half-width patch + Latin font + English dialogue, relocated.
      With script.json, also relocates and rebuilds the 8x8 system-font bank.
"""
import sys, os
import smd, script_io
from table import Table


def read_rom(path):
    data = open(path, 'rb').read()
    if smd.is_smd(data):
        return smd.smd_to_bin(data), data[:smd.HEADER_SIZE], True
    return data, None, False


def write_rom(path, binrom, header, was_smd):
    # The output EXTENSION decides the container. This used to be
    # `endswith('.smd') or was_smd`, which meant an SMD input always produced
    # SMD output no matter what the file was called - so asking for a .bin
    # silently handed back an interleaved SMD that emulators wanting raw
    # binary (Exodus among them) will not load.
    ext = os.path.splitext(path)[1].lower()
    if ext == '.bin':
        open(path, 'wb').write(binrom)
    elif ext == '.smd' or (not ext and was_smd):
        open(path, 'wb').write(smd.bin_to_smd(binrom, header))
    else:
        open(path, 'wb').write(binrom)


def fix_checksum(rom: bytes) -> bytes:
    """Mega Drive checksum: sum of every word from 0x200 to end of ROM."""
    import expand
    return expand.fix_checksum(rom)


def main():
    if len(sys.argv) < 2:
        print(__doc__); return 1
    cmd = sys.argv[1]
    tbl = Table()

    if cmd == 'extract':
        rom, _, _ = read_rom(sys.argv[2])
        ents = script_io.extract(rom, tbl)
        script_io.save(ents, sys.argv[3])
        print(f'extracted {len(ents)} messages -> {sys.argv[3]}')

    elif cmd == 'insert':
        rom, hdr, was = read_rom(sys.argv[2])
        ents = script_io.load(sys.argv[3])
        new, rep = script_io.reinsert(rom, ents, tbl, strict=False)
        new = fix_checksum(new)
        write_rom(sys.argv[4], new, hdr, was)
        print(f'wrote {sys.argv[4]}')
        print(f'  translated  : {rep["written"]}')
        print(f'  left as-is  : {rep["kept"]}')
        if rep["problems"]:
            print(f'  PROBLEMS ({len(rep["problems"])}):')
            for m in rep["problems"]:
                print('    ' + m)

    elif cmd == 'check':
        ents = script_io.load(sys.argv[2])
        rows, probs = script_io.plan(ents, tbl)
        done = sum(1 for e in ents if e.get('en', '').strip())
        print(f'{done}/{len(ents)} translated')
        print(f'{"seg":>4} {"range":>16} {"msgs":>5} {"used":>6} {"cap":>6} {"free":>6}')
        for r in rows:
            print(f'{r["segment"]:>4} {r["start"]:06X}-{r["end"]:06X} '
                  f'{r["count"]:>5} {r["used"]:>6} {r["capacity"]:>6} {r["free"]:>6}')
        print(f'{len(probs)} problems')
        for m in probs:
            print('  ' + m)
    elif cmd == 'dlg-extract':
        import dialogue
        rom, _, _ = read_rom(sys.argv[2])
        dt = dialogue.DialogueTable()
        ents = dialogue.extract(rom, dt) + dialogue.extract_streams(rom, dt)
        dialogue.save(ents, sys.argv[3])
        st = dialogue.stats(ents)
        print(f'extracted {st["messages"]} messages, {st["bytes"]} bytes '
              f'-> {sys.argv[3]}')
        print(f'  kanji {st["kanji"]}, unmapped {st["unmapped"]}')

    elif cmd == 'dlg-insert':
        import dialogue
        rom, hdr, was = read_rom(sys.argv[2])
        dt = dialogue.DialogueTable()
        ents = dialogue.load(sys.argv[3])
        new, rep = dialogue.reinsert_streams(rom, ents, dt, strict=False)
        new = fix_checksum(new)
        write_rom(sys.argv[4], new, hdr, was)
        print(f'wrote {sys.argv[4]}')
        print(f'  translated : {rep["written"]}')
        print(f'  left as-is : {rep["kept"]}')
        for r in rep["streams"]:
            print(f'  {r["src"]:06X}: {r["used"]:>5}/{r["avail"]:<5} '
                  f'{"ok" if r["fits"] else "TOO BIG"}')
        if rep["problems"]:
            print(f'  PROBLEMS ({len(rep["problems"])}):')
            for m in rep["problems"]:
                print('    ' + m)

    elif cmd == 'dlg-check':
        # decode -> encode -> recompress must reproduce every stream exactly
        import dialogue, lzss, lzss_enc
        rom, _, _ = read_rom(sys.argv[2])
        dt = dialogue.DialogueTable()
        ents = dialogue.load(sys.argv[3])
        groups = {}
        for e in ents:
            if 'stream' in e:
                groups.setdefault(e['stream'], []).append(e)
        bad = 0
        for src, g in sorted(groups.items()):
            want, avail = lzss.decompress(rom, src, limit=0x20000,
                                          with_size=True)
            plain = bytearray()
            for e in sorted(g, key=lambda x: x['offset']):
                enc = dt.encode(e['jp'])
                if enc != bytes.fromhex(e['hex']):
                    print(f'  {e["id"]}: decode/encode mismatch'); bad += 1
                plain += enc if e.get('tail') else enc + bytes([0xFF])
            ok = bytes(plain) == want
            packed = lzss_enc.compress(bytes(plain))
            rt = lzss.decompress(packed, 0, limit=0x20000) == bytes(plain)
            print(f'  {src:06X}: split {"ok" if ok else "MISMATCH"}, '
                  f'recompress {"ok" if rt else "FAIL"}, '
                  f'{len(packed)}/{avail} bytes')
            bad += (not ok) + (not rt)
        print(f'{bad} problems')

    elif cmd == 'font-export':
        import font
        rom, _, _ = read_rom(sys.argv[2])
        n, w, h = font.export(rom, sys.argv[3], sys.argv[4])
        print(f'{n} glyphs -> {sys.argv[4]} ({w}x{h}, 1:1)')
        print('Edit in place. Keep the size exactly; black = pixel on.')

    elif cmd == 'font-import':
        import font
        rom, hdr, was = read_rom(sys.argv[2])
        new, changed = font.import_(rom, sys.argv[3], sys.argv[4])
        new = fix_checksum(new)
        write_rom(sys.argv[5], new, hdr, was)
        print(f'{changed} glyph(s) changed -> {sys.argv[5]}')

    elif cmd == 'font-sheet':
        import font
        rom, _, _ = read_rom(sys.argv[2])
        n, w, h = font.sheet(rom, sys.argv[3], sys.argv[4])
        print(f'{n} glyphs -> {sys.argv[4]} ({w}x{h}, reference only)')

    elif cmd == 'font-check':
        import font, os
        rom, _, _ = read_rom(sys.argv[2])
        ok = True
        for name in font.FONTS:
            n, bad = font.check(rom, name)
            print(f'  {name}: {n} glyphs, '
                  f'{"bitmap round-trip exact" if not bad else str(len(bad)) + " FAILED"}')
            ok &= not bad
        # full file-level round-trip through PNG
        tmp = os.path.join(os.path.dirname(sys.argv[2]) or '.', '_fontrt.png')
        for name in font.FONTS:
            font.export(rom, name, tmp)
            back, changed = font.import_(rom, name, tmp)
            print(f'  {name}: PNG export->import changes {changed} glyph(s) '
                  f'{"(exact)" if changed == 0 else "(MISMATCH)"}')
            ok &= (changed == 0)
        os.remove(tmp)
        print('ok' if ok else 'PROBLEMS')

    elif cmd == 'hw-patch':
        import hwpatch
        rom, hdr, was = read_rom(sys.argv[2])
        print(hwpatch.free_space_ok(rom))
        if hwpatch.free_space_ok(rom).startswith('REFUSING'):
            return 1
        new, info = hwpatch.apply(rom)
        new = fix_checksum(new)
        write_rom(sys.argv[3], new, hdr, was)
        print(f'  draw routine : {info["code_bytes"]} bytes at '
              f'{info["code_at"]:06X}')
        print(f'  width table  : 28 bytes at {info["table_at"]:06X} (all zero)')
        print(f'  call site    : {info["callsite_bytes"]} bytes at 06AE4A')
        print(f'wrote {sys.argv[3]}')
        print('The table is empty, so every glyph is still full width and the')
        print('display is unchanged. Use hw-set to opt characters in.')

    elif cmd == 'hw-set':
        # codes as hex, comma separated, ranges allowed:  B6-CF,51-5A,00
        import hwpatch
        rom, hdr, was = read_rom(sys.argv[2])
        codes = []
        for part in sys.argv[4].split(','):
            part = part.strip()
            if '-' in part:
                lo, hi = part.split('-')
                codes += list(range(int(lo, 16), int(hi, 16) + 1))
            elif part:
                codes.append(int(part, 16))
        new = hwpatch.set_widths(rom, codes)
        new = fix_checksum(new)
        write_rom(sys.argv[3], new, hdr, was)
        marked = hwpatch.read_widths(new)
        print(f'{len(codes)} code(s) marked; {len(marked)} half-width in total')
        print(f'wrote {sys.argv[3]}')

    elif cmd == 'hw-list':
        import hwpatch, dialogue
        rom, _, _ = read_rom(sys.argv[2])
        t = dialogue.DialogueTable()
        marked = hwpatch.read_widths(rom)
        if not marked:
            print('no codes marked half-width (display unchanged)')
        else:
            print(f'{len(marked)} half-width code(s):')
            for c in marked:
                print(f'  ${c:02X}  {t.dec.get(c, "?")}')

    elif cmd == 'en-build':
        import hwpatch, english, dialogue
        rom, hdr, was = read_rom(sys.argv[2])
        source_build = '--source-build' in sys.argv[5:]
        if source_build:
            # The disassembly build is a different product, not a relocated
            # JP ROM.  Its dialogue trees, VWF renderers, fonts, title text,
            # and menu strips are all assembled from source.  Every legacy
            # binary patch below uses JP absolute addresses; running any of
            # them against ps4built.bin corrupts live code or title assets.
            # tools/sourcebuild.py is the write path from JSON to those source
            # files.  Here, make the old command safe for callers that already
            # have a freshly assembled input ROM.
            new = fix_checksum(rom)
            write_rom(sys.argv[4], new, hdr, was)
            print('source build     : no legacy binary patches applied')
            print('dialogue/VWF     : already embedded by the assembler')
            print(f'wrote {sys.argv[4]}')
            return 0
        if hwpatch.free_space_ok(rom).startswith('REFUSING'):
            print(hwpatch.free_space_ok(rom)); return 1
        rom, info = hwpatch.apply(rom)
        print(f'half-width patch : {info["code_bytes"]} bytes at '
              f'{info["code_at"]:06X}')
        rom = hwpatch.set_widths(rom, english.HALF_WIDTH)
        print(f'half-width codes : {len(english.HALF_WIDTH)}')
        rom, n = english.install_font(rom)
        print(f'Latin glyphs     : {n} drawn into the single-byte font')

        dt = dialogue.DialogueTable()
        ctrl_rev = {v: k for k, v in dt.ctrl.items()}
        enc = lambda t: english.encode(t, ctrl_rev, dialogue.CTRL_OPERANDS)
        import relocate
        if relocate.free_space_ok(rom).startswith('REFUSING'):
            print(relocate.free_space_ok(rom)); return 1
        ents = dialogue.load(sys.argv[3])
        packed, rep = dialogue.pack_streams(ents, dt, en_encode=enc)
        rom, rgrep = dialogue.reinsert_regions(rom, ents, dt, en_encode=enc)
        print(f'dialogue regions : {rgrep["written"]} written in place')
        for m in rgrep.get("relocated", []):
            print('    ' + m)
        for m in rgrep.get("pointers", []):
            print('    ptr ' + m)
        for m in rgrep["problems"]:
            print('    ' + m)
        new, mapping, rrep = relocate.apply(rom, packed)
        script_args = [a for a in sys.argv[5:] if not a.startswith('--')]
        if script_args:
            # script_io is imported at module scope; re-importing it here
            # made the name local to main(), which broke `extract` and `insert`
            import relocate8, english8, vwfpatch
            # The VWF renderer cannot draw ligature or creep glyphs, so the
            # tables it draws must be encoded as plain letters. Taking the set
            # from vwfpatch keeps the encoder and the renderer from disagreeing
            # about which tables are converted - they disagreed once, and the
            # pairs rendered as nothing ("Gifeuer" -> "Giu").
            english8.VWF_SEGMENTS = vwfpatch.VWF_SEGMENTS
            new, finfo = english8.install_font(new)
            print(f'8x8 font         : {finfo["glyphs"]} glyphs, '
                  f'{finfo["bytes"]}/{finfo["span"]} bytes '
                  f'({finfo["free"]} free)')
            sents = script_io.load(script_args[0])
            new, smap, srep = relocate8.apply(new, sents, Table(),
                                              en_encode=english8.encode)
            dang = relocate8.verify(rom, new, smap)
            print(f'8x8 bank         : {srep["written"]} translated, '
                  f'{srep["refs"]} references repointed')
            print(f'  arena          : {srep["used"]} used, '
                  f'{srep["free"]} free')
            print(f'  dangling refs  : {len(dang)}')
            for m in srep["problems"]:
                print('    ' + m)
            # relocate8 rewrites pointer operands, but two inline copies of
            # the name lookup reach entry $50 by a hardcoded BYTE offset,
            # which is an immediate and so invisible to a pointer scan. It
            # must be recomputed from the English data or every item from
            # index $50 up shows a name from several entries earlier.
            import layout
            new, olds, disp = layout.fix_item_disp(new)
            print(f'  item shortcut  : '
                  + ' '.join(f'${o:X}' for o in sorted(olds))
                  + f' -> ${disp:X} at '
                  + ' '.join(f'{a:06X}' for a in layout.ITEM_DISP_SITES))
            # Hard gate. Calling the fix above is not an assurance that it
            # ran, or that it was the only stale offset. This compares the
            # built rom against the stock one and REFUSES TO WRITE on any
            # disagreement, so the failure can never be silent again.
            probs = layout.verify_lookups(rom, new)
            if probs:
                print()
                print('  LOOKUP VERIFICATION FAILED - refusing to write:')
                for m in probs:
                    print('    ' + m)
                return 1
            print(f'  lookups        : verified against stock')
            # VWF: assets into the fourth megabyte, then the call-site redirect
            # Measure the ENCODED bytes, not the source text. vwffont.cells
            # assumes every letter is a small cap; capitals are a pixel wider,
            # so it under-measures any name with one and would pass a name that
            # actually overflows its slice.
            def _cells(e):
                return vwfpatch.cells_for(english8.encode(e['en'].strip(), e))
            over = [e['en'].strip() for e in sents
                    if e.get('segment') in vwfpatch.VWF_SEGMENTS
                    and e.get('en', '').strip()
                    and _cells(e) > vwfpatch.TILES_PER_ROW]
            if over:
                print(f'  VWF PROBLEM    : {len(over)} name(s) wider than a '
                      f'{vwfpatch.TILES_PER_ROW}-tile slice: {over[:4]}')
                return 1
            widest = max(_cells(e) for e in sents
                         if e.get('segment') in vwfpatch.VWF_SEGMENTS
                         and e.get('en', '').strip())
            new = vwfpatch.wire(vwfpatch.install_all(new))
            print(f'  VWF            : {len(vwfpatch.VWF_SEGMENTS)} table(s) '
                  f'converted, widest name '
                  f'{widest}/{vwfpatch.TILES_PER_ROW} cells')
        new = fix_checksum(new)
        write_rom(sys.argv[4], new, hdr, was)
        print(f'translated       : {rep["written"]}')
        print(f'relocation       : {rrep["moved"]} moved, '
              f'{rrep["in_place"]} in place, {rrep["code_bytes"]} bytes of code')
        print(f'script           : {rrep["bytes"]} bytes compressed')
        print(f'free after       : {rrep["free"]} bytes '
              f'(largest gap {rrep["largest_gap"]})')
        if rep["problems"]:
            print(f'  PROBLEMS ({len(rep["problems"])}):')
            for m in rep["problems"]:
                print('    ' + m)
        print(f'wrote {sys.argv[4]}')

    elif cmd == 'expand':
        # ps4tool.py expand <rom> <out> [size-mb]
        import expand as ex
        rom, _, was = read_rom(sys.argv[2])
        size = int(float(sys.argv[4]) * 0x100000) if len(sys.argv) > 4             else ex.CART_WINDOW
        new = ex.expand(rom, size)
        rep = ex.verify(rom, new)
        # a stale SMD header would still claim the old block count, so force a
        # fresh one rather than carrying the input's through
        write_rom(sys.argv[3], new, None, was)
        print(f'{rep["old_size"]} -> {rep["new_size"]} bytes '
              f'(+{rep["gained"]} free at {rep["old_size"]:06X}-{rep["new_size"]:06X})')
        print(f'  ROM end   : {rep["rom_end"]:06X}')
        print(f'  checksum  : {rep["checksum"]:04X}')
        print(f'  changed   : ' + ' '.join(f'${b:03X}' for b in rep['header_bytes_changed'])
              + ' (header only)')
        if sys.argv[3].lower().endswith('.smd') and rep['new_size'] >= 0x400000:
            print('  NOTE: a 4 MB SMD needs a 16-bit block count; the canonical'
                  ' format has 8 bits. Prefer .bin for anything this size.')
        print(f'wrote {sys.argv[3]}')

    elif cmd == 'decompress':
        # ps4tool.py decompress <rom> <hex-offset> <out.bin>
        import decomp
        rom, _, _ = read_rom(sys.argv[2])
        off = int(sys.argv[3], 16)
        data = decomp.decompress(rom, off)
        open(sys.argv[4], 'wb').write(data)
        print(f'{off:06X}: {len(data)} bytes ({len(data)//32} tiles) -> {sys.argv[4]}')

    else:
        print(__doc__); return 1
    return 0

sys.exit(main())
