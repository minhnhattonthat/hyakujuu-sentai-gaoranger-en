"""credits.py: English staff roll (DE_ST07): new text atlases + rewritten 12_17 sprite groups (docs/re/graphics.md
§Credits layout). The English lines live in gfx/credits.py.

    python -X utf8 tools/credits.py render [--jp] [--out work/gfx/credits]   # every text group as on screen

The roll draws each group's sprites (12_17, tools/sprgroups.py) from four 256x256 4bpp atlases (TIMs 148, 149,
150, 142 = DE_ST07 9_7..9_10, texture pages x 9-12, y 1). Japanese lines are built from shared fragments, so the
English is laid out from scratch: every line becomes one strip packed into the atlases, and each group's sprites
are rewritten to point at its strips (the group keeps its sprite count; spare sprites get w = h = 0).
"""
import argparse
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "gfx"))
import extract  # noqa: E402
import gfx  # noqa: E402
import gfx_edit  # noqa: E402
import sprgroups  # noqa: E402

PAC = "DE_ST07.PAC"
LAYOUT = f"{PAC}/12_17"
ATLAS = {9: f"{PAC}/9_7", 10: f"{PAC}/9_8", 11: f"{PAC}/9_9", 12: f"{PAC}/9_10"}  # texture page x -> leaf (y 1)
SPR = struct.Struct("<hhBBBBHH")


def is_text(tp):
    return tp >> 4 & 1 and (tp & 15) in ATLAS


def palettes(tims):
    """{(clut x, clut y): RGB list}: 9_7 loads its CLUT at (128, 496), the others at (0, 496) (all the same)."""
    out = {}
    for tpx, t in tims.items():
        cx = 128 if tpx == 9 else 0
        for r in range(t.clut_rows()):
            out[(cx, 496 + r)] = [gfx.timscan.rgb(c) for c in t.pal(r)]
    return out


def render(layout, tims, out_dir, tag):
    """One sheet per 24 groups: each text group drawn at its screen offsets (centre 160, 120 of a 320x240 view)."""
    pals = palettes(tims)
    shots = []
    for g, _, sprs in sprgroups.groups(layout):
        sprs = [s for s in sprs if is_text(s[6]) and s[4] and s[5]]
        if not sprs:
            continue
        im = Image.new("RGB", (320, 240), (40, 40, 60))
        for x, y, u, v, w, h, tp, clut in sprs:
            t, pal = tims[tp & 15], pals[((clut & 63) * 16, clut >> 6)]
            for yy in range(h):
                for xx in range(w):
                    i = t.px[v + yy][u + xx]
                    if i:
                        im.putpixel((160 + x + xx, 120 + y + yy), pal[i])
        bb = (0, max(0, 120 + min(s[1] for s in sprs) - 2), 320, min(240, 120 + max(s[1] + s[5] for s in sprs) + 2))
        shots.append((g, im.crop(bb)))
    out_dir.mkdir(parents=True, exist_ok=True)
    for page in range(0, len(shots), 24):
        part = shots[page:page + 24]
        H = sum(i.height + 14 for _, i in part)
        sheet = Image.new("RGB", (320, H), (0, 0, 0))
        d = ImageDraw.Draw(sheet)
        y = 0
        for g, i in part:
            d.text((2, y), f"g{g:02d}", fill=(255, 0, 255))
            sheet.paste(i, (0, y + 12))
            y += i.height + 14
        p = out_dir / f"{tag}_{page // 24}.png"
        sheet.resize((640, H * 2), Image.NEAREST).save(p)
        print(p)


FONT = "sans-b"
OUTLINE, FILL = 1, 15  # every credits glyph: index 15 core, index 1 dark rim (each CLUT row is a 0-15 ramp)
CLUT = {  # (atlas page x is 9, style) -> CLUT word: TIM 148 has its CLUT at (128, 496), the others at (0, 496)
    (True, "name"): 0x7c48, (True, "role"): 0x7cc8, (False, "name"): 0x7c00, (False, "role"): 0x7c80}
TITLE_RECT = (0, 0, 96, 24)  # g20 スタッフ in TIM 148, kept in place and relabelled


SIZE = 13  # 15 still fits the strip, but cast rows like "Composed & Arranged" then run off the 320 px screen


def strip(text, size):
    """(width, 16 rows of indices) for one line."""
    m = gfx_edit.render_mask(text, FONT, size, 254, 14)
    assert m, f"credits line too wide: {text!r}"
    cols = [x for x in range(254) if any(r[x] for r in m)]
    c = gfx_edit.Canvas(cols[-1] - cols[0] + 3, 16)
    gfx_edit.label(c, (0, 0, c.W, 16), text, font=FONT, size=size, style=(OUTLINE, {y: FILL for y in range(16)}))
    return c.W, c.px


def build(spec=None):
    """(layout bytes, {page x: Tim}) with the English roll; spec = gfx/credits_en.py GROUPS."""
    import credits_en
    spec = spec or credits_en.GROUPS
    layout = bytearray(extract.leaf(LAYOUT))
    tims = {k: gfx.load(p) for k, p in ATLAS.items()}
    title = gfx.load(ATLAS[9])
    for t in tims.values():
        t.px = [[0] * t.W for _ in range(t.H)]
    gfx_edit.label(title, TITLE_RECT, **credits_en.BIG)
    x0, y0, w0, h0 = TITLE_RECT
    for y in range(y0, y0 + h0):
        tims[9].px[y][x0:x0 + w0] = title.px[y][x0:x0 + w0]
    size = SIZE
    placed = {}  # (text, style) -> (page x, u, v, w); identical lines share one strip
    pages, cur = list(ATLAS), [9, 0, 24]  # page, u, v (TIM 148 rows 0-23 hold the title)
    seen = set()
    for g, off, sprs in sprgroups.groups(bytes(layout)):
        if g not in spec or off in seen:
            continue
        seen.add(off)
        slots = [k for k, s in enumerate(sprs) if is_text(s[6])]
        items = spec[g]
        assert len(items) <= len(slots), f"g{g}: {len(items)} lines, {len(slots)} sprites"
        for k, slot in enumerate(slots):
            o = off + 2 + 12 * slot
            x, y, u, v, w, h, tp, clut = sprs[slot]
            if k >= len(items):  # spare sprite: draws nothing
                SPR.pack_into(layout, o, 0, 0, 0, 0, 0, 0, tp, clut)
                continue
            ix, iy, text, style, align = items[k]
            if (text, style) not in placed:
                sw, px = strip(text, size)
                page, u_, v_ = cur
                # the roll draws quads with u+w and v+h as u8: an edge at 256 wraps to 0 (mirrored, sheared strip)
                if u_ + sw > 255:
                    u_, v_ = 0, v_ + 16
                if v_ + 16 > 255:
                    page = pages[pages.index(page) + 1]  # IndexError: the four atlases are full
                    u_, v_ = 0, 0
                for r in range(16):
                    tims[page].px[v_ + r][u_:u_ + sw] = px[r]
                placed[(text, style)] = (page, u_, v_, sw)
                cur = [page, u_ + sw, v_]
            page, su, sv, sw = placed[(text, style)]
            sx = {"l": ix, "c": ix - sw // 2, "r": ix - sw}[align]
            assert -160 <= sx and sx + sw <= 160, f"g{g} {text!r} leaves the screen ({sx}..{sx + sw})"
            SPR.pack_into(layout, o, sx, iy, su, sv, sw, 16, (tp & ~15) | page, CLUT[(page == 9, style)])
    missing = set(spec) - {g for g, _, _ in sprgroups.groups(bytes(layout))}
    assert not missing, missing
    return bytes(layout), tims


def leaves():
    """{"DE_ST07.PAC/leaf": bytes}: the layout and the four atlases (gfx_edit.patched_leaves adds them)."""
    layout, tims = build()
    out = {LAYOUT: layout}
    for k, p in ATLAS.items():
        out[p] = tims[k].encode()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("--jp", action="store_true", help="the original layout and atlases")
    r.add_argument("--out", default=str(ROOT / "work" / "gfx" / "credits"))
    a = ap.parse_args()
    if a.jp:
        layout, tims = extract.leaf(LAYOUT), {k: gfx.load(p) for k, p in ATLAS.items()}
    else:
        lv = leaves()
        Path(a.out).mkdir(parents=True, exist_ok=True)
        for k, p in ATLAS.items():
            gfx.Tim(lv[p]).image(0, 2).save(Path(a.out) / f"atlas{k}.png")
        layout, tims = lv[LAYOUT], {k: gfx.Tim(lv[p]) for k, p in ATLAS.items()}
    render(layout, tims, Path(a.out), "jp" if a.jp else "en")


if __name__ == "__main__":
    main()
