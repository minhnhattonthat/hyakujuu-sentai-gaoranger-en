"""Phase 4: script/*.json rebuild every string table byte-exact (roundtrip) and no text lies outside them (coverage)."""
import glob
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import extract  # noqa: E402
import runscan  # noqa: E402
import textscan  # noqa: E402

PAC = ROOT / "work" / "pac"
need_disc = pytest.mark.skipif(not (extract.DATA / "DS_ST01.PAC").is_file(), reason="disc not dumped (docs/re/disc.md)")
need_pac = pytest.mark.skipif(not PAC.is_dir(), reason="run tools/unpack_all.py (AGENTS.md)")


def scripts():
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "script").glob("*.json"))}


def test_script_files_match_table_list():
    s = scripts()
    assert set(s) == set(extract.TABLES)
    for name, t in s.items():
        assert t["files"] == extract.TABLES[name]
        ids = [x["id"] for x in t["strings"]]
        assert len(ids) == len(set(ids))


def test_jp_encodes_through_table():
    for t in scripts().values():
        for x in t["strings"]:
            assert extract.TBL.decode(extract.TBL.encode(x["jp"] + "{end}"))[0] == x["jp"] + "{end}", x["id"]
            assert "[" not in x["jp"], f"{x['id']}: unknown byte in {x['jp']!r}"


@need_disc
def test_roundtrip_original_bytes():
    """Rebuilding each table from its jp fields gives the original leaf, in every file that holds it."""
    for name, t in scripts().items():
        for f in t["files"]:
            assert extract.build(t) == extract.leaf(f), f"{name}: {f}"


def test_build_keeps_alignment_and_slots():
    t = {"a": 0, "count": 3, "lead": 0, "end_slots": [2], "strings": [
        {"slots": [0], "jp": "ガオ", "en": "GAO", "pad": 2}, {"slots": [1], "jp": "あ", "en": "", "pad": 1}]}
    b = extract.build(t, "en")  # "GAO" = 6 bytes + FF, + pad 2 = odd: must be evened up
    back = extract.parse(b)
    assert [s["slots"] for s in back["strings"]] == [[0], [1]] and back["end_slots"] == [2]
    assert extract.TBL.decode(b, 10)[0] == "GAO{end}" and len(b) % 2 == 0
    assert all(o % 2 == 0 for o in __import__("struct").unpack_from("<3H", b, 4))


@need_pac
def test_coverage_every_table_listed():
    """textscan finds a table in exactly the leaves extract.TABLES lists (none missed, none extra)."""
    found = set()
    for f in glob.glob(str(PAC / "**" / "*.bin"), recursive=True):
        if textscan.table(Path(f).read_bytes()):
            p = Path(f)
            found.add(f"{p.parent.name}/{p.stem}")
    assert found == {f for files in extract.TABLES.values() for f in files}


@need_pac
def test_coverage_no_text_outside_tables():
    """Grammar sweep of every non-table leaf, the EXE and the PRGs: only pixel-data noise (runs of 1-3 kinds)."""
    files = glob.glob(str(PAC / "**" / "*.bin"), recursive=True)
    files += [str(extract.DATA.parent / "SLPS_033.53")] + glob.glob(str(extract.DATA / "*.PRG"))
    hits = []
    for f in files:
        d = Path(f).read_bytes()
        if textscan.table(d):
            continue
        hits += [(f, p, s) for p, s, _ in runscan.runs(d, 6) if len(set(s)) >= 4]
    assert not hits
