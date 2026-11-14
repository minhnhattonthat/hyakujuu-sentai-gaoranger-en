"""Find 12-byte sprite records (s16 x, s16 y, u8 u, v, w, h, u16 tpage, u16 clut; docs/re/graphics.md §Redraw status)
that show a given texture-page area, in every leaf of the named PACs (work/pac/<PAC>/*.bin).

    python -X utf8 tools/sprfind.py --tpage-x 14 --u 100-115 --v 60-75 A_EX01.PAC A_ST11.PAC ..

tpage & 0x1f must equal tpage-x + 16 * (VRAM y >= 256, --tpage-y 1 default). Records are scanned at every 2-byte
offset, so expect some noise: check w/h look like a label.
"""
import argparse
import glob
import os
import struct

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rng(s):
    a, _, b = s.partition("-")
    return int(a, 0), int(b or a, 0)


def scan(data, page, u, v, minw):
    for o in range(0, len(data) - 11, 2):
        x, y, uu, vv, w, h, tp, clut = struct.unpack_from("<hhBBBBHH", data, o)
        if tp & 0x1f == page and u[0] <= uu <= u[1] and v[0] <= vv <= v[1] and w >= minw and 0 < h <= 64:
            yield o, (x, y, uu, vv, w, h, tp, clut)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pacs", nargs="+")
    ap.add_argument("--tpage-x", type=int, required=True)
    ap.add_argument("--tpage-y", type=int, default=1)
    ap.add_argument("--u", type=rng, default=(0, 255))
    ap.add_argument("--v", type=rng, default=(0, 255))
    ap.add_argument("--min-w", type=int, default=8)
    a = ap.parse_args()
    page = a.tpage_x + 16 * a.tpage_y
    for pac in a.pacs:
        for f in sorted(glob.glob(os.path.join(ROOT, "work", "pac", pac, "*.bin"))):
            for o, r in scan(open(f, "rb").read(), page, a.u, a.v, a.min_w):
                print(f"{pac}/{os.path.basename(f)}+{o:#x}  x {r[0]} y {r[1]} u {r[2]} v {r[3]} w {r[4]} h {r[5]} "
                      f"tpage {r[6]:#06x} clut {r[7]:#06x}")


if __name__ == "__main__":
    main()
