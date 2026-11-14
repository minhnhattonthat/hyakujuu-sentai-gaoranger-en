"""Intersect tools/lua/memfree.lua reports: RAM ranges and VRAM tiles free in every run (subtitle engine home).

    python -X utf8 tools/memfree.py work/qa/memfree [--min 2048]
"""
import argparse
import re
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--min", type=lambda s: int(s, 0), default=2048, help="smallest RAM run to print")
    a = ap.parse_args()
    ram, vram, runs = None, None, 0
    for f in sorted(Path(a.dir).rglob("memfree.txt")):
        runs += 1
        r, v = set(), set()
        for line in f.read_text().splitlines():
            m = re.match(r"RAM free ([0-9a-f]+)-([0-9a-f]+)", line)
            if m:
                r.update(range(int(m[1], 16) >> 8, int(m[2], 16) >> 8))
            m = re.match(r"VRAM free (\d+) (\d+) (\d+) 16", line)
            if m:
                x, y, w = map(int, m.groups())
                v.update((t, y // 16) for t in range(x // 16, (x + w) // 16))
        ram = r if ram is None else ram & r
        vram = v if vram is None else vram & v
    print(f"{runs} runs")
    s = None
    for b in range(0x800000 >> 8, (0x80200000 >> 8) + 1):
        if b in ram and s is None:
            s = b
        if b not in ram and s is not None:
            if (b - s) << 8 >= a.min:
                print(f"RAM  {s << 8:08x}-{b << 8:08x} {(b - s) << 8:6d}")
            s = None
    for ty in range(32):
        row = [tx for tx in range(64) if (tx, ty) in vram]
        if row:
            spans, st = [], row[0]
            for p, q in zip(row, row[1:] + [None]):
                if q != p + 1:
                    spans.append(f"x {st * 16}-{(p + 1) * 16}")
                    st = q
            print(f"VRAM y {ty * 16}-{ty * 16 + 16}: {', '.join(spans)}")


if __name__ == "__main__":
    main()
