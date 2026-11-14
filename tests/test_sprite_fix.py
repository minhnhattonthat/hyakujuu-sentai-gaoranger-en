import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "gfx"))
import edits  # noqa: E402
import gfx_edit  # noqa: E402


def group(recs, clut):
    return struct.pack("<H", len(recs)) + b"".join(gfx_edit.SPR.pack(*r, clut) for r in recs)


def test_sprite_fix_rewrites_matching_groups_keeps_clut():
    old, new = edits.SPRITE_FIXES[0]
    other = group([(1, 2, 3, 4, 5, 6, 0x200f)], 0x3c53)
    data = other + group(old, 0x3c53) + b"\0\0" + group(old, 0x3c93)
    got, n = gfx_edit.sprite_fix(data, edits.SPRITE_FIXES)
    assert n == 2
    assert got == other + group(new, 0x3c53) + b"\0\0" + group(new, 0x3c93)


def test_sprite_fix_needs_every_record():
    old, _ = edits.SPRITE_FIXES[0]
    near = group([old[0], old[1][:2] + (0,) + old[1][3:]], 0x3c53)  # second sprite differs
    assert gfx_edit.sprite_fix(near, edits.SPRITE_FIXES) == (near, 0)
