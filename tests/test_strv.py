"""tools/strv.py re-encodes original STR frames bit for bit; fmvcap's STRs pass verify.check_fmv, which catches a
sector changed outside the caption frames and a bad EDC."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fmvcap  # noqa: E402
import mkdisc  # noqa: E402
import strv  # noqa: E402
import verify  # noqa: E402

pytestmark = pytest.mark.skipif(not (mkdisc.TREE / "XA" / "RB2.STR").is_file(), reason="no unpacked disc tree")


def test_roundtrip():
    data = strv.sectors(mkdisc.TREE / "XA" / "RB2.STR")
    for fno, secs, hd in strv.frames(data)[::25]:
        buf = strv.frame_bytes(data, secs)
        q, _, blocks, _ = strv.parse(buf, hd["w"], hd["h"])
        out = strv.replace_blocks(data, secs, hd, blocks, q)
        assert all(out[i] == data[i * strv.SECTOR:(i + 1) * strv.SECTOR] for i in secs), fno


def test_check_fmv(tmp_path):
    fmvcap.cached(tmp_path)
    assert verify.check_fmv(tmp_path) == []
    f = tmp_path / "XA" / "RB2.STR"
    b = bytearray(f.read_bytes())
    b[8 + 100] ^= 1  # sector 0: outside the caption, EDC now wrong too
    i = min(fmvcap.caption_sectors("RB2"))
    b[i * strv.SECTOR + 8 + 100] ^= 1  # inside the caption range, EDC not recomputed
    f.write_bytes(b)
    errs = verify.check_fmv(tmp_path)
    assert any("sector 0 outside" in e for e in errs) and any(f"sector {i} EDC" in e for e in errs)


def test_subtitle_burn(tmp_path, monkeypatch):
    subs = tmp_path / "subs.tsv"
    subs.write_text("RN2\t0.5\t1.0\tテスト\tPress on, rangers!\n", encoding="utf-8")
    monkeypatch.setattr(fmvcap, "SUBS", subs)
    assert fmvcap.edited()["RN2"] == [(16, 31)]
    orig = strv.sectors(mkdisc.TREE / "XA" / "RN2.STR")
    data = bytearray(orig)
    assert fmvcap.subtitle("RN2", data, fmvcap.load_subs()["RN2"]) == 16
    fr = {f[0]: f for f in strv.frames(bytes(data))}
    _, secs, hd = fr[20]
    q, _, blocks, _ = strv.parse(strv.frame_bytes(data, secs), hd["w"], hd["h"])
    band = strv.to_rgb(blocks, q, hd["w"], hd["h"])[180:205, 40:280]
    assert (band.min(-1) > 180).sum() > 30 and (band.max(-1) < 50).sum() > 100  # white letters, black outline
    _, secs, _ = fr[40]  # outside the subtitle: untouched
    assert all(data[i * strv.SECTOR:(i + 1) * strv.SECTOR] == orig[i * strv.SECTOR:(i + 1) * strv.SECTOR]
               for i in secs)
