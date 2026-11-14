"""Phase 5: English font, en.tbl, VWF EXE hook and text insertion (marker build)."""
import json
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402
import extract  # noqa: E402
import font  # noqa: E402
import insert  # noqa: E402
from tbl import Table  # noqa: E402

need_disc = pytest.mark.skipif(not (extract.DATA / "DS_ST01.PAC").is_file(), reason="disc not dumped (docs/re/disc.md)")


def test_font_selftest():
    font.selftest()


def test_en_tbl_is_current():
    want = (ROOT / "tbl" / "en.tbl").read_text(encoding="utf-8")
    assert font.write_tbl().read_text(encoding="utf-8") == want, "tbl/en.tbl is stale: run tools/font.py"


def test_en_tbl_roundtrip():
    en = Table.load(ROOT / "tbl" / "en.tbl")
    s = "The quick brown fox, 0123456789! [ds01-002e] ({n}A-Z) ○×"
    assert en.decode(en.encode(s + "{end}"))[0] == s + "{end}"
    assert en.encode(" ") == b"\x00\xa0"


def test_line_px():
    assert font.line_px("0" * 37 + "mi") == 232
    assert font.line_px("{col:00}M") == 8


@need_disc
def test_exe_hook(tmp_path):
    build.build_exe(tmp_path)
    exe = (tmp_path / "SLPS_033.53").read_bytes()
    orig = (extract.DATA.parent / "SLPS_033.53").read_bytes()
    o = 0x80022A6C - 0x80010000 + 0x800
    w = font.widths()
    assert exe[o:o + len(w)] == w
    diff = [i for i in range(len(exe)) if exe[i] != orig[i]]
    lo, hi = 0x800 + 0x80022A6C - 0x80010000, 0x800 + 0x80022BC4 - 0x80010000
    for i in diff:  # every changed byte is at a site build.HOOKS checks
        a = i - 0x800 + 0x80010000
        assert lo <= i < hi or any(k <= a < k + len(v) // 2 for k, v in build.HOOKS.items()), hex(a)


@need_disc
def test_marker_insert(tmp_path):
    names = insert.insert(tmp_path, marker=True)  # asserts every written leaf reads back
    en = Table.load(ROOT / "tbl" / "en.tbl")
    assert "DS_ST01.PAC" in names
    blob = insert.leaf_of((tmp_path / "DATA" / "DS_ST01.PAC").read_bytes(), "13_12")
    txt = en.decode(blob, struct.unpack_from("<H", blob, 4)[0])[0]  # slot 0 -> ds01-002e
    assert txt.startswith("[ds01-002e] The quick"), txt
    for f in insert.FONT_LEAVES:
        name, leaf = f.split("/")
        assert insert.leaf_of((tmp_path / "DATA" / name).read_bytes(), leaf) == font.patch_tim(extract.leaf(f))
    assert json.loads((ROOT / "script" / "ds01.json").read_text(encoding="utf-8"))["files"] == ["DS_ST01.PAC/13_12"]
