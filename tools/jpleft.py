"""jpleft.py: Japanese text still in a build. The text sits in lzs-compressed PAC leaves, so the skill's jp_left.py
(raw image scan) can't see it; this reads each string table back out of the built PACs instead.

For every table leaf (script/*.json "files") in BUILD_OVERLAY/DATA (or the original PAC when the build didn't touch
it), a string still holding its original Japanese bytes is reported unless its id is in script/keep_jp.txt.
Also scans every leaf of every built PAC for string tables the extractor doesn't know (textscan).

    python -X utf8 tools/jpleft.py [build/overlay]     # exit 1 if anything is left
"""
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import extract  # noqa: E402
import insert  # noqa: E402
import pac  # noqa: E402
import textscan  # noqa: E402


def scan(overlay):
    keep = {ln.split()[0] for ln in (ROOT / "script" / "keep_jp.txt").read_text(encoding="utf-8").splitlines()
            if ln.strip()} if (ROOT / "script" / "keep_jp.txt").exists() else set()
    left, known = [], set()
    for p in sorted((ROOT / "script").glob("*.json")):
        t = json.loads(p.read_text(encoding="utf-8"))
        for f in t["files"]:
            name, leaf = f.split("/")
            known.add(f)
            built = Path(overlay) / "DATA" / name
            d = insert.leaf_of((built if built.exists() else extract.DATA / name).read_bytes(), leaf)
            n = struct.unpack_from("<H", d, 2)[0]
            offs = struct.unpack_from(f"<{n}H", d, 4)
            for s in t["strings"]:
                if not s["slots"] or not insert.JP_TEXT.search(s["jp"]) or s["id"] in keep:
                    continue
                jp = extract.TBL.encode(s["jp"] + "{end}")
                o = offs[s["slots"][0]]
                if d[o:o + len(jp)] == jp:
                    left.append(f"{f} {s['id']}: {s['jp']}")
    unknown = []
    for built in sorted((Path(overlay) / "DATA").glob("*.PAC")):
        d = built.read_bytes()
        for path, off, size, k in pac.walk(d, 0, len(d)):
            if k == "add" or not path:
                continue
            blob = pac.lzs_decode(d, off)[0] if k == "lzs" else d[off:off + size]
            if textscan.table(blob) and f"{built.name}/{'_'.join(map(str, path))}" not in known:
                unknown.append(f"{built.name}/{'_'.join(map(str, path))}")
    return left, unknown


if __name__ == "__main__":
    left, unknown = scan(sys.argv[1] if len(sys.argv) > 1 else ROOT / "build" / "overlay")
    for x in left:
        print("JP", x)
    for x in unknown:
        print("UNKNOWN TABLE", x)
    print(f"jpleft: {len(left)} Japanese strings left, {len(unknown)} unknown tables")
    sys.exit(1 if left or unknown else 0)
