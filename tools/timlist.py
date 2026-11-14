"""timlist.py: list the TIMs among unpacked leaves with their VRAM image and CLUT rectangles.

    python -X utf8 tools/timlist.py work/pac/DE_ST01.PAC [--hit X,Y]   # --hit: only TIMs whose image/CLUT covers X,Y
"""
import struct
import sys
from pathlib import Path


def tim_rects(d):
    """-> (bpp mode, clut rect or None, image rect) for a TIM, else None. Rects are (x, y, w, h) in VRAM halfwords."""
    if len(d) < 20 or d[:4] != b"\x10\0\0\0":
        return None
    fl = struct.unpack_from("<I", d, 4)[0]
    o, clut = 8, None
    if fl & 8:
        cl, cx, cy, cw, ch = struct.unpack_from("<IHHHH", d, 8)
        clut, o = (cx, cy, cw, ch), 8 + cl
    if o + 12 > len(d):
        return None
    _, x, y, w, h = struct.unpack_from("<IHHHH", d, o)
    return fl & 7, clut, (x, y, w, h)


def covers(r, x, y):
    return r and r[0] <= x < r[0] + r[2] and r[1] <= y < r[1] + r[3]


if __name__ == "__main__":
    hit = tuple(map(int, sys.argv[sys.argv.index("--hit") + 1].split(","))) if "--hit" in sys.argv else None
    for p in sorted(Path(sys.argv[1]).rglob("*.bin")):
        t = tim_rects(p.read_bytes())
        if t and (not hit or covers(t[1], *hit) or covers(t[2], *hit)):
            print(f"{p.relative_to(sys.argv[1])}  bpp-mode {t[0]}  clut {t[1]}  image {t[2]}")
