"""gfx_edit.py: English lettering into TIM index arrays (gfx/edits.py says what goes where).

A label replaces the Japanese inside one rect of a texture page: the rect is cleared to index 0 (transparent), the
English is rendered without antialiasing (fonts/, open licence), every glyph pixel takes the fill index the original
used on that row (the game's vertical gradients survive) and an 8-neighbour ring around the glyphs takes the outline
index. Outline and per-row fill are read from the original pixels in the rect unless the edit names them.

    boxes(tim, rect)        -> ink bounding boxes inside rect (to find label rects)
    apply(tim, edits)       -> changes tim.px in place, returns the list of rects touched
    preview(out_dir)        -> original | English sheet per edited image (gfx.py preview)
"""
import functools
import os
import struct
import sys
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "gfx"))
import gfx  # noqa: E402

FONTS = {"sans-b": "LiberationSans-Bold.ttf", "sans": "LiberationSans-Regular.ttf", "anton": "Anton-Regular.ttf"}
N8 = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]


def boxes(t, rect, gap=3):
    """Bounding boxes of ink (index != 0) in rect, rows split on empty rows, columns split on `gap` empty columns."""
    x0, y0, w, h = rect
    rows = [y for y in range(y0, y0 + h) if any(t.px[y][x0:x0 + w])]
    bands, cur = [], []
    for y in rows:
        if cur and y != cur[-1] + 1:
            bands.append(cur)
            cur = []
        cur.append(y)
    if cur:
        bands.append(cur)
    out = []
    for b in bands:
        cols = [x for x in range(x0, x0 + w) if any(t.px[y][x] for y in b)]
        start = prev = cols[0]
        for x in cols[1:] + [10 ** 9]:
            if x - prev > gap:
                out.append((start, b[0], prev - start + 1, b[-1] - b[0] + 1))
                start = x
            prev = x
    return out


def style_of(t, rect):
    """(outline index, {row: fill index}) read from the original ink in rect."""
    x0, y0, w, h = rect
    edge, inner = Counter(), {}
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            v = t.px[y][x]
            if not v:
                continue
            nb = [t.px[y + dy][x + dx] if 0 <= y + dy < t.H and 0 <= x + dx < t.W else 0 for dx, dy in N8]
            if 0 in nb:
                edge[v] += 1
            else:
                inner.setdefault(y, Counter())[v] += 1
    outline = edge.most_common(1)[0][0]
    fill = {y: c.most_common(1)[0][0] for y, c in inner.items()}
    for y, c in inner.items():  # a row whose inner pixels are mostly outline (bar joints): next best
        if fill[y] == outline and len(c) > 1:
            fill[y] = c.most_common(2)[1][0]
    return outline, fill


def render_mask(text, font, size, box_w, box_h, xscale=1.0, tracking=0, align="c"):
    """1-bit text mask (list of rows of 0/1) in box_w x box_h (align l/c/r, centred vertically); None if it
    doesn't fit."""
    f = ImageFont.truetype(str(ROOT / "fonts" / FONTS.get(font, font)), size)
    widths = [f.getlength(c) for c in text]
    tw = int(sum(widths) + tracking * (len(text) - 1) + 2)
    # one vertical band per font/size (cap top to descender when there is lowercase), so labels drawn side by
    # side share a baseline
    ref = f.getbbox("Hg" if any(c.islower() for c in text) else "H")
    l, top, r, bot = f.getbbox(text)
    top, bot = min(top, ref[1]), max(bot, ref[3])
    im = Image.new("1", (tw + 4, bot + 4), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = "1"
    x = 1
    for c, cw in zip(text, widths):
        d.text((x, 0), c, font=f, fill=1)
        x += cw + tracking
    bb = im.getbbox()
    if not bb:
        return [[0] * box_w for _ in range(box_h)]
    im = im.crop((bb[0], top, bb[2], bot))
    if xscale != 1.0:
        im = im.resize((max(1, round(im.width * xscale)), im.height), Image.NEAREST)
    if im.width > box_w or im.height > box_h:
        return None
    lead = round(f.getlength(" ") * (len(text) - len(text.lstrip(" "))))  # kept spaces: gap to the next piece
    trail = round(f.getlength(" ") * (len(text) - len(text.rstrip(" "))))
    if im.width + (lead if align == "l" else trail if align == "r" else 0) > box_w:
        return None
    ox = {"l": lead, "c": (box_w - im.width) // 2, "r": box_w - im.width - trail}[align]
    oy = (box_h - im.height + 1) // 2
    m = [[0] * box_w for _ in range(box_h)]
    for y in range(im.height):
        for x in range(im.width):
            if im.getpixel((x, y)):
                m[oy + y][ox + x] = 1
    return m


def label(t, rect, text, font="sans-b", size=None, outline=None, fill=None, xscale=1.0, tracking=0, ring=1,
          min_size=7, glow=None, align="c", style=None):
    """Replace rect's content with `text`. size None: the largest that fits (rect minus the outline ring).
    glow: index list by distance (replaces the outline; ring = its length). style: (outline, {y: fill}) to use
    instead of reading the rect (composite labels)."""
    x0, y0, w, h = rect
    ring = len(glow) if glow else ring
    o_idx, rows = style or style_of(t, rect)
    o_idx = o_idx if outline is None else outline
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            t.px[y][x] = 0
    bw, bh = w - 2 * ring, h - 2 * ring
    m = None
    for s in ([size] if size else range(bh + 8, min_size - 1, -1)):
        m = render_mask(text, font, s, bw, bh, xscale, tracking, align)
        if m:
            break
    if not m:
        raise SystemExit(f"{text!r} doesn't fit {rect} at size {size or min_size} ({font}, xscale {xscale})")

    def fill_at(y):
        if fill is not None:
            return fill
        near = min(rows, key=lambda r: abs(r - y))
        return rows[near]

    ink = {(x0 + ring + x, y0 + ring + y) for y, r in enumerate(m) for x, v in enumerate(r) if v}
    if glow:  # glow[d-1] = index at Euclidean distance d from the glyphs (ramp palettes: game over)
        R = len(glow)
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                if (x, y) in ink:
                    continue
                d2 = min(((x - gx) ** 2 + (y - gy) ** 2 for gx, gy in ink
                          if abs(gx - x) <= R and abs(gy - y) <= R), default=None)
                if d2 is not None and d2 <= R * R:
                    t.px[y][x] = glow[max(1, round(d2 ** 0.5)) - 1]
    elif ring:
        for x, y in ink:
            for dx, dy in N8:
                p = (x + dx, y + dy)
                if p not in ink and x0 <= p[0] < x0 + w and y0 <= p[1] < y0 + h:
                    t.px[p[1]][p[0]] = o_idx
    for x, y in ink:
        t.px[y][x] = fill_at(y)


class Canvas:
    def __init__(self, w, h):
        self.W, self.H, self.px = w, h, [[0] * w for _ in range(h)]


def composite(t, pieces, text, **kw):
    """Render text once across the pieces' total width (style of the first piece), then cut it into the pieces,
    each centred vertically on the strip."""
    o_idx, rows = style_of(t, pieces[0])
    H = max(r[3] for r in pieces)
    top = pieces[0][1] - (H - pieces[0][3]) // 2
    c = Canvas(sum(r[2] for r in pieces), H)
    label(c, (0, 0, c.W, H), text, style=(o_idx, {y - top: v for y, v in rows.items()}), **kw)
    cx = 0
    for x0, y0, w, h in pieces:
        dy = (H - h) // 2
        for y in range(h):
            t.px[y0 + y][x0:x0 + w] = c.px[dy + y][cx:cx + w]
        cx += w


def apply(t, edits):
    """edits: list of dicts {rect, text, ...label kwargs} or {rect, clear: True}. Returns the rects."""
    rects = []
    for e in edits:
        e = dict(e)
        if "rects" in e:  # one label cut across pieces the game draws side by side (データ+の+ロ+ード)
            pieces = [tuple(r) for r in e.pop("rects")]
            composite(t, pieces, e.pop("text"), **e)
            rects += pieces
            continue
        rect = tuple(e.pop("rect"))
        if e.pop("clear", False):
            for y in range(rect[1], rect[1] + rect[3]):
                for x in range(rect[0], rect[0] + rect[2]):
                    t.px[y][x] = 0
        else:
            label(t, rect, e.pop("text"), **e)
        rects.append(rect)
    return rects


def patched():
    """{sha prefix: (Tim original, Tim edited, rects)} for every image in gfx/edits.py."""
    import edits
    out = {}
    skip = os.environ.get("GFX_SKIP", "").split(",")  # bisect: GFX_SKIP=sha,.. builds without those edits
    for sha, (row, eds) in edits.EDITS.items():
        if sha in skip:
            continue
        path, off = gfx.copies(sha)[0]
        orig = gfx.load(path, off)
        new = gfx.load(path, off)
        rects = apply(new, eds)
        changed = [(x, y) for y in range(new.H) for x in range(new.W) if new.px[y][x] != orig.px[y][x]]
        for x, y in changed:  # nothing outside the declared rects
            assert any(rx <= x < rx + rw and ry <= y < ry + rh for rx, ry, rw, rh in rects), (sha, x, y)
        out[sha] = (orig, new, rects, row)
    return out


@functools.cache  # insert.py and verify.py both ask; the edits are slow pure Python
def patched_leaves():
    """{"PAC/leaf": bytes} for every copy of every edited image (a leaf holding two edited images gets both)."""
    leaves = {}
    for sha, (orig, new, _, _) in patched().items():
        for path, off in gfx.copies(sha):
            cur = leaves.get(path) or gfx.extract.leaf(path)
            t = gfx.Tim(cur, off)
            assert t.px == orig.px, f"{path}+{off:x} is not the image {sha}"
            t.px = new.px
            leaves[path] = t.encode()
    import credits  # staff roll: rebuilt atlases + sprite layout (tools/credits.py)
    for path, data in credits.leaves().items():
        assert path not in leaves, f"{path}: both a TIM edit and the credits"
        leaves[path] = data
    import edits
    for path in edits.SPRITE_LEAVES:
        leaves[path], n = sprite_fix(leaves.get(path) or gfx.extract.leaf(path), edits.SPRITE_FIXES)
        assert n == 2, f"{path}: {n} sprite groups fixed, expected 2"
    return leaves


SPR = struct.Struct("<hhBBBBHH")  # x, y, u, v, w, h, tpage, clut (sprite group record, tools/sprgroups.py)


def sprite_fix(data, fixes):
    """Rewrite every group (u16 count + records) whose records match `old` (clut aside) to `new`; returns
    (bytes, groups rewritten)."""
    d, n = bytearray(data), 0
    for old, new in fixes:
        head = struct.pack("<H", len(old)) + SPR.pack(*old[0], 0)[:-2]
        i = d.find(head)
        while i >= 0:
            recs = [SPR.unpack_from(d, i + 2 + SPR.size * k) for k in range(len(old))]
            if all(r[:7] == o for r, o in zip(recs, old)):
                for k, (r, s) in enumerate(zip(recs, new)):
                    SPR.pack_into(d, i + 2 + SPR.size * k, *s, r[7])
                n += 1
            i = d.find(head, i + 1)
    return bytes(d), n


def preview(out_dir, zoom=2):
    out_dir.mkdir(parents=True, exist_ok=True)
    for sha, (orig, new, rects, row) in patched().items():
        a, b = orig.image(row, zoom), new.image(row, zoom)
        sheet = Image.new("RGB", (a.width * 2 + 8, a.height), (255, 0, 255))
        sheet.paste(a, (0, 0))
        sheet.paste(b, (a.width + 8, 0))
        p = out_dir / f"{sha}.png"
        sheet.save(p)
        print(p)
