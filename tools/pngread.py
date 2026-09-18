"""Minimal PNG reader - enough to get RGB pixels out of a screenshot.

Supports the colour types a screen capture actually produces (8-bit RGB and
RGBA, non-interlaced) and applies the five standard scanline filters.
"""
import zlib, struct


def read(path):
    """Returns (width, height, pixels) where pixels[y][x] = (r, g, b).

    Greyscale images are expanded to equal r/g/b so callers need not care.
    """
    data = open(path, 'rb').read()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('not a PNG')
    pos = 8
    idat = b''
    w = h = depth = ctype = None
    while pos < len(data):
        ln = struct.unpack('>I', data[pos:pos + 4])[0]
        tag = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        if tag == b'IHDR':
            w, h, depth, ctype = struct.unpack('>IIBB', body[:10])
            if body[12] != 0:
                raise ValueError('interlaced PNG not supported')
        elif tag == b'IDAT':
            idat += body
        elif tag == b'IEND':
            break
        pos += 12 + ln
    # 0 = greyscale, 2 = RGB, 4 = greyscale+alpha, 6 = RGBA.
    # Greyscale matters because png.write_gray emits type 0, so the font
    # sheets this toolchain exports must be readable by this reader.
    if depth != 8 or ctype not in (0, 2, 4, 6):
        raise ValueError(f'unsupported PNG depth={depth} colour type={ctype}')

    nch = {0: 1, 2: 3, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(idat)
    stride = w * nch
    out = []
    prev = bytearray(stride)
    p = 0
    for _ in range(h):
        f = raw[p]; p += 1
        line = bytearray(raw[p:p + stride]); p += stride
        if f == 1:
            for i in range(nch, stride):
                line[i] = (line[i] + line[i - nch]) & 0xFF
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif f == 3:
            for i in range(stride):
                a = line[i - nch] if i >= nch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(stride):
                a = line[i - nch] if i >= nch else 0
                b = prev[i]
                c = prev[i - nch] if i >= nch else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        if nch <= 2:                     # greyscale: fan the one value out
            out.append([(line[x * nch],) * 3 for x in range(w)])
        else:
            out.append([tuple(line[x * nch:x * nch + 3]) for x in range(w)])
        prev = line
    return w, h, out
