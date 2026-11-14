"""sprgroups.py: list sprite groups of a story/ending PAC's 12_17-style leaf (credits layouts, docs/re/graphics.md).

    python -X utf8 tools/sprgroups.py PAC/LEAF [--tpage-x 9,10,11,12]

Leaf: u32 offset table (0 = no group) up to the first group; a group = u16 count, then count x 12-byte sprites
(s16 x, s16 y screen offset, u8 u, v, w, h, u16 tpage, u16 clut). Prints one line per sprite.
"""
import argparse
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract  # noqa: E402


def groups(b):
    offs = []
    i = 0x3c  # 0x00-0x3b: header (DE_ST07 12_17), then the offset table up to the first group
    while not offs or i < min(offs):
        o = struct.unpack_from("<I", b, i)[0]
        if 0 < o < len(b) - 2:  # other values in the table aren't groups
            offs.append(o)
        i += 4
    for g, o in enumerate(offs):
        n = struct.unpack_from("<H", b, o)[0]
        yield g, o, [struct.unpack_from("<hhBBBBHH", b, o + 2 + 12 * k) for k in range(n)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("leaf")
    ap.add_argument("--tpage-x", help="only sprites whose texture page x (0-15) is in this list")
    a = ap.parse_args()
    want = a.tpage_x and {int(v) for v in a.tpage_x.split(",")}
    for g, o, sprs in groups(extract.leaf(a.leaf)):
        for x, y, u, v, w, h, tp, clut in sprs:
            if want and (tp & 15) not in want:
                continue
            print(f"g{g:02d} @{o:04x} x{x:5d} y{y:5d} u{u:3d} v{v:3d} w{w:3d} h{h:3d} tpx {tp & 15} tpy {tp >> 4 & 1}"
                  f" clut {clut:04x}")


if __name__ == "__main__":
    main()
