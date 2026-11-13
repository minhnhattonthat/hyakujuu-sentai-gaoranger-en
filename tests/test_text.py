import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import make_tbl  # noqa: E402
import pac  # noqa: E402
import textscan  # noqa: E402

TREE = ROOT / "work" / "disc" / "tree" / "DATA"


def test_table_layout():
    chars = [c for _, c in make_tbl.entries()]
    assert len(chars) == len(set(chars)), "a character appears twice in the font table"
    codes = dict(make_tbl.entries())
    assert codes[0xE0] == "ぁ" and codes[0x123] == "の" and codes[0x1EA] == "「"


def test_decode_known_lines():
    s = textscan.decode(bytes.fromhex("01ea0168016601230105015101010109010b014801e001ebff"), 0)
    assert s == ("「ガオのせんしたちよ。」", 25)


@pytest.mark.skipif(not (TREE / "DS_ST01.PAC").is_file(), reason="disc not dumped (docs/re/disc.md)")
def test_story_table_decodes():
    d = (TREE / "DS_ST01.PAC").read_bytes()
    leaves = {p: (o, s, k) for p, o, s, k in pac.walk(d, 0, len(d))}
    o, size, k = leaves[(13, 12)]
    blob, end = pac.lzs_decode(d, o)
    assert end <= o + size
    t = textscan.table(blob)
    assert t and any(s.startswith("「ちきゅうのいのちを") for s, _ in t[2].values())
