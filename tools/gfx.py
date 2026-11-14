"""gfx.py: graphics text - TIM pixels as index arrays, English lettering, every copy of an image.

    python -X utf8 tools/gfx.py show ID [--row N] [--zoom 2] [--out PNG]   # sweep id (work/gfx/sweep/index.tsv)
    python -X utf8 tools/gfx.py show-leaf PAC/LEAF [--off HEX] ...
    python -X utf8 tools/gfx.py preview [--out work/gfx/preview]           # original | English for every edited TIM

Edits live in gfx/edits.py (one entry per image: the original TIM's sha1 prefix, clear rects, text runs); build.py
calls patched_leaves() -> {leaf path: new bytes} for every copy of every edited image (insert.py writes them).
"""
import argparse
import hashlib
import struct
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import extract  # noqa: E402
import timscan  # noqa: E402

SWEEP = ROOT / "gfx" / "tims.tsv"  # tools/timscan.py's index.tsv (every TIM and its copies), committed for the build


class Tim:
    """A 4/8 bpp TIM inside a leaf: .px[y][x] palette indices, .pal(row) RGB list, .encode() the leaf bytes."""

    def __init__(self, leaf, off=0):
        self.leaf, self.off = bytes(leaf), off
        t = timscan.parse_tim(self.leaf, off)
        assert t and t["bpp"] in (0, 1), "only 4/8 bpp TIMs"
        self.t = t
        self.bits = 4 if t["bpp"] == 0 else 8
        self.W, self.H = t["w"] * 16 // self.bits, t["h"]
        self.pix_off = t["end"] - len(t["pix"])
        p, stride = t["pix"], t["w"] * 2
        if self.bits == 4:
            self.px = [[(p[y * stride + x // 2] >> (4 * (x & 1))) & 15 for x in range(self.W)] for y in range(self.H)]
        else:
            self.px = [list(p[y * stride:(y + 1) * stride]) for y in range(self.H)]

    @property
    def sha(self):
        t = self.t
        return hashlib.sha1(t["pix"] + (t["clut"][2] if t["clut"] else b"")).hexdigest()

    def pal(self, row=0):
        cw, ch, cd = self.t["clut"]
        r = min(row, ch - 1)
        return [struct.unpack_from("<H", cd, (r * cw + i) * 2)[0] for i in range(cw)]

    def clut_rows(self):
        return self.t["clut"][1] if self.t["clut"] else 0

    def image(self, row=0, zoom=1):
        pal = [timscan.rgb(c) for c in self.pal(row)]
        im = Image.new("RGB", (self.W, self.H))
        im.putdata([pal[i] if i < len(pal) else (255, 0, 255) for r in self.px for i in r])
        return im.resize((self.W * zoom, self.H * zoom), Image.NEAREST) if zoom > 1 else im

    def encode(self):
        out = bytearray(self.leaf)
        stride = self.t["w"] * 2
        for y, r in enumerate(self.px):
            o = self.pix_off + y * stride
            if self.bits == 4:
                out[o:o + stride] = bytes(r[x] | (r[x + 1] << 4) for x in range(0, self.W, 2))
            else:
                out[o:o + stride] = bytes(r)
        return bytes(out)


def sweep_rows():
    rows = {}
    for line in SWEEP.read_text(encoding="utf-8").splitlines()[1:]:
        f = line.split("\t")
        rows[int(f[0])] = (f[1], [x.replace("\\", "/") for x in f[6].split(" ")])
    return rows


def copies(sha_prefix):
    """Every (PAC/leaf path without .bin, offset) holding the image whose sha1 starts with sha_prefix."""
    for _, (sha, files) in sweep_rows().items():
        if sha_prefix.startswith(sha) or sha.startswith(sha_prefix):
            out = []
            for f in files:
                path, off = f.split("+")
                out.append((path[:-4], int(off, 16)))
            return out
    raise KeyError(sha_prefix)


def load(path, off=0):
    return Tim(extract.leaf(path), off)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show")
    s.add_argument("id", type=int)
    s2 = sub.add_parser("show-leaf")
    s2.add_argument("path")
    s2.add_argument("--off", default="0")
    for p in (s, s2):
        p.add_argument("--row", type=int, default=None, help="CLUT row (default: all rows side by side)")
        p.add_argument("--zoom", type=int, default=2)
        p.add_argument("--crop", help="x,y,w,h in image pixels")
        p.add_argument("--out")
    pv = sub.add_parser("preview")
    pv.add_argument("--out", default=str(ROOT / "work" / "gfx" / "preview"))
    a = ap.parse_args()
    if a.cmd == "preview":
        import gfx_edit
        gfx_edit.preview(Path(a.out))
        return
    if a.cmd == "show":
        sha, files = sweep_rows()[a.id]
        path, off = files[0].split("+")
        t = load(path[:-4], int(off, 16))
        name = f"tim{a.id}"
    else:
        t = load(a.path, int(a.off, 16))
        name = a.path.replace("/", "_")
    rows = [a.row] if a.row is not None else list(range(max(1, t.clut_rows())))
    ims = []
    for r in rows:
        im = t.image(r)
        if a.crop:
            x, y, w, h = map(int, a.crop.split(","))
            im = im.crop((x, y, x + w, y + h))
        ims.append(im.resize((im.width * a.zoom, im.height * a.zoom), Image.NEAREST))
    sheet = Image.new("RGB", (sum(i.width + 4 for i in ims), ims[0].height), (255, 0, 255))
    x = 0
    for i in ims:
        sheet.paste(i, (x, 0))
        x += i.width + 4
    out = Path(a.out or ROOT / "work" / "gfx" / "show" / f"{name}.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(out, f"{t.W}x{t.H} {t.bits}bpp clut rows {t.clut_rows()} sha {t.sha[:12]}")


if __name__ == "__main__":
    main()
