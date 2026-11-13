"""Warp to a scene from a cold boot (docs/re/flow.md §Debug tool). No debugger, so runs at full speed.

    python -X utf8 tools/debug/warp.py SCENE [--cue CUE] [--out DIR] [--frames N] [--state] [--trace]
    python -X utf8 tools/debug/warp.py --all [--jobs 3] [--state]    # every scene: shots + sheet, exit 1 on a miss
    python -X utf8 tools/debug/warp.py --list

tools/debug/scenes.txt, one scene per line (shell-style quoting):
    name  chapter  swap  after  expect  frames  route  description
  chapter  0 = leave (chapter 1), else written when the opening's chapter switch is in RAM
  swap     FROM>TO file ids (hex) for warp.lua, or -
  after    chapter to write once `expect` has loaded, 0 = none
  expect   file id (hex, tools/filetable.py) whose CD seek proves the warp (LOADED in log.txt), or -
  frames   run length; route = a tools/routes/*.txt file or an inline emu.py route string
Each run writes work/qa/warp/<scene>/ (a shot every 150 frames, sheet.png, final.png, log.txt) and, with
--state, work/states/<scene>.sstate. --trace adds tools/lua/cdlog.lua (+ --debugger: slow) to log every load.
"""
import argparse
import concurrent.futures
import os
import shlex
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from skill import SKILL  # noqa: E402

CUE = os.path.join(ROOT, "rom", "Hyakujuu Sentai GaoRanger (Japan).cue")
SCENES = os.path.join(ROOT, "tools", "debug", "scenes.txt")
# expect id kind -> overlay that runs it (A_SYS, B_SYS). Story/menu files (D_SYS) get no skip: they and D_SYS are
# preloaded before the opening can be skipped, and START in the story skips the story itself.
OVERLAY = {3: 0xC002, 4: 0xC003}


def load_scenes():
    scenes = {}
    for line in open(SCENES, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, chapter, swap, after, expect, frames, route, desc = shlex.split(line)
        fr, to = (int(x, 16) for x in swap.split(">")) if swap != "-" else (0, 0)
        scenes[name] = dict(name=name, chapter=int(chapter), fr=fr, to=to, after=int(after),
                            expect=None if expect == "-" else int(expect, 16), frames=int(frames), route=route,
                            desc=desc)
    return scenes


def run(sc, cue, out, frames, state, mash, trace, skip=True):
    out = out or os.path.join(ROOT, "work", "qa", "warp", sc["name"])
    cmd = [sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "emu.py"), cue, "--out", out,
           "--frames", str(frames or sc["frames"]), "--shot-every", "150", "--sheet", "--timeout", "1500",
           "--script", os.path.join(ROOT, "tools", "debug", "warp.lua"),
           "--var", f"CHAPTER={sc['chapter']}", "--var", f"FROM={sc['fr']:#x}", "--var", f"TO={sc['to']:#x}",
           "--var", f"AFTER={sc['after']}"]
    if sc["expect"]:
        cmd += ["--var", f"EXPECT={sc['expect']:#x}"]
        ovl = OVERLAY.get(sc["expect"] >> 12)
        if ovl and skip:
            cmd += ["--var", f"SKIP={ovl:#x}"]
        if sc["expect"] >> 12 == 5 and mash:  # story/menu: stop pressing once it loads, end on its first box
            cmd += ["--var", "HOLD=1"]
    r = sc["route"]
    cmd += ["--route", os.path.join(ROOT, r)] if r.endswith(".txt") else ["--route-str", r]
    if mash:
        cmd += ["--mash", "60", "--mash-key", "circle"]
    if trace:
        cmd += ["--debugger", "--script", os.path.join(ROOT, "tools", "lua", "cdlog.lua")]
    if state:
        cmd += ["--state-out", os.path.join(ROOT, "work", "states", sc["name"] + ".sstate")]
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "warp_cmd.log"), "w", encoding="utf-8") as f:
        p = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=ROOT)
    log = open(os.path.join(out, "log.txt"), encoding="utf-8", errors="replace").read() \
        if os.path.exists(os.path.join(out, "log.txt")) else ""
    why = "ok"
    if p.returncode != 0:
        why = f"emu.py exit {p.returncode}"
    elif sc["chapter"] and "CHAPTER frame" not in log:
        why = "chapter switch never found"
    elif sc["fr"] and "SWAP frame" not in log:
        why = "swap op never found"
    elif sc["expect"] and "LOADED frame" not in log:
        why = f"file {sc['expect']:04x} never loaded"
    print(f"{sc['name']:14s} {'OK  ' if why == 'ok' else 'FAIL'} {why}  {os.path.relpath(out, ROOT)}", flush=True)
    return why == "ok"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scene", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--cue", default=CUE)
    ap.add_argument("--out")
    ap.add_argument("--frames", type=int)
    ap.add_argument("--state", action="store_true", help="save work/states/<scene>.sstate at the end")
    ap.add_argument("--no-mash", action="store_true", help="don't press circle every 60 frames after the route")
    ap.add_argument("--trace", action="store_true", help="log every file load (debugger: slow)")
    ap.add_argument("--no-skip", action="store_true", help="watch the opening and earlier story instead of "
                    "tapping START through them")
    ap.add_argument("--jobs", type=int, default=3)
    a = ap.parse_args()
    scenes = load_scenes()
    if a.list:
        for s in scenes.values():
            print(f"{s['name']:14s} {s['desc']}")
        return 0
    bad = [s for s in a.scene if s not in scenes]
    todo = list(scenes.values()) if a.all else [scenes[s] for s in a.scene]
    if bad or not todo:
        ap.error(f"unknown scene(s) {bad}; --list shows them")
    if len(todo) > 1:
        a.out = None
    with concurrent.futures.ThreadPoolExecutor(a.jobs) as ex:
        res = list(ex.map(lambda s: run(s, a.cue, None if a.all else a.out, a.frames, a.state, not a.no_mash,
                                        a.trace, not a.no_skip), todo))
    return 0 if all(res) else 1


if __name__ == "__main__":
    sys.exit(main())
