"""lint.py: text lint over script/*.json `en` fields (check.py runs it).

Per translated string: encodes through tbl/en.tbl, no Japanese left, control codes other than {n} the same as the
jp (same order), lines <= the box's line budget, each line's pixel width (font.line_px) <= the box's budget, no
ordinal suffix glued to a number, no stub last line. Budgets per table: BUDGETS (measured in game, docs/re/text.md
§Box budgets); a table with no measured budget is reported, not passed.

    python -X utf8 tools/lint.py [--untranslated]   # exit 1 on any error; --untranslated also fails on empty en
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import font  # noqa: E402
from tbl import Table  # noqa: E402

# table -> (lines, px per line, proof). lines "jp": max(2, the jp's line count); the box opens with 3 rows for a
# 3-line message (story box layout 1) and 2 rows otherwise. Missing table = not measured yet.
BUDGETS = {
    **{f"ds0{i}": (2, 232, "work/qa/width/w1,w2") for i in range(1, 8)},
    **{t: ("jp", 232, "work/qa/mk/saveunf, tcont, option: same box, x 38") for t in ("save", "load", "option")},
}
JP = re.compile(r"[぀-ヿ一-鿿]")
CTRL = re.compile(r"\{(?!n\})[^}]*\}")
KEEP = ROOT / "script" / "keep_jp.txt"  # ids that stay Japanese on purpose: "<id> <reason>" per line


def lint(untranslated=False):
    en = Table.load(ROOT / "tbl" / "en.tbl")
    keep = {ln.split()[0] for ln in KEEP.read_text(encoding="utf-8").splitlines() if ln.strip()} \
        if KEEP.exists() else set()
    errors, todo, nobudget = [], 0, set()
    for p in sorted((ROOT / "script").glob("*.json")):
        t = json.loads(p.read_text(encoding="utf-8"))
        budget = BUDGETS.get(p.stem)
        for s in t["strings"]:
            sid, jp, txt = s["id"], s["jp"], s.get("en", "")
            if not txt:
                if JP.search(jp) and sid not in keep:
                    todo += 1
                    if untranslated:
                        errors.append(f"{sid}: no en")
                continue
            try:
                en.encode(txt + "{end}")
            except Exception as e:  # noqa: BLE001
                errors.append(f"{sid}: not encodable ({e})")
            if JP.search(txt):
                errors.append(f"{sid}: Japanese in en")
            if CTRL.findall(txt) != CTRL.findall(jp):
                errors.append(f"{sid}: control codes {CTRL.findall(txt)} != jp {CTRL.findall(jp)}")
            if re.search(r"\d(st|nd|rd|th)\b", txt):
                errors.append(f"{sid}: ordinal suffix after a number")
            lines = txt.split("{n}")
            if len(lines) > 1 and len(font.re_ctrl.sub("", lines[-1]).strip()) < 6:
                errors.append(f"{sid}: stub last line {lines[-1]!r}")
            if txt != txt.strip() and jp == jp.strip():
                errors.append(f"{sid}: leading/trailing blanks the jp doesn't have")
            if budget is None:
                nobudget.add(p.stem)
                continue
            nl, px, _ = budget
            if nl == "jp":
                nl = max(2, len(jp.split("{n}")))
            if len(lines) > nl:
                errors.append(f"{sid}: {len(lines)} lines > {nl}")
            for i, ln in enumerate(lines):
                w = font.line_px(ln)
                if w > px:
                    errors.append(f"{sid}: line {i + 1} is {w} px > {px}: {ln!r}")
    return errors, todo, nobudget


if __name__ == "__main__":
    errs, todo, nob = lint("--untranslated" in sys.argv)
    for e in errs:
        print(e)
    print(f"lint: {len(errs)} errors, {todo} strings untranslated"
          + (f", no measured budget for {sorted(nob)}" if nob else ""))
    sys.exit(1 if errs or nob else 0)
