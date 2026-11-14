"""Visual QA by independent read-only reviewers (codex exec), one per qa_gate chunk (docs/visual-qa-brief.md).

    python -X utf8 tools/vqa_codex.py work/qa/tour [--size 12] [--jobs 4]

Runs qa_gate.py todo on TOUR/manifest.tsv, then `codex exec -s read-only` per chunk; each reviewer's last message
(TSV verdict lines) is saved as TOUR/verdicts/<chunk>.tsv. Orca workers can't start subagents, so codex is the
independent reviewer here (D10-style worker call).
"""
import argparse
import concurrent.futures
import glob
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from skill import SKILL  # noqa: E402

PROMPT = """You are a read-only visual-QA reviewer. Follow docs/visual-qa-brief.md exactly (read it first; SKILL is
{skill}). Your chunk file is {chunk}: one sheet path per line (contact sheets of an English fan translation of a
Japanese PS1 game). Open and look at EVERY sheet with your image viewing tool; zoom into frames (they sit next to
each sheet, named fNNNNNN.png) wherever text is small. You cannot write files: your FINAL message must be ONLY the
verdict lines, one per sheet, `id<TAB>ok|issue<TAB>note`, where id is the sheet path relative to work/qa/tour
without the .png extension (e.g. ds01/qa_sheet_2). No other text in the final message."""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tour")
    ap.add_argument("--size", default="12")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    chunks_dir = os.path.join(a.tour, "chunks")
    verdicts = os.path.join(a.tour, "verdicts")
    os.makedirs(verdicts, exist_ok=True)
    for old in glob.glob(os.path.join(chunks_dir, "chunk_*.txt")):
        os.remove(old)
    subprocess.check_call([sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "qa_gate.py"), "todo",
                           os.path.join(a.tour, "manifest.tsv"), verdicts, "--size", a.size, "--out-dir", chunks_dir])
    chunks = sorted(glob.glob(os.path.join(chunks_dir, "chunk_*.txt")))
    tag = len(glob.glob(os.path.join(verdicts, "*.tsv")))

    def review(chunk):
        name = os.path.splitext(os.path.basename(chunk))[0]
        out = os.path.join(verdicts, f"r{tag:02d}_{name}.tsv")
        prompt = PROMPT.format(skill=SKILL, chunk=os.path.relpath(chunk, ROOT).replace(os.sep, "/"))
        # codex.cmd on Windows: a batch file cuts arguments at newlines, so the prompt goes in on stdin ("-")
        rc = subprocess.run([shutil.which("codex"), "exec", "-s", "read-only", "--skip-git-repo-check", "-C", ROOT,
                             "-o", out, "-"], input=prompt, text=True, encoding="utf-8",
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
        return name, rc, out

    with concurrent.futures.ThreadPoolExecutor(a.jobs) as ex:
        for name, rc, out in ex.map(review, chunks):
            lines = open(out, encoding="utf-8").read().splitlines() if os.path.exists(out) else []
            bad = [ln for ln in lines if ln.split("\t")[1:2] == ["issue"]]
            print(f"{name}: rc {rc}, {len(lines)} verdicts, {len(bad)} issues", flush=True)
            for ln in bad:
                print("   ", ln, flush=True)


if __name__ == "__main__":
    main()
