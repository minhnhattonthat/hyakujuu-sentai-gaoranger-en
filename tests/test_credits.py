"""tools/credits.py: every English line lands on screen as a strip the engine can draw (u+w, v+h stay below 256: the
roll computes them as u8), strips don't overlap, and every Japanese text sprite now points at English or nothing."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import credits  # noqa: E402
import extract  # noqa: E402

pytestmark = pytest.mark.skipif(not (extract.DATA / "DE_ST07.PAC").is_file(), reason="no unpacked disc tree")


def test_layout():
    layout, tims = credits.build()
    import credits_en
    rects = set()
    for g, _, sprs in credits.sprgroups.groups(layout):
        text = [s for s in sprs if credits.is_text(s[6])]
        if g not in credits_en.GROUPS:
            assert not text or g == 20, f"g{g}: Japanese text sprites left"  # g20: the title, relabelled in place
            continue
        shown = [s for s in text if s[4]]
        assert len(shown) == len(credits_en.GROUPS[g])
        for x, y, u, v, w, h, tp, clut in shown:
            assert u + w <= 255 and v + h <= 255 and -160 <= x and x + w <= 160
            t = tims[tp & 15]
            assert any(any(r[u:u + w]) for r in t.px[v:v + h]), f"g{g}: empty strip"
            rects.add((tp & 15, u, v, w))
    for a in rects:  # strips shared by identical lines are one rect; distinct ones never overlap
        for b in rects:
            if a != b and a[0] == b[0] and a[2] == b[2]:
                assert a[1] + a[3] <= b[1] or b[1] + b[3] <= a[1], (a, b)
