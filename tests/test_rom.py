import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_rom  # noqa: E402


@pytest.mark.skipif(not (ROOT / "rom").is_dir() or not any((ROOT / "rom").glob("*.bin")), reason="no ROM")
def test_rom_sha1():
    check_rom.check()
