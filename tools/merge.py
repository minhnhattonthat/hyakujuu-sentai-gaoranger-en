"""merge.py: set script/*.json `en` fields from a TSV of `id<TAB>en` lines (translator output, polish fixes).

Refuses unknown or duplicate ids and literal tabs/escapes; writes the JSON the way extract.py does. Run lint after.

    python -X utf8 tools/merge.py work/tl/out.tsv [--force]   # --force: overwrite an en that is already set
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_tsv(path):
    rows = {}
    for n, ln in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not ln.strip() or ln.startswith("#"):
            continue
        sid, sep, en = ln.partition("\t")
        if not sep or "\t" in en or "\\" in en:
            sys.exit(f"{path}:{n}: want id<TAB>en, no tabs or backslashes in en")
        if sid in rows:
            sys.exit(f"{path}:{n}: duplicate id {sid}")
        rows[sid] = en
    return rows


def merge(rows, force=False):
    tables = {p: json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "script").glob("*.json"))}
    known = {s["id"]: s for t in tables.values() for s in t["strings"]}
    if set(rows) - set(known):
        sys.exit(f"unknown ids: {sorted(set(rows) - set(known))}")
    for sid, en in rows.items():
        if known[sid].get("en") and known[sid]["en"] != en and not force:
            sys.exit(f"{sid}: en already set ({known[sid]['en']!r}); --force to overwrite")
    for p, t in tables.items():  # all checks passed: write only tables that change
        if any(s["id"] in rows for s in t["strings"]):
            for s in t["strings"]:
                s["en"] = rows.get(s["id"], s.get("en", ""))
            p.write_text(json.dumps(t, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return len(rows)


if __name__ == "__main__":
    print(f"merged {merge(read_tsv(sys.argv[1]), '--force' in sys.argv)} strings")
