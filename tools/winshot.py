"""Screenshot a window by process id without focusing it.

    python tools/winshot.py <pid> out.png
"""
import ctypes, ctypes.wintypes as W, struct, sys, zlib

user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32


def windows_of_pid(pid):
    out = []
    @ctypes.WINFUNCTYPE(ctypes.c_bool, W.HWND, W.LPARAM)
    def cb(hwnd, _):
        p = W.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if p.value == pid and user32.IsWindowVisible(hwnd):
            out.append(hwnd)
        return True
    user32.EnumWindows(cb, 0)
    return out


def shot(hwnd):
    r = W.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    hdc = user32.GetDC(hwnd)
    mdc = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(mdc, bmp)
    # BitBlt from the window DC rather than PrintWindow: PrintWindow sends
    # WM_PRINT and blocks until the window's thread services it, which never
    # happens while BlastEm is stopped in its debugger stub.  Under DWM a
    # window DC reads the window's own redirection surface, so this works
    # while the window is stalled and even when it is partly covered.
    gdi32.BitBlt(mdc, 0, 0, w, h, hdc, 0, 0, 0x00CC0020)
    class BMI(ctypes.Structure):
        _fields_ = [("biSize", W.DWORD), ("biWidth", W.LONG), ("biHeight", W.LONG),
                    ("biPlanes", W.WORD), ("biBitCount", W.WORD), ("biCompression", W.DWORD),
                    ("biSizeImage", W.DWORD), ("biXPelsPerMeter", W.LONG), ("biYPelsPerMeter", W.LONG),
                    ("biClrUsed", W.DWORD), ("biClrImportant", W.DWORD)]
    bmi = BMI(ctypes.sizeof(BMI), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(bmi), 0)
    gdi32.DeleteObject(bmp); gdi32.DeleteDC(mdc); user32.ReleaseDC(hwnd, hdc)
    return w, h, buf.raw


def png(path, w, h, bgra):
    rows = b"".join(b"\x00" + bytes(c for x in range(w) for c in (bgra[(y * w + x) * 4 + 2], bgra[(y * w + x) * 4 + 1], bgra[(y * w + x) * 4])) for y in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                           + chunk(b"IDAT", zlib.compress(rows, 6)) + chunk(b"IEND", b""))


def capture(pid, path):
    hw = windows_of_pid(pid)
    if not hw:
        raise RuntimeError("no visible window for pid %d" % pid)
    w, h, raw = shot(hw[0])
    png(path, w, h, raw)
    return w, h


if __name__ == "__main__":
    print(capture(int(sys.argv[1]), sys.argv[2]))
