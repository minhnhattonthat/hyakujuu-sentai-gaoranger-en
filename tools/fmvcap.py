"""English robot-name captions burned into the FMVs (docs/re/fmv.md, D17).

Each caption is static (white letters, thick blue outline) over a moving scene. For every frame in its range:
the caption mask (pixels caption-coloured in most full-strength frames, dilated) is filled by harmonic inpainting,
the English name is drawn in the same colours at the strength the Japanese one had in that frame (fades), and
only the macroblocks the edit touches are re-encoded (strv.py); the rest keep their original codes bit for bit.

    python -X utf8 tools/fmvcap.py OUTDIR [--preview DIR]     # writes OUTDIR/XA/<name>.STR (build.py calls it)
"""
import argparse
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
import strv  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TREE = ROOT / "work" / "disc" / "tree"
FONT = ROOT / "fonts" / "LiberationSans-Bold.ttf"

# file, first..last frame carrying any caption pixel (fades included), caption box x0,y0,x1,y1, English
CAPTIONS = [
    ("RB0", 1366, 1452, (98, 172, 222, 204), "GAOKING"),  # caps as the TIM 136 banners (D13); sans "GaoIcarus"
    ("RB2", 477, 536, (58, 162, 266, 195), "GAOMUSCLE STRIKER"),  # read as "Gaolcarus"
    ("RB4", 665, 736, (94, 172, 234, 203), "GAOICARUS"),
]
W, H = 320, 208


def is_blue(a):
    return (a[..., 2] > 120) & (a[..., 2] - a[..., 0] > 40) & (a[..., 2] - a[..., 1] > 30)


def is_white(a):
    return a.min(-1) > 170


def inpaint(img, mask, iters=400):
    """Harmonic fill of mask (bool HxW) in img (HxWx3 float) from the pixels around it."""
    out = img.copy()
    ys, xs = np.nonzero(mask)
    y0, y1, x0, x1 = max(ys.min() - 1, 0), min(ys.max() + 2, img.shape[0]), max(xs.min() - 1, 0), \
        min(xs.max() + 2, img.shape[1])
    sub, m = out[y0:y1, x0:x1], mask[y0:y1, x0:x1]
    sub[m] = sub[~m].mean(0)
    k = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], float)
    wsum = ndimage.convolve(np.ones(m.shape), k, mode="constant")
    for _ in range(iters):
        avg = np.stack([ndimage.convolve(sub[..., c], k, mode="constant") for c in range(3)], -1) / wsum[..., None]
        sub[m] = avg[m]
    return out


def render(text, box, maxw, fill, edge):
    """RGBA layer HxW: text centred on box (the Japanese caption's extent), as tall as it, blue outline."""
    x0, y0, x1, y1 = box
    stroke = 3
    size = 40
    while True:
        f = ImageFont.truetype(str(FONT), size)
        l, t, r, b = f.getbbox(text, stroke_width=stroke)
        if r - l <= maxw and b - t <= y1 - y0:
            break
        size -= 1
    layer = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(layer)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    d.text((cx - (l + r) / 2, cy - (t + b) / 2), text, font=f, fill=tuple(fill) + (255,), stroke_width=stroke,
           stroke_fill=tuple(edge) + (255,))
    return np.asarray(layer).astype(float) / 255


def caption(name, first, last, box, text, preview=None):
    data = bytearray(strv.sectors(TREE / "XA" / f"{name}.STR"))
    fr = [f for f in strv.frames(bytes(data)) if first <= f[0] <= last]
    x0, y0, x1, y1 = box
    dec = []
    for fno, secs, hd in fr:
        q, _, blocks, _ = strv.parse(strv.frame_bytes(data, secs), W, H)
        dec.append((fno, secs, hd, q, blocks, strv.to_rgb(blocks, q, W, H).astype(float)))
    inbox = np.zeros((H, W), bool)
    inbox[y0:y1, x0:x1] = True
    blue = np.array([(is_blue(r) & inbox).sum() for *_, r in dec])
    full = [r for (*_, r), n in zip(dec, blue) if n >= 0.8 * blue.max()]
    fb = np.mean([is_blue(r) for r in full], 0) >= 0.6
    fw = np.mean([is_white(r) for r in full], 0) >= 0.6
    core = fw & inbox & ndimage.binary_dilation(fb, iterations=3)  # letter fill: white next to the outline
    cap = ndimage.binary_fill_holes((fb | core) & inbox)
    mask = ndimage.binary_dilation(cap, iterations=2)
    px = np.concatenate([r[(fb | core) & inbox] for r in full])
    lum = px @ np.array([0.299, 0.587, 0.114])
    edge = np.median(px[lum <= np.percentile(lum, 15)], 0)  # the outline's dark middle, not its antialiased rim
    fill = np.median(px[lum >= np.percentile(lum, 70)], 0)
    ys, xs = np.nonzero(cap)
    layer = render(text, (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1), x1 - x0, fill.astype(int),
                   edge.astype(int))
    bgs = [inpaint(r, mask) for *_, r in dec]
    # caption strength per frame (fades): its contrast against the filled-in scene, relative to full strength
    con = np.array([np.linalg.norm(r[cap] - bg[cap], axis=-1).mean() for (*_, r), bg in zip(dec, bgs)])
    base = con[0]  # each range starts on a caption-free frame: the inpaint's own error
    strength = np.clip((con - base) / (np.percentile(con, 75) - base), 0, 1)
    touch = mask | ndimage.binary_dilation(layer[..., 3] > 0, iterations=1)
    mbs = {(x // 16, y // 16) for y, x in zip(*np.nonzero(touch))}
    changed, cuts = 0, []
    for (fno, secs, hd, q, blocks, rgb), bg, st in zip(dec, bgs, strength):
        if st < 0.05:  # no visible caption: keep the frame as it is
            continue
        a = layer[..., 3:] * st
        img = np.clip(bg * (1 - a) + layer[..., :3] * 255 * a, 0, 255).astype(np.uint8)
        cuts.append((put(data, name, fno, secs, hd, q, blocks, img, mbs, preview), fno))
        changed += 1
    trimmed = [f"{f}:{c}" for c, f in cuts if c < 63]
    print(f"fmvcap: {name}: frames trimmed to fit (frame:last zigzag index kept): {' '.join(trimmed) or '-'}")
    return bytes(data), changed


def put(data, name, fno, secs, hd, q, blocks, img, mbs, preview=None):
    """Re-encode macroblocks mbs of one frame from img into data (in place); returns the zigzag cut used."""
    mh = (H + 15) // 16
    for cut in range(63, 9, -3):  # drop high frequencies of the edited blocks until the frame fits
        new = list(blocks)
        for mx, my in mbs:
            i = (mx * mh + my) * 6
            new[i:i + 6] = strv.encode_mb(img[my * 16:my * 16 + 16, mx * 16:mx * 16 + 16], q, cut)
        out = strv.replace_blocks(data, secs, hd, new, q)
        if out is not None:
            break
    else:  # still too big: the whole frame from the decoded image at a coarser qscale (frees bits everywhere)
        full = strv.to_rgb(blocks, q, W, H)
        for mx, my in mbs:
            full[my * 16:my * 16 + 16, mx * 16:mx * 16 + 16] = img[my * 16:my * 16 + 16, mx * 16:mx * 16 + 16]
        for q2 in range(q + 1, 64):
            new = [b for mx in range(W // 16) for my in range(mh)
                   for b in strv.encode_mb(full[my * 16:my * 16 + 16, mx * 16:mx * 16 + 16], q2, 63)]
            out = strv.replace_blocks(data, secs, hd, new, q2)
            if out is not None:
                cut, q = -q2, q2  # negative: the frame's new qscale (printed by the callers)
                break
        else:
            sys.exit(f"{name} frame {fno}: re-encoded text does not fit its {len(secs)} sectors")
    for i, s in out.items():
        data[i * strv.SECTOR:(i + 1) * strv.SECTOR] = s
    if preview:
        os.makedirs(preview, exist_ok=True)
        Image.fromarray(strv.to_rgb(new, q, W, H)).save(os.path.join(preview, f"{name}_f{fno:05d}.png"))
    return cut


# Subtitles (script/subs.tsv): spoken lines burned into the bottom of the FMV frames.
SUBS = ROOT / "script" / "subs.tsv"
FPS = 30  # STR frames per second (RB0: 1464 frames, 48.8 s of audio)
SUB_SIZE, SUB_STROKE, SUB_BOTTOM, SUB_MAXW = 13, 2, 204, 304


def load_subs():
    """{STR name: [(first frame, last frame, english)]} from script/subs.tsv (src, start s, end s, ja, en; '#' and
    rows with no en are skipped; CDXA* rows are in-game voice, not FMV)."""
    out = {}
    if not SUBS.is_file():
        return out
    for line in SUBS.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        src, start, end, _ja, en = (line.split("\t") + [""] * 5)[:5]
        if en.strip() and (TREE / "XA" / f"{src}.STR").is_file():
            out.setdefault(src, []).append((int(float(start) * FPS) + 1, int(float(end) * FPS) + 1, en.strip()))
    return out


def wrap(text, f):
    """Lines of text no wider than SUB_MAXW ('|' forces a break)."""
    lines = []
    for part in text.split("|"):
        cur = ""
        for w in part.split():
            t = f"{cur} {w}".strip()
            if cur and f.getlength(t) + 2 * SUB_STROKE > SUB_MAXW:
                lines.append(cur)
                t = w
            cur = t
        lines.append(cur)
    return lines


def sub_layer(text):
    """RGBA layer HxW: white text, black outline, centred at the bottom of the frame."""
    f = ImageFont.truetype(str(FONT), SUB_SIZE)
    lines = wrap(text, f)
    assert len(lines) <= 2, f"subtitle needs {len(lines)} lines (max 2): {text!r}"
    layer = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(layer)
    lh = SUB_SIZE + 2
    y = SUB_BOTTOM - lh * len(lines)
    for ln in lines:
        d.text((W / 2, y), ln, font=f, anchor="mt", fill=(255, 255, 255, 255), stroke_width=SUB_STROKE,
               stroke_fill=(0, 0, 0, 255))
        y += lh
    return np.asarray(layer).astype(float) / 255


def subtitle(name, data, subs, preview=None):
    """Burn subs [(first, last, en)] into STR data (bytearray, in place); returns frames changed."""
    layers = [(a, b, sub_layer(t)) for a, b, t in subs]
    changed, cuts = 0, []
    for fno, secs, hd in strv.frames(bytes(data)):
        on = [ly for a, b, ly in layers if a <= fno <= b]
        if not on:
            continue
        layer = on[-1]
        q, _, blocks, _ = strv.parse(strv.frame_bytes(data, secs), W, H)
        rgb = strv.to_rgb(blocks, q, W, H).astype(float)
        a = layer[..., 3:]
        img = np.clip(rgb * (1 - a) + layer[..., :3] * 255 * a, 0, 255).astype(np.uint8)
        mbs = {(x // 16, y // 16) for y, x in zip(*np.nonzero(layer[..., 3] > 0))}
        cuts.append((put(data, name, fno, secs, hd, q, blocks, img, mbs, preview), fno))
        changed += 1
    low = min((c for c, _ in cuts), default=63)
    print(f"fmvcap: {name}: {changed} subtitle frames, lowest zigzag cut {low}")
    return changed


def edited():
    """{STR name: [(first, last frame)]}: every frame range the build may change (captions + subtitles)."""
    out = {}
    for c in CAPTIONS:
        out.setdefault(c[0], []).append((c[1], c[2]))
    for name, subs in load_subs().items():
        out.setdefault(name, []).extend((a, b) for a, b, _ in subs)
    return out


def cached(overlay):
    """build.py: the edited STRs into overlay/XA/, from build/fmvcache/<hash of code, font, subs> when present."""
    import hashlib
    import shutil
    srcs = [Path(__file__), Path(strv.__file__), FONT] + ([SUBS] if SUBS.is_file() else [])
    h = hashlib.sha1(b"".join(p.read_bytes() for p in srcs)).hexdigest()[:12]
    cache = ROOT / "build" / "fmvcache" / h
    names = edited()
    if not all((cache / "XA" / f"{n}.STR").is_file() for n in names):
        shutil.rmtree(cache.parent, ignore_errors=True)
        build(cache)
    for n in names:
        (Path(overlay) / "XA").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(cache / "XA" / f"{n}.STR", Path(overlay) / "XA" / f"{n}.STR")


def caption_sectors(name):
    """Sector indexes of the frames a caption or subtitle may change (verify.py)."""
    data = strv.sectors(TREE / "XA" / f"{name}.STR")
    rs = edited()[name]
    return {i for fno, secs, _ in strv.frames(data) if any(a <= fno <= b for a, b in rs) for i in secs}


def build(outdir, preview=None):
    subs = load_subs()
    for name in edited():
        data = bytearray(strv.sectors(TREE / "XA" / f"{name}.STR"))
        for n, first, last, box, text in CAPTIONS:
            if n == name:
                cdata, k = caption(name, first, last, box, text, preview)
                data[:] = cdata
                print(f"fmvcap: {name} {k} frames -> {text}")
        if name in subs:
            subtitle(name, data, subs[name], preview)
        p = Path(outdir) / "XA" / f"{name}.STR"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("--preview")
    a = ap.parse_args()
    build(a.out, a.preview)


if __name__ == "__main__":
    main()
