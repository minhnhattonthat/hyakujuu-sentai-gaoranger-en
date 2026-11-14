"""lzsmap.py: where the game decodes lzs blocks, from tools/lua/lzslog.lua logs (warp.py --trace --script ...).

For every decode of a text-table block (decoded size = a built table block's size), lists the other decodes and
file loads of the same run whose RAM range overlaps the bytes the table GREW into ([dst + orig size, dst + new size)).
Ranges reused later by another scene are normal; an overlap while the table is still in use is a bug.

    python -X utf8 tools/lzsmap.py DIR..       # DIR = warp output dir with log.txt (or a root of them)
    python -X utf8 tools/lzsmap.py DIR --all   # also print every decode
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract  # noqa: E402
import pac  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LZS = re.compile(r"LZS frame (\d+) src ([0-9a-f]+) dst ([0-9a-f]+) size (\d+) ra ([0-9a-f]+)")


def grown():
    """built decoded size -> (original decoded size, PAC/path) for every lzs block the build changed in size."""
    out = {}
    for b in sorted((ROOT / "build" / "overlay" / "DATA").glob("*.PAC")):
        def sizes(d):
            return {p: len(pac.lzs_decode(d, o)[0]) for p, o, s, k in pac.walk(d, 0, len(d)) if k == "lzs"}
        old, new = sizes((extract.DATA / b.name).read_bytes()), sizes(b.read_bytes())
        for p in old:
            if new[p] != old[p]:
                out.setdefault(new[p], (old[p], f"{b.name}/{'_'.join(map(str, p))}"))
    return out


def scan(log, table, show_all):
    decs = [(int(f), int(s, 16), int(d, 16), int(n), int(r, 16)) for f, s, d, n, r in LZS.findall(log.read_text(
        encoding="utf-8", errors="replace"))]
    print(f"{log.parent.name}: {len(decs)} decodes")
    if show_all:
        for f, s, d, n, r in decs:
            print(f"  frame {f:6d} src {s:08x} dst {d:08x}..{d + n:08x} ra {r:08x}")
    hits = 0
    for i, (f, s, d, n, r) in enumerate(decs):
        if n not in table:
            continue
        old, name = table[n]
        lo, hi = d + old, d + n
        print(f"  {name}? frame {f} dst {d:08x} grew {old} -> {n}: tail {lo:08x}..{hi:08x}")
        for f2, s2, d2, n2, r2 in decs[i + 1:]:
            if d2 < hi and lo < d2 + n2:
                hits += 1
                print(f"    overlap: frame {f2} decode dst {d2:08x}..{d2 + n2:08x} (src {s2:08x})")
    return hits


if __name__ == "__main__":
    table = grown()
    logs = [p for a in sys.argv[1:] if not a.startswith("--") for p in sorted(Path(a).rglob("log.txt"))]
    n = sum(scan(p, table, "--all" in sys.argv) for p in logs)
    print(f"lzsmap: {n} overlaps")
    sys.exit(1 if n else 0)
