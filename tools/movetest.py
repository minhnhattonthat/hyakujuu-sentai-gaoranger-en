"""movetest.py: a disc where every PAC is repacked with every lzs block re-encoded by pac.lzs_encode.

Sizes change, so every PAC after the first grows or shrinks and moves; warping scenes on this build proves the game
finds moved/resized files by name and decodes our compressor's output (docs/re/disc.md §Rebuild).

    python -X utf8 tools/movetest.py [--out work/movetest/gao.bin]
then: python -X utf8 tools/debug/warp.py --all --cue work/movetest/gao.cue
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mkdisc  # noqa: E402
import pac  # noqa: E402


def recompress(node):
    if node["kind"] == "lzs":
        node["payload"] = pac.lzs_decode(node["raw"], 0)[0]
    elif node["kind"] == "add":
        for c in node["slots"].values():
            recompress(c)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(mkdisc.ROOT / "work" / "movetest" / "gao.bin"))
    a = ap.parse_args()
    overlay = Path(a.out).resolve().parent / "overlay" / "DATA"
    overlay.mkdir(parents=True, exist_ok=True)
    moved = 0
    for f in sorted((mkdisc.TREE / "DATA").glob("*.PAC")):
        d = f.read_bytes()
        node = pac.parse(d)
        recompress(node)
        b = pac.build(node)
        assert pac.build(pac.parse(b)) == b
        (overlay / f.name).write_bytes(b)
        moved += (len(b) + 2047) // 2048 != (len(d) + 2047) // 2048
        print(f"{f.name:14s} {len(d):8d} -> {len(b):8d}")
    print(f"{moved} PACs changed sector count")
    print(mkdisc.build(a.out, overlay.parent))


if __name__ == "__main__":
    main()
