"""verify.py: phase-7 checks on a finished build (build.py runs it last; exit 1 on any failure).

1. EXE: romdiff.check of the built EXE against the original: changed bytes only at the asm/vwf.asm sites, each
   write's original bytes as build.HOOKS expects, the width table only inside the dead PCdrv code.
2. EXE: no branch or j/jal in the original code (outside the overwritten spans) lands strictly inside a hook span,
   or anywhere in the width table region.
3. PACs: every built PAC has the same leaves (recursing into lzs payloads) as the original, and the only leaves
   whose decoded bytes differ are the text tables (script/*.json "files") and the font TIMs (insert.FONT_LEAVES).
   This is romdiff for compressed archives: the lzs streams are re-encoded, so a byte diff of the PAC means nothing.
4. Text: every string of every table, read back from the built PAC through its pointer slots, decodes to the text
   insert.text_for chose (en, marker, qa) or to its original jp bytes; every slot is checked, not only the first.
5. Disc: dumpsxiso of the built .bin gives the original tree with the overlay files swapped in, byte for byte.

    python -X utf8 tools/verify.py [build/gaoranger_en.bin] [--marker] [--qa ID=TEXT ...]
"""
import argparse
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402
import extract  # noqa: E402
import insert  # noqa: E402
import mkdisc  # noqa: E402
import pac  # noqa: E402
import romdiff  # noqa: E402
from tbl import Table  # noqa: E402

ROOT = mkdisc.ROOT
EXE_BASE = 0x80010000 - 0x800  # file offset = address - EXE_BASE
WTAB = (0x80022A6C, 0x80022BC4)  # width table region: the replaced read/write PCdrv functions


def check_exe(overlay):
    orig = (mkdisc.TREE / "SLPS_033.53").read_bytes()
    new = (Path(overlay) / "SLPS_033.53").read_bytes()
    writes = []
    for addr, hexbytes in build.HOOKS.items():
        o, n = addr - EXE_BASE, len(hexbytes) // 2
        if addr != WTAB[0]:  # the table site is covered by the allowed range below
            writes.append((o, bytes.fromhex(hexbytes), new[o:o + n], f"vwf.asm@{addr:08x}"))
    errs, _ = romdiff.check(orig, new, set(range(WTAB[0] - EXE_BASE, WTAB[1] - EXE_BASE)), writes)
    return [f"EXE {e}" for e in errs] + branch_errors(orig)


def branch_errors(exe):
    """Original code reaching into a span the build replaced (a hook's middle, or the width table)."""
    spans = [(a, a + len(h) // 2) for a, h in build.HOOKS.items() if a != WTAB[0]]
    t_addr, t_size = struct.unpack_from("<II", exe, 0x18)
    errs = []
    for pc in range(t_addr, t_addr + t_size, 4):
        if WTAB[0] <= pc < WTAB[1] or any(lo <= pc < hi for lo, hi in spans):
            continue
        w = struct.unpack_from("<I", exe, pc - EXE_BASE)[0]
        op = w >> 26
        if op in (2, 3):  # j, jal
            t = (pc + 4) & 0xF0000000 | (w & 0x3FFFFFF) << 2
        elif op in (1, 4, 5, 6, 7):  # regimm, beq, bne, blez, bgtz
            t = pc + 4 + ((w & 0xFFFF) - ((w & 0x8000) << 1)) * 4
        else:
            continue
        if WTAB[0] <= t < WTAB[1] or any(lo < t < hi for lo, hi in spans):
            errs.append(f"EXE {pc:08x}: {w:08x} branches to {t:08x}, inside a replaced span")
    return errs


def leaves(d, path=()):
    """(path, decoded bytes) of every leaf; lzs payloads are decoded and their add tables walked (insert.set_leaf's
    path convention: an lzs node adds no path component)."""
    k = pac.kind(d, 0)
    if k == "lzs":
        yield from leaves(pac.lzs_decode(d, 0)[0], path)
    elif k == "add":
        for i, o, s in pac.add_entries(d, 0):
            if s:
                yield from leaves(d[o:o + s], path + (i,))
    else:
        yield path, d


def check_pacs(overlay, marker, qa):
    allowed = set(insert.FONT_LEAVES)
    tables = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "script").glob("*.json"))]
    for t in tables:
        allowed |= set(t["files"])
    errs = []
    for built in sorted((Path(overlay) / "DATA").glob("*.PAC")):
        old = dict(leaves((extract.DATA / built.name).read_bytes()))
        new = dict(leaves(built.read_bytes()))
        if set(old) != set(new):
            errs.append(f"{built.name}: leaf set changed: {sorted(set(old) ^ set(new))}")
            continue
        for p in old:
            name = f"{built.name}/{'_'.join(map(str, p))}"
            # raw leaves may be zero-padded to their old size, so compare the original length only
            if old[p] != new[p][:len(old[p])] and name not in allowed:
                errs.append(f"{name}: changed but is neither a text table nor a font")
    en = Table.load(ROOT / "tbl" / "en.tbl")
    for t in tables:
        for f in t["files"]:
            name, leaf = f.split("/")
            built = Path(overlay) / "DATA" / name
            d = insert.leaf_of((built if built.exists() else extract.DATA / name).read_bytes(), leaf)
            n = struct.unpack_from("<H", d, 2)[0]
            if n != t["count"]:
                errs.append(f"{f}: {n} slots, script has {t['count']}")
                continue
            offs = struct.unpack_from(f"<{n}H", d, 4)
            for s in t["strings"]:
                text = insert.text_for(s, marker, qa)
                for i in s["slots"]:
                    if text:
                        got = en.decode(d, offs[i])[0]
                        ok = got == text + "{end}"
                    else:
                        want = extract.TBL.encode(s["jp"] + "{end}")
                        got, ok = d[offs[i]:offs[i] + len(want)], d[offs[i]:offs[i] + len(want)] == want
                    if not ok:
                        errs.append(f"{f} {s['id']} slot {i}: reads back {got!r}")
    return errs


def check_disc(bin_path, overlay):
    errs = []
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run([str(build.DUMPSXISO), "-q", "-x", tmp, "-s", str(Path(tmp) / "l.xml"),
                            str(Path(bin_path).with_suffix(".cue"))], capture_output=True)
        if r.returncode:
            return [f"dumpsxiso failed on {bin_path}"]
        got = {p.relative_to(tmp).as_posix(): p for p in Path(tmp).rglob("*") if p.is_file() and p.name != "l.xml"}
        want = {p.relative_to(mkdisc.TREE).as_posix(): p for p in mkdisc.TREE.rglob("*") if p.is_file()}
        if set(got) != set(want):
            errs.append(f"disc file set differs: {sorted(set(got) ^ set(want))}")
        for rel in sorted(set(got) & set(want)):
            ov = Path(overlay) / rel
            src = ov if ov.is_file() else want[rel]
            if got[rel].read_bytes() != src.read_bytes():
                errs.append(f"disc {rel}: differs from {'overlay' if ov.is_file() else 'original'}")
    return errs


def verify(bin_path, overlay, marker=False, qa=None):
    return check_exe(overlay) + check_pacs(overlay, marker, qa or {}) + check_disc(bin_path, overlay)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bin", nargs="?", default=str(ROOT / "build" / "gaoranger_en.bin"))
    ap.add_argument("--overlay", default=str(ROOT / "build" / "overlay"))
    ap.add_argument("--marker", action="store_true")
    ap.add_argument("--qa", action="append", default=[], metavar="ID=TEXT")
    a = ap.parse_args()
    errs = verify(a.bin, a.overlay, a.marker, dict(x.split("=", 1) for x in a.qa))
    for e in errs[:100]:
        print(e)
    print(f"verify: {len(errs)} errors")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
