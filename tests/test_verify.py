"""tools/verify.py catches what it claims to: a stray EXE byte, a branch into a replaced span, a non-text leaf
changed, a table that reads back wrong, a disc file that differs from the overlay."""
import shutil
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402
import insert  # noqa: E402
import mkdisc  # noqa: E402
import pac  # noqa: E402
import verify  # noqa: E402

BIN = ROOT / "build" / "gaoranger_en.bin"
need_tree = pytest.mark.skipif(not (mkdisc.TREE / "SLPS_033.53").is_file(), reason="no unpacked disc tree")


@pytest.fixture(scope="module")
def overlay(tmp_path_factory):
    ov = tmp_path_factory.mktemp("ov")
    build.build_exe(ov)
    insert.insert(ov)
    return ov


@need_tree
def test_clean_build_passes(overlay):
    assert verify.check_exe(overlay) == []
    assert verify.check_pacs(overlay, False, {}) == []


@need_tree
def test_stray_exe_byte(overlay, tmp_path):
    shutil.copy(overlay / "SLPS_033.53", tmp_path / "SLPS_033.53")
    exe = bytearray((tmp_path / "SLPS_033.53").read_bytes())
    exe[0x1000] ^= 1
    (tmp_path / "SLPS_033.53").write_bytes(exe)
    assert any("outside" in e for e in verify.check_exe(tmp_path))


@need_tree
def test_branch_into_width_table():
    exe = bytearray((mkdisc.TREE / "SLPS_033.53").read_bytes())
    assert verify.branch_errors(exe) == []
    struct.pack_into("<I", exe, 0x80020000 - verify.EXE_BASE, 3 << 26 | (verify.WTAB[0] + 8) >> 2 & 0x3FFFFFF)
    assert verify.branch_errors(exe)


@need_tree
def test_wrong_text_and_foreign_leaf(overlay, tmp_path):
    assert verify.check_pacs(overlay, False, {"ds01-00a2": "Something else"})  # reads back the real en
    shutil.copytree(overlay, tmp_path / "o")
    f = tmp_path / "o" / "DATA" / "DS_ST01.PAC"
    node = pac.parse(f.read_bytes())
    path = next(p for p, _ in verify.leaves(f.read_bytes()) if p not in ((13, 12), (9, 7)))
    data = dict(verify.leaves(f.read_bytes()))[path]
    node = insert.set_leaf(node, list(path), bytes([data[0] ^ 1]) + data[1:])
    insert.finish(node)
    f.write_bytes(pac.build(node))
    assert any("neither a text table" in e for e in verify.check_pacs(tmp_path / "o", False, {}))


@need_tree
@pytest.mark.skipif(not BIN.is_file(), reason="no build")
def test_disc_differs_from_overlay(tmp_path):
    shutil.copytree(ROOT / "build" / "overlay", tmp_path / "o")
    f = tmp_path / "o" / "DATA" / "DS_ST01.PAC"
    f.write_bytes(f.read_bytes()[:-1] + b"\x01")
    assert any("DS_ST01.PAC" in e for e in verify.check_disc(BIN, tmp_path / "o"))
