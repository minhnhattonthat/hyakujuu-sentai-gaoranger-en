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


def render_mask(text, font, size, box_w, box_h, xscale=1.0, tracking=0):
    """1-bit text mask (list of rows of 0/1), centred in box_w x box_h; None if it doesn't fit."""
    f = ImageFont.truetype(str(ROOT / "fonts" / FONTS.get(font, font)), size)
    widths = [f.getlength(c) for c in text]
    tw = int(sum(widths) + tracking * (len(text) - 1) + 2)
    l, top, r, bot = f.getbbox(text)
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
    im = im.crop(bb)
    if xscale != 1.0:
        im = im.resize((max(1, round(im.width * xscale)), im.height), Image.NEAREST)
    if im.width > box_w or im.height > box_h:
        return None
    ox, oy = (box_w - im.width) // 2, (box_h - im.height + 1) // 2
    m = [[0] * box_w for _ in range(box_h)]
    for y in range(im.height):
        for x in range(im.width):
            if im.getpixel((x, y)):
                m[oy + y][ox + x] = 1
    return m


def label(t, rect, text, font="sans-b", size=None, outline=None, fill=None, xscale=1.0, tracking=0, ring=1,
          min_size=7):
    """Replace rect's content with `text`. size None: the largest that fits (rect minus the outline ring)."""
    x0, y0, w, h = rect
    o_idx, rows = style_of(t, rect)
    o_idx = o_idx if outline is None else outline
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            t.px[y][x] = 0
    bw, bh = w - 2 * ring, h - 2 * ring
    m = None
    for s in ([size] if size else range(bh + 8, min_size - 1, -1)):
        m = render_mask(text, font, s, bw, bh, xscale, tracking)
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
    if ring:
        for x, y in ink:
            for dx, dy in N8:
                p = (x + dx, y + dy)
                if p not in ink and x0 <= p[0] < x0 + w and y0 <= p[1] < y0 + h:
                    t.px[p[1]][p[0]] = o_idx
    for x, y in ink:
        t.px[y][x] = fill_at(y)


def apply(t, edits):
    """edits: list of dicts {rect, text, ...label kwargs} or {rect, clear: True}. Returns the rects."""
    rects = []
    for e in edits:
        e = dict(e)
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
    for sha, (row, eds) in edits.EDITS.items():
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
    return leaves


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
