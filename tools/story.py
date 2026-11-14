"""Story pass (references/translation.md §Review): one chapter file per story script, codex as the reviewer.

    python -X utf8 tools/story.py            # write work/qa/story/chapters/*.txt + qa_gate init
    python -X utf8 tools/story.py --review   # also run codex exec -s read-only on every chapter lacking a verdict

Chapters: ds01-07 (Tetomu's briefings), plus `menus` (her save/load/option lines and the card table) so her voice is
read across every screen. Reports -> work/qa/story/reports/<ch>.md, Assessment word -> verdicts/r<NN>_<ch>.tsv.
Orca workers can't start subagents, so codex is the independent reviewer (D15-style worker call).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from skill import SKILL  # noqa: E402

STORY = os.path.join(ROOT, "work", "qa", "story")
CHAPTERS = {f"ds0{n}": [f"ds0{n}"] for n in range(1, 8)}
CHAPTERS["menus"] = ["save", "load", "option", "card"]
SPEAKER = {"card": "System"}  # everything else is Tetomu (glossary)

PROMPT = """You are a read-only story reviewer for an English fan translation of a Japanese PS1 game. Follow
{skill}/assets/story-reviewer-brief.md exactly (read it first). Inputs: chapter file {chapter}, docs/synopsis.md,
docs/style-reference.md, glossary.md. Box budget: 232 px (about 40 characters) a line; story
boxes 2 lines, save/load/option boxes 3 lines where the Japanese has 3 (tools/lint.py enforces both).
Your FINAL message is the report in the brief's format, ending with the `### Assessment` section whose first word
is ok or issue."""


def write_chapters():
    os.makedirs(os.path.join(STORY, "chapters"), exist_ok=True)
    keep = set(open(os.path.join(ROOT, "script", "keep_jp.txt"), encoding="utf-8").read().split())
    for ch, files in CHAPTERS.items():
        out = []
        for f in files:
            d = json.load(open(os.path.join(ROOT, "script", f + ".json"), encoding="utf-8"))
            for s in d["strings"]:
                if s["id"] in keep:
                    continue
                out += [f">> {s['id']} | {SPEAKER.get(f, 'Tetomu')} | {s['jp']}", s["en"], ""]
        with open(os.path.join(STORY, "chapters", ch + ".txt"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(out))
    gate("init", os.path.join(STORY, "chapters"), "--glob", "*.txt")


def gate(cmd, *args):
    return subprocess.run([sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "qa_gate.py"), cmd,
                           os.path.join(STORY, "manifest.tsv"), *args], capture_output=True, text=True,
                          encoding="utf-8")


def review():
    verdicts = os.path.join(STORY, "verdicts")
    reports = os.path.join(STORY, "reports")
    os.makedirs(verdicts, exist_ok=True)
    os.makedirs(reports, exist_ok=True)
    todo = [ln.split("\t")[-1].strip() for ln in gate("todo", verdicts, "--size", "1").stdout.splitlines()
            if "\t" in ln]
    tag = len(os.listdir(verdicts))
    for path in todo:
        ch = os.path.splitext(os.path.basename(path))[0]
        rep = os.path.join(reports, ch + ".md")
        prompt = PROMPT.format(skill=SKILL, chapter=os.path.relpath(path, ROOT).replace(os.sep, "/"))
        # codex.cmd cuts arguments at newlines, so the prompt goes in on stdin ("-")
        rc = subprocess.run([shutil.which("codex"), "exec", "-s", "read-only", "--skip-git-repo-check", "-C", ROOT,
                             "-o", rep, "-"], input=prompt, text=True, encoding="utf-8",
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
        text = open(rep, encoding="utf-8").read() if os.path.exists(rep) else ""
        m = re.search(r"###\s*Assessment\s*\n+\W*(ok|issue)\W*(.*)", text, re.I)
        if rc or not m:
            print(f"{ch}: rc {rc}, no assessment (see {rep})")
            continue
        word, note = m.group(1).lower(), m.group(2).strip().replace("\t", " ")
        with open(os.path.join(verdicts, f"r{tag:02d}_{ch}.tsv"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(f"{ch}\t{word}\t{note}\n")
        print(f"{ch}: {word} {note}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--review", action="store_true")
    a = ap.parse_args()
    write_chapters()
    if a.review:
        review()
    r = gate("check", os.path.join(STORY, "verdicts"))
    print(r.stdout + r.stderr, end="")
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
