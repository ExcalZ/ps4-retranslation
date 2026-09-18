"""Render the VDP planes of a BlastEm native savestate to a PNG.

BlastEm's `BLSTSZ` savestate has no section table we parse, but the VDP
section is laid out by vdp_serialize() as

    int8   VRAM size in KB (64)
    bytes  VRAM
    int16  CRAM x64        (big-endian)
    int16  VSRAM x40
    bytes  SAT cache (320: 4 bytes x 80 sprites)
    int8   registers x24

so once the VRAM is found the rest follows.  VRAM is located by content: the
game builds its Plane A nametable in work RAM (Plane_A_Buffer, $FFFF8000)
and DMAs it to $C000, so a distinctive row of that buffer appears twice in
the file - once in RAM (tools/blastem_ram.py finds that) and once in VRAM.

Usage:
    python tools/blastem_screen.py state.state [out.png] [--no-sprites]

Draws Plane B, Plane A, then sprites, honouring per-plane scroll, priority
and the window plane.  Good enough to read what a screen shows; it is not a
cycle-accurate VDP (no shadow/highlight, no mid-frame raster effects).
"""
import os, struct, sys, zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastem_ram

PLANE_A_BUF = 0x8000        # Plane_A_Buffer - $FF0000
PLANE_A_NT = 0xC000         # Command $8230 in the VDP register table


def locate_vdp(data):
    ram_base = blastem_ram.find_base(data)
    if ram_base is None:
        raise ValueError("work RAM not found")
    ram = data[ram_base:ram_base + 0x10000]
    pa = ram[PLANE_A_BUF:PLANE_A_BUF + 0xE00]
    for row in range(28):
        win = pa[row * 0x80:row * 0x80 + 0x50]
        if len(set(win)) < 6:
            continue
        i = data.find(win)
        hits = []
        while i >= 0:
            hits.append(i)
            i = data.find(win, i + 1)
        hits = [h for h in hits if h != ram_base + PLANE_A_BUF + row * 0x80]
        if len(hits) == 1:
            vram = hits[0] - row * 0x80 - PLANE_A_NT
            if 0 <= vram and vram + 0x10000 <= len(data) and data[vram - 1] == 64:
                return ram, vram
    raise ValueError("VRAM not found")


def read_state(path):
    data = open(path, "rb").read()
    ram, v = locate_vdp(data)
    vram = data[v:v + 0x10000]
    cram = struct.unpack(">64H", data[v + 0x10000:v + 0x10080])
    vsram = struct.unpack(">40H", data[v + 0x10080:v + 0x100D0])
    regs = data[v + 0x100D0 + 0x140:v + 0x100D0 + 0x140 + 24]
    return {"ram": ram, "vram": vram, "cram": cram, "vsram": vsram, "regs": regs}


def color(c):
    return ((c & 0xE) * 17, ((c >> 4) & 0xE) * 17, ((c >> 8) & 0xE) * 17)


def tile_pixel(vram, tile, x, y):
    off = (tile << 5) + y * 4 + (x >> 1)
    b = vram[off & 0xFFFF]
    return (b >> 4) if (x & 1) == 0 else (b & 0xF)


def render(st, sprites=True):
    vram, cram, vsram, regs = st["vram"], st["cram"], st["vsram"], st["regs"]
    h40 = bool(regs[12] & 0x81)
    W = 320 if h40 else 256
    H = 224
    ntA = (regs[2] & 0x38) << 10
    ntB = (regs[4] & 0x07) << 13
    ntW = (regs[3] & (0x3E if not h40 else 0x3C)) << 10
    sat = (regs[5] & (0x7F if not h40 else 0x7E)) << 9
    hscroll_tab = (regs[13] & 0x3F) << 10
    size = regs[16]
    pw = (32, 64, 32, 128)[size & 3]
    ph = (32, 64, 32, 128)[(size >> 4) & 3]
    hmode = regs[11] & 3
    vmode = regs[11] & 4
    bg = color(cram[regs[7] & 0x3F])

    win_right = regs[17] & 0x80
    win_x = (regs[17] & 0x1F) * 16
    win_down = regs[18] & 0x80
    win_y = (regs[18] & 0x1F) * 8

    pix = [[bg] * W for _ in range(H)]
    prio = [[0] * W for _ in range(H)]     # 0 bg, 1 low, 2 high

    def hscroll(plane, y):
        if hmode == 0:
            off = 0
        elif hmode == 2:
            off = (y & ~7) * 4
        elif hmode == 3:
            off = y * 4
        else:
            off = (y & 7) * 4 if hmode == 1 else 0
        o = hscroll_tab + off + (0 if plane == 0 else 2)
        return (vram[o] << 8 | vram[o + 1]) & 0x3FF

    def vscroll(plane, x):
        if vmode:
            idx = (x >> 4) * 2 + plane
        else:
            idx = plane
        return vsram[idx] & 0x3FF

    def draw_plane(nt, plane, window=False):
        for y in range(H):
            for x in range(W):
                if window:
                    in_win = False
                    if regs[17] & 0x1F or win_right:
                        in_win |= (x >= win_x) if win_right else (x < win_x)
                    if regs[18] & 0x1F or win_down:
                        in_win |= (y >= win_y) if win_down else (y < win_y)
                    if not in_win:
                        continue
                    ex, ey = x, y
                    cols = 64 if h40 else 32
                    entry = nt + ((ey >> 3) * cols + (ex >> 3)) * 2
                else:
                    if plane == 0 and (regs[17] & 0x1F or regs[18] & 0x1F) and \
                            in_window(x, y):
                        continue
                    ex = (x - hscroll(plane, y)) & (pw * 8 - 1)
                    ey = (y + vscroll(plane, x)) & (ph * 8 - 1)
                    entry = nt + ((ey >> 3) * pw + (ex >> 3)) * 2
                e = vram[entry & 0xFFFF] << 8 | vram[(entry + 1) & 0xFFFF]
                tile = e & 0x7FF
                tx, ty = ex & 7, ey & 7
                if e & 0x800: tx = 7 - tx
                if e & 0x1000: ty = 7 - ty
                c = tile_pixel(vram, tile, tx, ty)
                if c == 0:
                    continue
                p = 2 if e & 0x8000 else 1
                if p >= prio[y][x]:
                    pix[y][x] = color(cram[((e >> 13) & 3) * 16 + c])
                    prio[y][x] = p

    def in_window(x, y):
        if (regs[17] & 0x1F or win_right) and ((x >= win_x) if win_right else (x < win_x)):
            return True
        if (regs[18] & 0x1F or win_down) and ((y >= win_y) if win_down else (y < win_y)):
            return True
        return False

    draw_plane(ntB, 1)
    draw_plane(ntA, 0)
    if regs[17] & 0x9F or regs[18] & 0x9F:
        draw_plane(ntW, 0, window=True)

    if sprites:
        # walk the sprite link list, draw in reverse so earlier sprites win
        order = []
        idx = 0
        seen = set()
        while idx not in seen and len(order) < 80:
            seen.add(idx)
            order.append(idx)
            idx = vram[sat + idx * 8 + 3] & 0x7F
            if idx == 0:
                break
        for idx in reversed(order):
            s = sat + idx * 8
            sy = ((vram[s] << 8 | vram[s + 1]) & 0x3FF) - 128
            hs = ((vram[s + 2] >> 2) & 3) + 1
            vs = (vram[s + 2] & 3) + 1
            attr = vram[s + 4] << 8 | vram[s + 5]
            sx = ((vram[s + 6] << 8 | vram[s + 7]) & 0x1FF) - 128
            tile = attr & 0x7FF
            pal = ((attr >> 13) & 3) * 16
            p = 3 if attr & 0x8000 else 1
            for cx in range(hs):
                for cy in range(vs):
                    tcx = hs - 1 - cx if attr & 0x800 else cx
                    tcy = vs - 1 - cy if attr & 0x1000 else cy
                    t = tile + tcx * vs + tcy
                    for yy in range(8):
                        y = sy + cy * 8 + yy
                        if not 0 <= y < H:
                            continue
                        for xx in range(8):
                            x = sx + cx * 8 + xx
                            if not 0 <= x < W:
                                continue
                            tx = 7 - xx if attr & 0x800 else xx
                            ty = 7 - yy if attr & 0x1000 else yy
                            c = tile_pixel(vram, t, tx, ty)
                            if c == 0:
                                continue
                            # sprite priority: high beats everything, low
                            # beats low-priority plane pixels only
                            if p == 3 or prio[y][x] < 2:
                                pix[y][x] = color(cram[pal + c])
    return pix, W, H


def write_png(path, pix, W, H, scale=2):
    raw = bytearray()
    for y in range(H):
        row = bytearray()
        for x in range(W):
            row += bytes(pix[y][x]) * scale
        for _ in range(scale):
            raw += b"\x00" + row

    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W * scale, H * scale, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    open(path, "wb").write(png)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    st = read_state(args[0])
    out = args[1] if len(args) > 1 else os.path.splitext(args[0])[0] + ".png"
    pix, W, H = render(st, sprites="--no-sprites" not in sys.argv)
    write_png(out, pix, W, H)
    r = st["regs"]
    print("wrote %s  (%dx%d)  ntA $%04X ntB $%04X win $%04X sat $%04X hs $%04X r11 $%02X r16 $%02X r17 $%02X r18 $%02X"
          % (out, W, H, (r[2] & 0x38) << 10, (r[4] & 7) << 13, (r[3] & 0x3E) << 10,
             (r[5] & 0x7F) << 9, (r[13] & 0x3F) << 10, r[11], r[16], r[17], r[18]))
