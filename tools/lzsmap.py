"""lzsmap.py: where the game decodes the grown text tables, from tools/lua/lzslog.lua logs.

    python -X utf8 tools/debug/warp.py $(python tools/lzsmap.py --scenes) --cue build/gaoranger_en.cue \
        --out DIR --trace --script tools/lua/lzslog.lua --jobs 4   # the regression set, ~25 min (docs/re/pac.md)
    python -X utf8 tools/lzsmap.py DIR..         # DIR = a warp output dir with log.txt, or a root of them
    python -X utf8 tools/lzsmap.py DIR --all     # also print every decode

A decode is named by its first 16 stream bytes (lzslog's `head`) against every lzs block of the built disc
(build/overlay, else the original PAC), so copies of one table in several PACs get the table's name (script/*.json).
For each decode of a table the build grew, lists every later decode of the same run whose RAM range overlaps the
bytes the table grew into ([dst + orig size, dst + new size)) but not the table's original bytes (a decode over
both would overwrite the table in the original game too, so the table is no longer in use: the next scene).
Fails (exit 1) on such an overlap, on a scene in EXPECT whose run never decodes its table, and on a log without
heads (re-trace with the current lzslog.lua).
The card table (Y_TITLE/21, CARDMS/0) is decoded by no scene: docs/re/pac.md §Decode targets, tools/slotcalls.py.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract  # noqa: E402
import pac  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LZS = re.compile(r"LZS frame (\d+) src ([0-9a-f]+) dst ([0-9a-f]+) size (\d+) ra ([0-9a-f]+)(?: head ([0-9a-f]+))?")
# scene (tools/debug/scenes.txt) -> grown table its run must decode
EXPECT = {**{f"ds0{i}": f"ds0{i}" for i in range(1, 8)},
          **{s: "save" for s in ("de01", "de02", "de03s", "de04s", "de05s", "edsave", "save", "savedone",
                                 "saveover", "saveunf")},
          **{s: "load" for s in ("tcont", "tload", "tcontdata", "tload2")},
          **{s: "option" for s in ("option", "tsound", "tvib")}}
# EXPECT + scenes traced for the card table (none decodes it) or that stop before any table text (load: the graphic
# yes/no prompt; de03-05: the ending's last picture)
TRACE_SCENES = sorted(EXPECT) + ["de03", "de04", "de05", "load", "ofight", "ofmenu", "title", "tnew", "ytitle"]


def heads():
    """stream head hex -> (table or 'PAC/path', original decoded size, built decoded size), every lzs block on the
    built disc. A head shared by two different blocks is an error (it couldn't name a decode)."""
    tables = {}
    for p in sorted((ROOT / "script").glob("*.json")):
        for f in json.loads(p.read_text(encoding="utf-8"))["files"]:
            tables[f] = p.stem
    out = {}
    for orig in sorted(extract.DATA.glob("*.PAC")):
        built = ROOT / "build" / "overlay" / "DATA" / orig.name
        o, b = orig.read_bytes(), (built if built.is_file() else orig).read_bytes()
        osz = {p: pac.lzs_header(o, off)["usize"] for p, off, s, k in pac.walk(o, 0, len(o)) if k == "lzs"}
        for p, off, s, k in pac.walk(b, 0, len(b)):
            if k != "lzs":
                continue
            h = pac.lzs_header(b, off)
            leaf = f"{orig.name}/{'_'.join(map(str, p))}"
            ent = (tables.get(leaf, leaf), osz[p], h["usize"])
            key = b[h["data"]:h["data"] + 16].hex()
            if key in out and out[key] != ent and out[key][0] != ent[0]:
                # same bytes, different block: only harmless if neither grew
                if ent[1] != ent[2] or out[key][1] != out[key][2]:
                    raise SystemExit(f"lzsmap: head {key} is shared by {out[key][0]} and {leaf}")
                continue
            out[key] = ent
    return out


def scan(log, table, show_all):
    """-> (overlaps, problems) for one run's log."""
    scene = log.parent.name
    decs = [(int(f), int(s, 16), int(d, 16), int(n), int(r, 16), h) for f, s, d, n, r, h in LZS.findall(
        log.read_text(encoding="utf-8", errors="replace"))]
    problems = []
    if any(not h for *_, h in decs):
        problems.append(f"{scene}: log has no stream heads (old lzslog.lua): re-trace")
    print(f"{scene}: {len(decs)} decodes")
    seen = set()
    hits = 0
    for i, (f, s, d, n, r, h) in enumerate(decs):
        name, old, new = table.get(h, ("?", n, n))
        if show_all:
            print(f"  frame {f:6d} src {s:08x} dst {d:08x}..{d + n:08x} ra {r:08x} {name}")
        seen.add(name)
        if new == old:
            continue
        lo, hi = d + old, d + n
        print(f"  {name} frame {f} dst {d:08x} grew {old} -> {n}: tail {lo:08x}..{hi:08x}")
        for f2, s2, d2, n2, r2, h2 in decs[i + 1:]:
            # a decode that also covers the table's original bytes overwrites it in the original game too (the
            # next scene reusing the heap): the table is dead by then. Only a hit on the grown tail alone is new.
            if d2 < hi and lo < d2 + n2 and not (d2 < lo and d < d2 + n2):
                hits += 1
                print(f"    overlap: frame {f2} decode dst {d2:08x}..{d2 + n2:08x} ({table.get(h2, ('?',))[0]})")
    want = EXPECT.get(scene)
    if want and want not in seen:
        problems.append(f"{scene}: expected table {want} was never decoded")
    elif not want:
        print(f"  (no expected table for {scene})")
    return hits, problems


if __name__ == "__main__":
    if "--scenes" in sys.argv:
        sys.exit(print(" ".join(TRACE_SCENES)))
    table = heads()
    logs = [p for a in sys.argv[1:] if not a.startswith("--") for p in sorted(Path(a).rglob("log.txt"))]
    hits, problems = 0, []
    for p in logs:
        h, pr = scan(p, table, "--all" in sys.argv)
        hits, problems = hits + h, problems + pr
    for x in problems:
        print("PROBLEM", x)
    print(f"lzsmap: {len(logs)} runs, {hits} overlaps, {len(problems)} problems")
    sys.exit(1 if hits or problems or not logs else 0)
