"""verify.py: phase-7 checks on a finished build (build.py runs it last; exit 1 on any failure).

1. EXE: romdiff.check of the built EXE against the original. The expected writes come from assembling asm/vwf.asm a
   second time over a 0x00- and a 0xff-filled EXE (a byte armips wrote is the same in both), not from the built
   EXE: every write must sit inside a build.HOOKS site (whose original bytes it checks) or the width table region,
   the built EXE must hold exactly those bytes there, and nothing else may differ.
2. EXE + every PRG: no branch (EXE) or j/jal (EXE, PRGs) in code outside the overwritten spans, and no aligned
   32-bit word (jump tables, function pointers), lands strictly inside a hook span or anywhere in the width table.
   Not checked: lui/addiu pairs (checked once by hand, asm/vwf.asm).
3. PACs: every built PAC has the same leaves (recursing into lzs payloads) as the original, and the only leaves
   whose decoded bytes differ are the text tables (script/*.json "files") and the font TIMs (insert.FONT_LEAVES);
   any other leaf may only gain zero padding. romdiff for compressed archives: the lzs streams are re-encoded, so a
   byte diff of the PAC means nothing. The overlay holds only SLPS_033.53 and DATA/*.PAC.
4. Text: every string of every table, read back from the built PAC through its pointer slots, decodes to the text
   insert.text_for chose (en, marker, qa) or to its original jp bytes; every slot is checked, not only the first.
   jpleft.scan: no Japanese string left outside script/keep_jp.txt, no string table the extractor doesn't know.
5. Disc: dumpsxiso of the built .bin gives the original tree with the overlay files swapped in, byte for byte.
6. FMVs (fmvcap.py): only the caption frames' sectors change, with valid EDC/ECC, and every frame decodes.

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
import fmvcap  # noqa: E402
import font  # noqa: E402
import insert  # noqa: E402
import jpleft  # noqa: E402
import mkdisc  # noqa: E402
import pac  # noqa: E402
import romdiff  # noqa: E402
import strv  # noqa: E402
from tbl import Table  # noqa: E402

ROOT = mkdisc.ROOT
EXE_BASE = 0x80010000 - 0x800  # file offset = address - EXE_BASE
WTAB = build.DEAD[0]  # width table region: the replaced read/write PCdrv functions


def asm_writes(size, name="vwf.asm"):
    """[(file offset, bytes)] runs asm/<name> writes, from two armips runs over filled dummies of `size` bytes (bytes
    past `size`: the subs.asm blob appended to the image). subs.asm's code checksum word is filled in as build does."""
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "w.bin").write_bytes(font.widths())
        (t / "subs.asm").write_text(build.subs.asm(), encoding="ascii")
        outs = []
        for fill in (0x00, 0xFF):
            (t / "in.bin").write_bytes(bytes([fill]) * size)
            r = subprocess.run([str(build.ARMIPS), str(ROOT / "asm" / name), "-strequ", "EXE_IN", str(t / "in.bin"),
                                "-strequ", "EXE_OUT", str(t / "out.bin"), "-strequ", "WIDTHS", str(t / "w.bin"),
                                "-strequ", "SUBDATA", str(t / "subs.asm"), "-sym", str(t / "s.sym")],
                               capture_output=True)
            if r.returncode:
                raise SystemExit(f"armips failed: {r.stdout!r}")
            out = (t / "out.bin").read_bytes()
            outs.append(build.sub_checksum(out, t / "s.sym") if name == "subs.asm" else out)
    z, f = outs
    runs, start = [], None
    for i in range(len(z) + 1):
        w = i < len(z) and z[i] == f[i]
        if w and start is None:
            start = i
        elif not w and start is not None:
            runs.append((start, z[start:i]))
            start = None
    return runs


def check_exe(overlay):
    orig = (mkdisc.TREE / "SLPS_033.53").read_bytes()
    new = (Path(overlay) / "SLPS_033.53").read_bytes()
    writes, errs = [], []
    for name in ("vwf.asm", "subs.asm"):
        for o, data in asm_writes(len(orig), name):
            a, n = o + EXE_BASE, len(data)
            site = [(s, bytes.fromhex(h)) for s, h in build.HOOKS.items() if s <= a and a + n <= s + len(h) // 2]
            if any(lo <= a and a + n <= hi for lo, hi in build.DEAD):
                want = orig[o:o + n]  # the whole region is dead code, any original bytes are fine
            elif site:
                s, h = site[0]
                want = h[a - s:a - s + n]
            elif o >= len(orig):
                want = b"\xff" * n  # the appended blob (romdiff counts bytes past ORIG as 0xff)
            elif o == 0x1C and n == 4 and name == "subs.asm":
                want = orig[o:o + n]  # PS-X EXE header t_size: grows by the blob
            else:
                errs.append(f"EXE {name} writes {n} bytes at {a:08x}, outside every build.HOOKS site")
                continue
            writes.append((o, want, data, f"{name}@{a:08x}"))
    dead = set().union(*(range(lo - EXE_BASE, hi - EXE_BASE) for lo, hi in build.DEAD))
    e, _ = romdiff.check(orig, new, dead, writes)
    if len(new) % 0x800 or struct.unpack_from("<I", new, 0x1C)[0] != len(new) - 0x800:
        errs.append(f"EXE t_size {struct.unpack_from('<I', new, 0x1C)[0]:#x} != file size {len(new):#x} - 0x800")
    return errs + [f"EXE {x}" for x in e] + branch_errors(orig)


def branch_errors(exe, prgs=None):
    """Original code or data reaching into a span the build replaced (a hook's middle, or a dead region): EXE
    branches and j/jal, PRG j/jal (PRGs run at 0x80xxxxxx), and any aligned word in the EXE or a PRG."""
    spans = [(a, a + len(h) // 2) for a, h in build.HOOKS.items() if not any(lo <= a < hi for lo, hi in build.DEAD)]

    def indead(t):
        return any(lo <= t < hi for lo, hi in build.DEAD)

    def inside(t):
        return indead(t) or any(lo < t < hi for lo, hi in spans)

    def replaced(pc):
        return indead(pc) or any(lo <= pc < hi for lo, hi in spans)

    if prgs is None:
        prgs = {p.name: p.read_bytes() for p in sorted((mkdisc.TREE / "DATA").glob("*.PRG"))}
    t_addr, t_size = struct.unpack_from("<II", exe, 0x18)
    errs = []
    for pc in range(t_addr, t_addr + t_size, 4):
        if replaced(pc):
            continue
        w = struct.unpack_from("<I", exe, pc - EXE_BASE)[0]
        op = w >> 26
        t = None
        if op in (2, 3):  # j, jal
            t = (pc + 4) & 0xF0000000 | (w & 0x3FFFFFF) << 2
        elif op in (1, 4, 5, 6, 7):  # regimm, beq, bne, blez, bgtz
            t = pc + 4 + ((w & 0xFFFF) - ((w & 0x8000) << 1)) * 4
        if t is not None and inside(t):
            errs.append(f"EXE {pc:08x}: {w:08x} branches to {t:08x}, inside a replaced span")
        elif inside(w):
            errs.append(f"EXE {pc:08x}: word {w:08x} points inside a replaced span")
    for name, d in prgs.items():
        for o in range(0, len(d) - 3, 4):
            w = struct.unpack_from("<I", d, o)[0]
            if inside(w):
                errs.append(f"{name} +{o:x}: word {w:08x} points inside a replaced span")
            elif w >> 26 in (2, 3) and inside(0x80000000 | (w & 0x3FFFFFF) << 2):
                errs.append(f"{name} +{o:x}: j/jal {w:08x} into a replaced span")
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
    for f, data in insert.gfx_edit.patched_leaves().items():  # graphics leaves: exactly the edited images
        name, leaf = f.split("/")
        built = Path(overlay) / "DATA" / name
        got = insert.leaf_of(built.read_bytes(), leaf) if built.exists() else b""
        if got[:len(data)] != data or any(got[len(data):]):
            errs.append(f"{f}: graphics leaf differs from gfx/edits.py")
        allowed.add(f)
    for built in sorted((Path(overlay) / "DATA").glob("*.PAC")):
        old = dict(leaves((extract.DATA / built.name).read_bytes()))
        new = dict(leaves(built.read_bytes()))
        if set(old) != set(new):
            errs.append(f"{built.name}: leaf set changed: {sorted(set(old) ^ set(new))}")
            continue
        for p in old:
            name = f"{built.name}/{'_'.join(map(str, p))}"
            # raw leaves may be zero-padded to their old size: the original length must match, the rest be zero
            if (old[p] != new[p][:len(old[p])] or any(new[p][len(old[p]):])) and name not in allowed:
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


def check_overlay(overlay):
    """The build changes only the EXE, DATA/*.PAC files and the captioned FMVs."""
    rels = [p.relative_to(overlay).as_posix() for p in Path(overlay).rglob("*") if p.is_file()]
    fmv = {f"XA/{n}.STR" for n in fmvcap.edited()}
    return [f"overlay {r}: the build should not change this file" for r in rels
            if r != "SLPS_033.53" and r not in fmv
            and not (r.startswith("DATA/") and r.endswith(".PAC") and r.count("/") == 1)]


def check_fmv(overlay):
    """Captioned STRs: same size, only the caption frames' video sectors change, those keep valid EDC/ECC, and
    every caption frame still decodes."""
    errs = []
    for name, ranges in fmvcap.edited().items():
        rel = f"XA/{name}.STR"
        new, old = (Path(overlay) / rel).read_bytes(), (mkdisc.TREE / rel).read_bytes()
        if len(new) != len(old):
            errs.append(f"{rel}: size changed")
            continue
        allowed = fmvcap.caption_sectors(name)
        n = len(old) // strv.SECTOR
        for i in range(n):
            s = new[i * strv.SECTOR:(i + 1) * strv.SECTOR]
            if s == old[i * strv.SECTOR:(i + 1) * strv.SECTOR]:
                continue
            full = bytearray(16) + bytearray(s)
            mkdisc.fix_form1(full)
            if i not in allowed:
                errs.append(f"{rel}: sector {i} outside the caption frames changed")
            elif bytes(full[16:]) != s:
                errs.append(f"{rel}: sector {i} EDC/ECC wrong")
        try:
            for fno, secs, hd in strv.frames(new):
                if any(a <= fno <= b for a, b in ranges):  # a few untouched frames elsewhere don't parse cleanly (docs/re/fmv.md)
                    strv.parse(strv.frame_bytes(new, secs), hd["w"], hd["h"])
        except Exception as e:  # noqa: BLE001
            errs.append(f"{rel}: frame does not decode: {e}")
    return errs


def check_jpleft(overlay):
    left, unknown = jpleft.scan(overlay)
    return [f"jpleft: Japanese left {x}" for x in left] + [f"jpleft: unknown table {x}" for x in unknown]


def verify(bin_path, overlay, marker=False, qa=None):
    return (check_overlay(overlay) + check_exe(overlay) + check_pacs(overlay, marker, qa or {})
            + check_jpleft(overlay) + check_fmv(overlay) + check_disc(bin_path, overlay))


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
