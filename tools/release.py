"""release.py: build, gate and package the release (references/pipeline.md §Release). Stops at the first failure.

    python -X utf8 tools/release.py [--version 1.0] [--force] [--skip-build]

Steps: build (ends with verify.py) -> check.py -> smoke boot -> jpleft.py -> qa_gate check on every
work/qa/**/manifest.tsv (verdicts dir beside it) -> textcov on the tour -> no unticked docs/polish.md line -> no
template placeholder in README.md -> debug off (no debug file in the overlay; warp is external Lua only) -> xdelta3
patch vs the original .bin -> re-apply to the original and compare SHA-1 -> release/GaoRanger_EN_vX.Y.zip (patch +
README.txt, stored). Never publishes; that is the user's call (pipeline.md §Publish).
"""
import argparse
import hashlib
import re
import subprocess
import sys
import tempfile
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SKILL  # noqa: E402

ORIG = ROOT / "rom" / "Hyakujuu Sentai GaoRanger (Japan).bin"
ORIG_CUE = ORIG.with_suffix(".cue")
BUILT = ROOT / "build" / "gaoranger_en.bin"
PY = [sys.executable, "-X", "utf8"]


def run(name, cmd, **kw):
    print(f"== {name}", flush=True)
    rc = subprocess.call([str(c) for c in cmd], cwd=ROOT, **kw)
    if rc:
        sys.exit(f"release: {name} failed (exit {rc})")


def fail(msg):
    sys.exit(f"release: {msg}")


def hashes(p):
    data = p.read_bytes()
    return {"size": len(data), "crc32": f"{zlib.crc32(data):08x}", "md5": hashlib.md5(data).hexdigest(),
            "sha1": hashlib.sha1(data).hexdigest()}


def gates():
    for m in sorted((ROOT / "work" / "qa").rglob("manifest.tsv")):
        run(f"qa_gate {m.relative_to(ROOT)}", PY + [Path(SKILL) / "scripts" / "qa_gate.py", "check", m,
                                                   m.parent / "verdicts"])
    run("textcov", PY + [ROOT / "tools" / "textcov.py", ROOT / "work" / "qa" / "tour", "--waive",
                         ROOT / "script" / "text_unshown.tsv"])
    unticked = [ln for ln in (ROOT / "docs" / "polish.md").read_text(encoding="utf-8").splitlines()
                if ln.startswith("- [ ]")]
    if unticked:
        fail(f"{len(unticked)} unticked line(s) in docs/polish.md")
    ph = re.findall(r"<(?:Game title|platform|publisher|year|repo|file|size|sha1|game|ext|[A-Z][a-z]+ /[^>]*)>",
                    (ROOT / "README.md").read_text(encoding="utf-8"))
    if ph:
        fail(f"README.md template placeholders left: {sorted(set(ph))}")
    debug = [p for p in (ROOT / "build" / "overlay").rglob("*") if "DEBUG" in p.name.upper()]
    if debug:
        fail(f"debug files in the build overlay: {debug}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", default="1.0")
    ap.add_argument("--force", action="store_true", help="overwrite this version's existing release files")
    ap.add_argument("--skip-build", action="store_true", help="package the existing build (still verified)")
    a = ap.parse_args()
    out = ROOT / "release"
    stem = f"GaoRanger_EN_v{a.version}"
    patch, zpath = out / f"{stem}.xdelta", out / f"{stem}.zip"
    if (patch.exists() or zpath.exists()) and not a.force:
        fail(f"{zpath.name} exists; pass --force to overwrite")

    if not a.skip_build:
        run("build", PY + [ROOT / "tools" / "build.py"])  # plain build: no --marker/--qa
    else:
        run("verify", PY + [ROOT / "tools" / "verify.py", BUILT])
    run("check", PY + [ROOT / "tools" / "check.py"])
    run("smoke", PY + [Path(SKILL) / "scripts" / "emu.py", BUILT.with_suffix(".cue"), "--out",
                       ROOT / "work" / "qa" / "smoke", "--route", ROOT / "tools" / "routes" / "boot.txt", "--smoke"])
    run("jpleft", PY + [ROOT / "tools" / "jpleft.py"])
    gates()

    out.mkdir(exist_ok=True)
    base, built = hashes(ORIG), hashes(BUILT)
    if patch.exists():
        patch.unlink()
    # -B: match window = whole image (default 64 MB made disc patches huge, pipeline.md §Release)
    run("xdelta", ["xdelta3", "-e", "-9", "-B", str(base["size"]), "-s", ORIG, BUILT, patch])
    with tempfile.TemporaryDirectory() as td:
        back = Path(td) / "back.bin"
        run("re-apply", ["xdelta3", "-d", "-s", ORIG, patch, back])
        if hashes(back)["sha1"] != built["sha1"]:
            fail("re-applied patch differs from the build")
    readme = (ROOT / "docs" / "release-readme.txt").read_text(encoding="utf-8").format(
        version=a.version, patch=patch.name, cue_sha1=hashes(ORIG_CUE)["sha1"],
        patch_sha1=hashes(patch)["sha1"], **{f"base_{k}": v for k, v in base.items()},
        **{f"built_{k}": v for k, v in built.items()})
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_STORED) as z:
        z.write(patch, patch.name)
        z.writestr("README.txt", readme.replace("\n", "\r\n"))
    print(f"release: {zpath} (patch {patch.stat().st_size} bytes, sha1 {hashes(patch)['sha1']}; "
          f"patched .bin sha1 {built['sha1']}, crc32 {built['crc32']})")


if __name__ == "__main__":
    main()
