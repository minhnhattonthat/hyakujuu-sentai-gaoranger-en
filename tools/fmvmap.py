"""Which scene plays which FMV, from warp.py --trace logs (CD seeks into XA/*.STR extents; docs/re/fmv.md).

    python -X utf8 tools/fmvmap.py work/qa/fmvmap      # after: warp.py --all --trace --out work/qa/fmvmap
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def extents():
    out = []
    for line in (ROOT / "work" / "disc" / "lba.txt").read_text().splitlines():
        lba, size, name = line.split()
        if name.endswith(".STR"):
            out.append((int(lba), int(lba) + (int(size) + 2047) // 2048, name))
    return out


def main(d):
    ext = extents()
    for log in sorted(Path(d).glob("*/log.txt")):
        hits = {}
        for m in re.finditer(r"CD \w+ frame (\d+) lba (\d+)", log.read_text(errors="replace")):
            f, lba = int(m[1]), int(m[2])
            for lo, hi, name in ext:
                if lo <= lba < hi:
                    hits.setdefault(name, f)
        if hits:
            print(log.parent.name, " ".join(f"{n}@f{f}" for n, f in sorted(hits.items(), key=lambda x: x[1])))


if __name__ == "__main__":
    main(sys.argv[1])
