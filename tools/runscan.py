"""runscan.py: grammar sweep for GaoRanger strings anywhere (not only in tables): >= MIN glyphs ending in FF,
with at least one kana. Finds text outside textscan.py's tables (embedded records, code-built strings).
    python -X utf8 tools/runscan.py [--min 4] [--skip-tables] [FILES..]"""
import glob
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import textscan  # noqa: E402

KANA = re.compile(r"[ぁ-ヿ]")


def runs(d, mn):
    p = 0
    while p < len(d) - 1:
        if d[p] in (0, 1) and ((d[p] << 8) | d[p + 1]) in textscan.CH:
            s = textscan.decode(d, p)
            if s and len(s[0]) >= mn and len(KANA.findall(s[0])) >= 2:
                yield p, s[0], s[1]
                p = s[1]
                continue
        p += 1


def main():
    args = sys.argv[1:]
    mn = int(args[args.index("--min") + 1]) if "--min" in args else 4
    skip = "--skip-tables" in args
    files = [a for a in args if a.endswith(".bin")] or sorted(glob.glob("work/pac/**/*.bin", recursive=True))
    for f in files:
        d = open(f, "rb").read()
        if skip and textscan.table(d):
            continue
        for p, s, e in runs(d, mn):
            print(f"{f} {p:06x} {s.replace(chr(10), '/')}")


if __name__ == "__main__":
    main()
