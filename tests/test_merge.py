"""tools/merge.py refuses bad input before writing any script file."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import merge  # noqa: E402


def snapshot():
    return {p: p.read_bytes() for p in (ROOT / "script").glob("*.json")}


def test_unknown_id_writes_nothing():
    before = snapshot()
    with pytest.raises(SystemExit):
        merge.merge({"ds01-002e": "x", "nope-0000": "y"}, force=True)
    assert snapshot() == before


def test_set_en_needs_force():
    with pytest.raises(SystemExit):
        merge.merge({"ds01-00a2": "changed"})


def test_tsv_rejects_escapes(tmp_path):
    f = tmp_path / "x.tsv"
    f.write_text("ds01-00a2\tbad\\n\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        merge.read_tsv(f)
