"""timscan.py: find every TIM image in the unpacked PACs (work/pac/**), dedupe by pixel hash, render contact sheets.

    python -X utf8 tools/timscan.py [--out work/gfx/sweep] [--per 20]
Writes OUT/index.tsv (id, sha1, bpp, w, h, files with offsets) and OUT/sheet_NNN.png (labelled thumbnails, first
CLUT row). TIMs are found anywhere inside a leaf (magic 10 00 00 00, flags bpp 0-3 +CLUT bit, sizes that fit);
the sweep prints what it skipped."""
import argparse
import glob
import hashlib
import os
import struct

from PIL import Image, ImageDraw


def parse_tim(d, o):
    """Returns dict or None. Flags may carry bit 31 (this game sets it)."""
    if d[o:o + 4] != b"\x10\0\0\0" or o + 8 > len(d):
        return None
    fl = struct.unpack_from("<I", d, o + 4)[0] & 0x7FFFFFFF
    bpp, has_clut = fl & 7, fl & 8
    if bpp > 3 or fl & ~0xF:
        return None
    p = o + 8
    clut = None
    if has_clut:
        if p + 12 > len(d):
            return None
        cl, cx, cy, cw, ch = struct.unpack_from("<IHHHH", d, p)
        if cl != 12 + cw * ch * 2 or not (0 < cw <= 1024 and 0 < ch <= 512) or p + cl > len(d):
            return None
        clut = (cw, ch, d[p + 12:p + cl])
        p += cl
    if p + 12 > len(d):
        return None
    il, ix, iy, iw, ih = struct.unpack_from("<IHHHH", d, p)
    if il != 12 + iw * ih * 2 or not (0 < iw <= 1024 and 0 < ih <= 512) or p + il > len(d):
        return None
    return dict(bpp=bpp, clut=clut, w=iw, h=ih, x=ix, y=iy, pix=d[p + 12:p + il], end=p + il)


def rgb(c):
    return ((c & 31) << 3, ((c >> 5) & 31) << 3, ((c >> 10) & 31) << 3)


def render(t, row=0):
    bpp, iw, ih, pix = t["bpp"], t["w"], t["h"], t["pix"]
    per = {0: 4, 1: 2, 2: 1, 3: 1}[bpp]
    W = iw * per if bpp < 3 else iw * 2 // 3
    img = Image.new("RGB", (W, ih))
    px = img.load()
    pal = None
    if t["clut"]:
        cw, ch, cd = t["clut"]
        r = min(row, ch - 1)
        pal = [rgb(struct.unpack_from("<H", cd, (r * cw + i) * 2)[0]) for i in range(cw)]
    for y in range(ih):
        line = pix[y * iw * 2:(y + 1) * iw * 2]
        if bpp == 2:
            for x in range(iw):
                px[x, y] = rgb(struct.unpack_from("<H", line, x * 2)[0])
        elif bpp == 3:
            for x in range(W):
                px[x, y] = tuple(line[x * 3:x * 3 + 3])
        else:
            bits = 4 if bpp == 0 else 8
            for x in range(W):
                i = (line[x * bits // 8] >> ((x * bits) % 8)) & ((1 << bits) - 1)
                px[x, y] = pal[i] if pal and i < len(pal) else (i * (255 >> bits << bits >> 4) % 256,) * 3
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="work/gfx/sweep")
    ap.add_argument("--per", type=int, default=20)
    ap.add_argument("--thumb", type=int, default=200)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    seen = {}
    order = []
    for f in sorted(glob.glob("work/pac/**/*.bin", recursive=True)):
        d = open(f, "rb").read()
        o = 0
        while True:
            o = d.find(b"\x10\0\0\0", o)
            if o < 0:
                break
            t = parse_tim(d, o)
            if not t:
                o += 4
                continue
            h = hashlib.sha1(t["pix"] + (t["clut"][2] if t["clut"] else b"")).hexdigest()
            if h not in seen:
                seen[h] = (t, [])
                order.append(h)
            seen[h][1].append(f"{os.path.relpath(f, 'work/pac')}+{o:x}")
            o = t["end"]
    with open(os.path.join(a.out, "index.tsv"), "w", encoding="utf-8") as idx:
        idx.write("id\tsha1\tbpp\tw\th\tvram\tfiles\n")
        for i, h in enumerate(order):
            t, fs = seen[h]
            idx.write(f"{i}\t{h[:12]}\t{t['bpp']}\t{t['w']}\t{t['h']}\t{t['x']},{t['y']}\t{' '.join(fs)}\n")
    T = a.thumb
    for s in range(0, len(order), a.per):
        cols = 5
        sheet = Image.new("RGB", (cols * (T + 6), ((a.per + cols - 1) // cols) * (T + 20)), (60, 0, 60))
        dr = ImageDraw.Draw(sheet)
        for k, h in enumerate(order[s:s + a.per]):
            t, fs = seen[h]
            im = render(t)
            im.thumbnail((T, T))
            x, y = (k % cols) * (T + 6), (k // cols) * (T + 20)
            sheet.paste(im, (x, y + 14))
            dr.text((x, y), f"#{s + k} {fs[0][:26]}", fill=(255, 255, 0))
        sheet.save(os.path.join(a.out, f"sheet_{s // a.per:03d}.png"))
    print(len(order), "unique TIMs,", sum(len(v[1]) for v in seen.values()), "occurrences ->", a.out)


if __name__ == "__main__":
    main()
