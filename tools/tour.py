"""QA tour (phase 8): every warp scene on a build, with the text-coverage probe, then one changed-frames contact sheet
per scene for visual QA and the qa_gate manifest.

    python -X utf8 tools/tour.py [--cue build/gaoranger_en.cue] [--out work/qa/tour] [--jobs 4] [SCENE ..]

Text scenes (story, endings, menus, card flows) are shot every 30 frames: mashing advances a box every 60. The rest
every 150. Each scene dir gets qa_sheet*.png (sheet.py --changed); the manifest is OUT/manifest.tsv, verdicts go in
OUT/verdicts (qa_gate.py; the release guard reads the verdicts dir beside each manifest). Coverage: python -X utf8 tools/textcov.py OUT --waive script/text_unshown.tsv
"""
import argparse
import glob
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tools", "debug"))
from skill import SKILL  # noqa: E402
from warp import load_scenes  # noqa: E402

SLOW = ("a", "e", "b")  # action, extra, robo scenes: HUD graphics only, shots every 150 (ba/bb/b*, a*, ex*)
LONG = {"de07", "overb", "ofight", "ademo", "ytitle"}


def text_scene(name):
    return name not in LONG and not (name[0] in SLOW and name[:2] not in ("de", "ed"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenes", nargs="*")
    ap.add_argument("--cue", default=os.path.join(ROOT, "build", "gaoranger_en.cue"))
    ap.add_argument("--out", default=os.path.join(ROOT, "work", "qa", "tour"))
    ap.add_argument("--jobs", default="4")
    ap.add_argument("--sheets-only", action="store_true", help="redo the sheets and manifest from the last run")
    a = ap.parse_args()
    names = a.scenes or list(load_scenes())
    warp = [sys.executable, "-X", "utf8", os.path.join(ROOT, "tools", "debug", "warp.py"), "--cue", a.cue,
            "--out", a.out, "--jobs", a.jobs, "--script", os.path.join(ROOT, "tools", "lua", "textptr.lua"),
            "--var", "HOLD=0"]
    rc = 0
    for every, group in (("30", [n for n in names if text_scene(n)]), ("150", [n for n in names if not text_scene(n)])):
        if group and not a.sheets_only:
            rc |= subprocess.call(warp + ["--shot-every", every] + group)
    for n in names:
        d = os.path.join(a.out, n)
        if os.path.isdir(d):
            for old in glob.glob(os.path.join(d, "qa_sheet*.png")):
                os.remove(old)
            # stages and robo battles move every frame: only big changes, smaller tiles (HUD graphics only)
            opts = ["--changed", "0.05", "--max", "24", "--cols", "6"] if text_scene(n) else \
                ["--changed", "0.5", "--max", "24", "--cols", "6", "--div", "3"]
            subprocess.call([sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "sheet.py"), d, *opts,
                             "--out", os.path.join(d, "qa_sheet.png")], stdout=subprocess.DEVNULL)
    subprocess.call([sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "qa_gate.py"), "init",
                     os.path.join(a.out, "manifest.tsv"), a.out, "--glob", "qa_sheet*.png", "--build",
                     a.cue[:-4] + ".bin"])
    sys.exit(rc)


if __name__ == "__main__":
    main()
