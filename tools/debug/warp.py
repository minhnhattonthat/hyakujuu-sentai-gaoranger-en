"""Warp to a scene from a cold boot (docs/re/flow.md §Debug tool). No debugger, so runs at full speed.

    python -X utf8 tools/debug/warp.py SCENE [--cue CUE] [--out DIR] [--frames N] [--state] [--trace]
    python -X utf8 tools/debug/warp.py --all [--jobs 3] [--state]    # every scene: shots + sheet, exit 1 on a miss;
                                                    # work/qa/warp/finals*.png = every scene's last frame
    python -X utf8 tools/debug/warp.py --list

tools/debug/scenes.txt, one scene per line (shell-style quoting):
    name  chapter  swap  after  expect  frames  route  description  [options]
  chapter  0 = leave (chapter 1), else written when the opening's chapter switch is in RAM
  swap     FROM>TO file ids (hex) for warp.lua, or -; a chain FROM>TO,FROM2>TO2 also swaps a load the first
           target's own script makes
  options  nomash (no circle presses after the route), card=PATH (start from this memory card instead of a blank
           one; card=unformatted: all zeros), var=NAME=LUA, var2=.. (extra warp.lua globals; later ones win)
A card the game wrote during the run is kept as work/saves/<scene>.mcd (a fixture for card=).
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
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from skill import SKILL  # noqa: E402
from blankcard import blank_card  # noqa: E402

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
        name, chapter, swap, after, expect, frames, route, desc, *opts = shlex.split(line)
        sw = [tuple(int(x, 16) for x in p.split(">")) for p in swap.split(",")] if swap != "-" else []
        if len(sw) > 2:
            raise SystemExit(f"{name}: at most two swaps")
        o = dict(x.split("=", 1) if "=" in x else (x, "1") for x in opts)
        scenes[name] = dict(name=name, chapter=int(chapter), swaps=sw, after=int(after),
                            expect=None if expect == "-" else int(expect, 16), frames=int(frames), route=route,
                            desc=desc, nomash="nomash" in o, card=o.get("card"),
                            vars=[v for k, v in o.items() if k.startswith("var")])
    return scenes


def run(sc, cue, out, frames, state, mash, trace, skip=True, card=None):
    out = out or os.path.join(ROOT, "work", "qa", "warp", sc["name"])
    os.makedirs(out, exist_ok=True)
    mash = mash and not sc["nomash"]
    card = card or (sc["card"] and os.path.join(ROOT, sc["card"]))
    if sc["card"] == "unformatted":  # all zeros: the game offers to format it
        card = os.path.join(out, "unformatted.mcd")
        open(card, "wb").write(bytes(128 * 1024))
    elif card and not os.path.exists(card):
        print(f"{sc['name']:14s} FAIL card {card} missing (run the scene that writes it first)", flush=True)
        return False
    if not card:  # each run gets its own empty card (emu.py copies it), so parallel runs never share saves
        card = os.path.join(out, "blank.mcd")
        open(card, "wb").write(blank_card())
    cmd = [sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "emu.py"), cue, "--out", out,
           "--frames", str(frames or sc["frames"]), "--shot-every", "150", "--sheet", "--timeout", "1500",
           "--script", os.path.join(ROOT, "tools", "debug", "warp.lua"),
           "--var", f"CHAPTER={sc['chapter']}", "--var", f"AFTER={sc['after']}", "--sav", card]
    for i, (fr, to) in enumerate(sc["swaps"]):
        n = str(i + 1) if i else ""
        cmd += ["--var", f"FROM{n}={fr:#x}", "--var", f"TO{n}={to:#x}"]
    if sc["expect"]:
        cmd += ["--var", f"EXPECT={sc['expect']:#x}"]
        ovl = OVERLAY.get(sc["expect"] >> 12)
        if ovl and skip:
            cmd += ["--var", f"SKIP={ovl:#x}"]
        if sc["expect"] >> 12 == 5 and mash:  # story/menu: stop pressing once it loads, end on its first box
            cmd += ["--var", "HOLD=1"]
    for v in sc["vars"]:  # last, so they override the defaults above
        cmd += ["--var", v]
    r = sc["route"]
    cmd += ["--route", os.path.join(ROOT, r)] if r.endswith(".txt") else ["--route-str", r]
    if mash:
        cmd += ["--mash", "60", "--mash-key", "circle"]
    if trace:
        cmd += ["--debugger", "--script", os.path.join(ROOT, "tools", "lua", "cdlog.lua")]
    if state:
        cmd += ["--state-out", os.path.join(ROOT, "work", "states", sc["name"] + ".sstate")]
    with open(os.path.join(out, "warp_cmd.log"), "w", encoding="utf-8") as f:
        p = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=ROOT)
    log = open(os.path.join(out, "log.txt"), encoding="utf-8", errors="replace").read() \
        if os.path.exists(os.path.join(out, "log.txt")) else ""
    wrote = os.path.join(out, "memcard1.mcd")  # what the game saved: keep it as a fixture (work/saves/<scene>.mcd)
    # save blocks only: the BIOS rewrites the header block's write-test frame on any card access
    if os.path.exists(wrote) and open(wrote, "rb").read()[8192:] != open(card, "rb").read()[8192:]:
        os.makedirs(os.path.join(ROOT, "work", "saves"), exist_ok=True)
        shutil.copy(wrote, os.path.join(ROOT, "work", "saves", sc["name"] + ".mcd"))
    why = "ok"
    if p.returncode != 0:
        why = f"emu.py exit {p.returncode}"
    elif sc["chapter"] and "CHAPTER frame" not in log:
        why = "chapter switch never found"
    elif sc["swaps"] and "SWAP frame" not in log:
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
    ap.add_argument("--card", help="memory card to start from (copied; default: a blank card per run)")
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
    res = []
    # scenes starting from a work/saves card run after the scenes that write those cards
    for batch in ([s for s in todo if not s["card"]], [s for s in todo if s["card"]]):
        with concurrent.futures.ThreadPoolExecutor(a.jobs) as ex:
            res += ex.map(lambda s: run(s, a.cue, None if a.all else a.out, a.frames, a.state, not a.no_mash,
                                        a.trace, not a.no_skip, a.card), batch)
    if a.all:  # one overview of every scene's last frame: work/qa/warp/finals*.png
        fin = os.path.join(ROOT, "work", "qa", "warp", "_finals")
        shutil.rmtree(fin, ignore_errors=True)
        os.makedirs(fin)
        pngs = []
        for i, s in enumerate(todo):
            src = os.path.join(ROOT, "work", "qa", "warp", s["name"], "final.png")
            if os.path.exists(src):
                pngs.append(os.path.join(fin, f"{i:02d}-{s['name']}.png"))
                shutil.copy(src, pngs[-1])
        subprocess.run([sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "sheet.py"), *pngs, "--out",
                        os.path.join(ROOT, "work", "qa", "warp", "finals.png")], cwd=ROOT)
    return 0 if all(res) else 1


if __name__ == "__main__":
    sys.exit(main())
