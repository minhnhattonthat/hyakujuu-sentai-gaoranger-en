"""fmvdiff.py: frames of a built STR that differ from the original above the subtitle band (re-encode damage).

    python -X utf8 tools/fmvdiff.py RB0 [--overlay build/overlay] [--thresh 40] [--png DIR]

Mean abs diff per macroblock above y 160 (subtitles sit below); prints frames whose worst block exceeds --thresh.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fmvcap  # noqa: E402
import strv  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--overlay", default=str(fmvcap.ROOT / "build" / "overlay"))
    ap.add_argument("--thresh", type=float, default=40)
    ap.add_argument("--png")
    a = ap.parse_args()
    o = strv.sectors(fmvcap.TREE / "XA" / f"{a.name}.STR")
    n = strv.sectors(Path(a.overlay) / "XA" / f"{a.name}.STR")
    bad = 0
    for fno, secs, hd in strv.frames(o):
        if all(o[i * strv.SECTOR:(i + 1) * strv.SECTOR] == n[i * strv.SECTOR:(i + 1) * strv.SECTOR] for i in secs):
            continue
        im = []
        for d in (o, n):
            q, _, blocks, _ = strv.parse(strv.frame_bytes(d, secs), hd["w"], hd["h"])
            im.append(strv.to_rgb(blocks, q, hd["w"], hd["h"]).astype(float))
        diff = np.abs(im[0] - im[1]).mean(-1)[:160]
        mb = diff.reshape(10, 16, 20, 16).mean((1, 3))
        if mb.max() > a.thresh:
            bad += 1
            y, x = np.unravel_index(mb.argmax(), mb.shape)
            print(f"{a.name} frame {fno}: worst block ({x},{y}) diff {mb.max():.0f}")
            if a.png:
                Path(a.png).mkdir(parents=True, exist_ok=True)
                Image.fromarray(np.concatenate(im, 1).astype(np.uint8)).save(Path(a.png) / f"{a.name}_{fno:05d}.png")
    print(f"{a.name}: {bad} damaged frames")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
