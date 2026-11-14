"""textcov.py: which strings a warp/tour run put in a text window (tools/lua/textptr.lua logs).

Each TEXTPTR line holds the RAM around a window's text pointer; a string counts as shown when its encoded bytes (as
the build wrote them: marker text with --marker, else en, else jp) sit in that RAM with the pointer inside them.
Identical strings in several tables all count. Strings with no slot (unreferenced) are skipped.

    python -X utf8 tools/textcov.py LOGDIR [--marker] [--waive script/text_unshown.tsv]   # exit 1 if any unshown
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import extract  # noqa: E402
import insert  # noqa: E402
from tbl import Table  # noqa: E402

LINE = re.compile(r"TEXTPTR f(\d+) w(\d) ([0-9a-f]{8}) ([0-9a-f]+)")


def encoded(marker):
    en = Table.load(ROOT / "tbl" / "en.tbl")
    out = {}
    for p in sorted((ROOT / "script").glob("*.json")):
        for s in json.loads(p.read_text(encoding="utf-8"))["strings"]:
            if not s["slots"]:
                continue
            txt = insert.marker(s) if marker and insert.JP_TEXT.search(s["jp"]) else s.get("en")
            out[s["id"]] = en.encode(txt + "{end}") if txt else extract.TBL.encode(s["jp"] + "{end}")
    return out


def shown(logdir, enc):
    seen = {}
    for log in Path(logdir).rglob("log.txt"):
        for m in LINE.finditer(log.read_text(encoding="utf-8", errors="replace")):
            ram = bytes.fromhex(m[4])
            mid = len(ram) // 2
            for sid, b in enc.items():
                if sid in seen:
                    continue
                # the logged RAM holds 400 bytes on each side of the pointer: the whole string must be there with
                # the pointer inside it or on its FF (a pressed button jumps the pointer to the end). Whole string,
                # not a head or tail: marker strings share their tails and table defaults share heads.
                i = ram.find(b)
                while i >= 0 and sid not in seen:
                    if i <= mid < i + len(b):
                        seen[sid] = f"{log.parent.name} f{m[1]}"
                    i = ram.find(b, i + 1)
    return seen


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("logdir")
    ap.add_argument("--marker", action="store_true")
    ap.add_argument("--waive")
    a = ap.parse_args()
    enc = encoded(a.marker)
    seen = shown(a.logdir, enc)
    waive = {}
    if a.waive and Path(a.waive).exists():
        for ln in Path(a.waive).read_text(encoding="utf-8").splitlines():
            if "\t" in ln and ln.split("\t", 1)[1].strip():
                waive[ln.split("\t")[0]] = ln.split("\t", 1)[1]
    missing = [s for s in enc if s not in seen and s not in waive]
    for s in missing:
        print("UNSHOWN", s)
    print(f"textcov: {len(seen)} of {len(enc)} strings shown, {len(missing)} unshown (not waived)")
    sys.exit(1 if missing else 0)
