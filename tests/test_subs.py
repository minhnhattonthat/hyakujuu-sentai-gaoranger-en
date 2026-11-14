"""In-game voice subtitles (tools/subs.py, asm/subs.asm): sector maps, wrap/lint, and every script/subs.tsv CDXA row fits."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import subs  # noqa: E402

need_xa = pytest.mark.skipif(not (subs.XA / "CDXA00.XA").is_file(), reason="disc not dumped (docs/re/disc.md)")


@need_xa
def test_selftest():
    subs.selftest()


def test_rows_fit():
    assert subs.lint() == []


@need_xa
def test_mid_channel_rows_start_late():
    """A row starting mid-channel begins 2 sectors late (no flash at the previous clip's end); a row at 0 doesn't."""
    secs = subs.channel_sectors(0)[2]
    (_, _, a0, *_), (_, _, a1, *_) = subs.table([(0, 2, 0.0, 1.0, "", "x"), (0, 2, 22.0, 23.0, "", "x")])
    assert a0 == secs[0]
    assert a1 == secs[int(22.0 / subs.SECTOR_S) + 2]
