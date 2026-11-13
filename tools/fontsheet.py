"""fontsheet.py: render the dialogue font (4bpp TIM, 12x12 cells, 21 per row) as a labelled cell sheet.

    python -X utf8 tools/fontsheet.py FONT_TIM.bin OUT.png [--y0 80] [--zoom 4]
Each cell is labelled with its code (0xA0 + row*0x20 + col) and the tbl/jp.tbl character, to check the table."""
import argparse
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import make_tbl  # noqa: E402


def load_tim4(d):
    """4bpp TIM with CLUT -> (width px, height, index rows)."""
    assert struct.unpack_from("<I", d, 0)[0] == 0x10
    clen = struct.unpack_from("<I", d, 8)[0]
    o = 8 + clen
    _, x, y, w, h = struct.unpack_from("<IHHHH", d, o)
    pix = d[o + 12:o + 12 + w * 2 * h]
    rows = [[(pix[r * w * 2 + i // 2] >> (4 * (i & 1))) & 15 for i in range(w * 4)] for r in range(h)]
    return w * 4, h, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tim")
    ap.add_argument("out")
    ap.add_argument("--y0", type=int, default=80)
    ap.add_argument("--x0", type=int, default=0)
    ap.add_argument("--zoom", type=int, default=4)
    a = ap.parse_args()
    w, h, rows = load_tim4(open(a.tim, "rb").read())
    chars = dict(make_tbl.entries())
    z, cw, ch = a.zoom, 12, 16  # cell 12 wide, rows 16 apart: u = (code & 31) * 12, v = (code >> 5) * 16
    lab = 14
    img = Image.new("RGB", (21 * (cw * z + 4), 11 * (ch * z + lab + 4)), (40, 40, 40))
    dr = ImageDraw.Draw(img)
    for r in range(11):
        for c in range(21):
            ox, oy = c * (cw * z + 4), r * (ch * z + lab + 4)
            code = 0xA0 + r * 0x20 + c
            dr.text((ox, oy), f"{code:03X} {chars.get(code, '')}", fill=(255, 200, 0))
            for yy in range(ch):
                for xx in range(cw):
                    py, px = a.y0 + r * ch + yy, a.x0 + c * cw + xx
                    v = rows[py][px] if py < h and px < w else 0
                    g = v * 17
                    dr.rectangle([ox + xx * z, oy + lab + yy * z, ox + xx * z + z - 1, oy + lab + yy * z + z - 1],
                                 fill=(g, g, g))
    img.save(a.out)
    print(a.out, "(table chars for reference:", "".join(chars.get(0xA0 + r * 0x20 + c, "_") for r in (8, 9) for c in range(21)), ")")


if __name__ == "__main__":
    main()
