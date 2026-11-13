"""vram.py: render a PS1 VRAM dump (1024x512 16-bit, from L.dump_ppu) to PNG.

    python tools/vram.py V.vram.bin OUT.png [--mode 16|4|8] [--x 0 --y 0 --w 1024 --h 512] [--zoom 1]
                         [--clut X,Y]   (4/8 bpp: palette from VRAM at X,Y; without it greyscale by index)
4bpp: each VRAM halfword holds 4 pixels (low nibble = left), so a VRAM column x maps to pixel 4x."""
import argparse
import struct

from PIL import Image


def rgb(c):
    return ((c & 31) << 3, ((c >> 5) & 31) << 3, ((c >> 10) & 31) << 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vram")
    ap.add_argument("out")
    ap.add_argument("--mode", type=int, default=16)
    ap.add_argument("--x", type=int, default=0)
    ap.add_argument("--y", type=int, default=0)
    ap.add_argument("--w", type=int, default=1024, help="width in VRAM halfwords")
    ap.add_argument("--h", type=int, default=512)
    ap.add_argument("--zoom", type=int, default=1)
    ap.add_argument("--clut")
    a = ap.parse_args()
    v = open(a.vram, "rb").read()
    hw = lambda x, y: struct.unpack_from("<H", v, (y * 1024 + x) * 2)[0]
    per = {16: 1, 8: 2, 4: 4}[a.mode]
    img = Image.new("RGB", (a.w * per, a.h))
    pal = None
    if a.clut and a.mode != 16:
        cx, cy = map(int, a.clut.split(","))
        pal = [rgb(hw(cx + i, cy)) for i in range(1 << a.mode)]
    px = img.load()
    for y in range(a.h):
        for x in range(a.w):
            c = hw(a.x + x, a.y + y)
            if a.mode == 16:
                px[x, y] = rgb(c)
                continue
            bits = a.mode
            for k in range(per):
                i = (c >> (k * bits)) & ((1 << bits) - 1)
                g = i * 255 // ((1 << bits) - 1)
                px[x * per + k, y] = pal[i] if pal else (g, g, g)
    if a.zoom > 1:
        img = img.resize((img.width * a.zoom, img.height * a.zoom), Image.NEAREST)
    img.save(a.out)


if __name__ == "__main__":
    main()
