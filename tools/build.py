"""build.py: build the patched disc -> build/gaoranger_en.bin/.cue.

Checks the dump (rom.sha1), unpacks the disc tree if missing, writes every changed file into build/overlay/
(same paths as work/disc/tree): the EXE with the VWF hook (asm/vwf.asm), the PACs with the English font and text
tables (insert.py). Then builds the image with mkdisc.py. With an empty overlay the .bin is byte-identical to the
original (tests/test_disc.py).

    python -X utf8 tools/build.py [--out build/gaoranger_en.bin] [--marker]
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_rom  # noqa: E402
import font  # noqa: E402
import insert  # noqa: E402
import mkdisc  # noqa: E402

ROOT = mkdisc.ROOT
CUE = ROOT / "rom" / "Hyakujuu Sentai GaoRanger (Japan).cue"
DUMPSXISO = ROOT / "tools" / "mkpsxiso" / "mkpsxiso-2.30-win64" / "dumpsxiso.exe"
ARMIPS = ROOT / "tools" / "armips" / "armips.exe"
# original EXE bytes at every site asm/vwf.asm writes (a different EXE revision fails here, not in game)
HOOKS = {
    0x80022A6C: "58bfbd27211880009840b2af",  # host-file read prologue (dead code, becomes the width table)
    0x80027260: "00000000",
    0x80027290: "04008294000000008000423006004010ffffc331401003002110430080100200b19c0008211043004010030021104300"
                "8010020021600202",
    0x800154D8: "14000724",
    0x80015504: "14000724",
}


def ensure_tree():
    if (mkdisc.TREE / "SLPS_033.53").is_file():
        return
    out = mkdisc.TREE.parent
    r = subprocess.run([str(DUMPSXISO), "-q", "-x", str(mkdisc.TREE), "-s", str(out / "layout.xml"), str(CUE)])
    if r.returncode or not (mkdisc.TREE / "SLPS_033.53").is_file():
        sys.exit("dumpsxiso failed: see docs/re/disc.md")


def build_exe(overlay):
    """asm/vwf.asm over the original EXE -> overlay/SLPS_033.53, after checking the bytes it replaces."""
    exe = mkdisc.TREE / "SLPS_033.53"
    orig = exe.read_bytes()
    for addr, hexbytes in HOOKS.items():
        o = addr - 0x80010000 + 0x800
        if orig[o:o + len(hexbytes) // 2].hex() != hexbytes:
            sys.exit(f"EXE bytes at {addr:08x} differ from what asm/vwf.asm expects")
    widths = ROOT / "build" / "vwf_widths.bin"
    widths.write_bytes(font.widths())
    out = overlay / "SLPS_033.53"
    r = subprocess.run([str(ARMIPS), str(ROOT / "asm" / "vwf.asm"), "-strequ", "EXE_IN", str(exe),
                        "-strequ", "EXE_OUT", str(out), "-strequ", "WIDTHS", str(widths)])
    if r.returncode or len(out.read_bytes()) != len(orig):
        sys.exit("armips failed")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "build" / "gaoranger_en.bin"))
    ap.add_argument("--marker", action="store_true", help="every Japanese string -> [id] marker text (phase 5)")
    ap.add_argument("--qa", action="append", default=[], metavar="ID=TEXT",
                    help="override one string (width-gate stress lines); repeatable")
    a = ap.parse_args()
    qa = dict(x.split("=", 1) for x in a.qa)
    check_rom.check()
    ensure_tree()
    overlay = ROOT / "build" / "overlay"
    shutil.rmtree(overlay, ignore_errors=True)
    overlay.mkdir(parents=True)
    font.selftest()
    font.write_tbl()
    build_exe(overlay)
    insert.insert(overlay, marker=a.marker, qa=qa)
    out = mkdisc.build(a.out, overlay)
    import verify  # imports build: load it late
    errs = verify.verify(out, overlay, a.marker, qa)
    for e in errs[:100]:
        print(e)
    if errs:
        sys.exit(f"verify: {len(errs)} errors in {out}")
    print(out.with_suffix(".cue"))


if __name__ == "__main__":
    main()
