"""build.py: build the patched disc -> build/gaoranger_en.bin/.cue.

Checks the dump (rom.sha1), unpacks the disc tree if missing, writes every changed file into build/overlay/
(same paths as work/disc/tree; nothing yet: text and graphics insertion come in later phases), then builds the
image with mkdisc.py. With an empty overlay the .bin is byte-identical to the original (tests/test_disc.py).

    python -X utf8 tools/build.py [--out build/gaoranger_en.bin]
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_rom  # noqa: E402
import mkdisc  # noqa: E402

ROOT = mkdisc.ROOT
CUE = ROOT / "rom" / "Hyakujuu Sentai GaoRanger (Japan).cue"
DUMPSXISO = ROOT / "tools" / "mkpsxiso" / "mkpsxiso-2.30-win64" / "dumpsxiso.exe"


def ensure_tree():
    if (mkdisc.TREE / "SLPS_033.53").is_file():
        return
    out = mkdisc.TREE.parent
    r = subprocess.run([str(DUMPSXISO), "-q", "-x", str(mkdisc.TREE), "-s", str(out / "layout.xml"), str(CUE)])
    if r.returncode or not (mkdisc.TREE / "SLPS_033.53").is_file():
        sys.exit("dumpsxiso failed: see docs/re/disc.md")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "build" / "gaoranger_en.bin"))
    a = ap.parse_args()
    check_rom.check()
    ensure_tree()
    overlay = ROOT / "build" / "overlay"
    shutil.rmtree(overlay, ignore_errors=True)
    overlay.mkdir(parents=True)
    out = mkdisc.build(a.out, overlay)
    print(out.with_suffix(".cue"))


if __name__ == "__main__":
    main()
