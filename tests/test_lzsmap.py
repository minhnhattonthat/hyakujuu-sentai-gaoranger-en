"""tools/lzsmap.py: an overlap only counts on the grown tail alone; a scene must decode its expected table."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import lzsmap  # noqa: E402

HEAD, OTHER = "11" * 16, "22" * 16
TABLE = {HEAD: ("ds01", 0x100, 0x180), OTHER: ("x", 0x40, 0x40)}


def run(tmp_path, scene, *decs):
    d = tmp_path / scene
    d.mkdir()
    (d / "log.txt").write_text("".join(f"LZS frame {i} src 0 dst {dst:08x} size {n} ra 0 head {h}\n"
                                       for i, (dst, n, h) in enumerate(decs)))
    return lzsmap.scan(d / "log.txt", TABLE, False)


def test_tail_only_overlap_counts(tmp_path):
    hits, probs = run(tmp_path, "ds01", (0x1000, 0x180, HEAD), (0x1140, 0x40, OTHER))
    assert (hits, probs) == (1, [])


def test_reuse_over_original_bytes_is_fine(tmp_path):
    hits, _ = run(tmp_path, "ds01", (0x1000, 0x180, HEAD), (0x1000, 0x400, OTHER))
    assert hits == 0


def test_expected_table_missing(tmp_path):
    hits, probs = run(tmp_path, "ds01", (0x1000, 0x40, OTHER))
    assert hits == 0 and probs == ["ds01: expected table ds01 was never decoded"]
