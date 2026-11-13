"""mkdisc.py: build the disc image from work/disc/tree + an overlay dir, matching the original's mastering.

mkpsxiso builds from disc/layout.xml (from dumpsxiso, tuned). Then fix_image() reproduces what mkpsxiso can't express
(docs/re/disc.md §Rebuild): the PVD sector's submode, the root directory's 1901 date, the data track's postgap
subheaders, and the track-2 pregap that the original cue declares (PREGAP) but does not store in the .bin.
With an empty overlay the result is byte-identical to the original dump (tests/test_disc.py).

    python -X utf8 tools/mkdisc.py OUT.bin [--overlay DIR]   # files in DIR (same paths as the tree) replace originals
"""
import argparse
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT / "work" / "disc" / "tree"
LAYOUT = ROOT / "disc" / "layout.xml"
MKPSXISO = ROOT / "tools" / "mkpsxiso" / "mkpsxiso-2.30-win64" / "mkpsxiso.exe"
SEC = 2352
PREGAP = 150  # track 2 pregap in sectors: counted in disc LBAs, absent from the .bin (orig cue: PREGAP 00:02:00)
POSTGAP = 150  # data track's last sectors (layout <dummy>): original has submode 0 and no EDC except the last two
ROOT_DATE = bytes.fromhex("010a01052f3224")  # 1901-10-01 05:47:50 +9h, the mastering tool's root dir stamp
PVD_SUBMODE = 0x08  # original PVD subheader (mkpsxiso writes 0x09; cdvd_style=true breaks the path tables instead)

# --- EDC/ECC (ECMA-130), for mode 2 form 1 sectors we touch ---
_F = [0] * 256
_B = [0] * 256
_EDC = [0] * 256
for _i in range(256):
    _j = ((_i << 1) ^ (0x11D if _i & 0x80 else 0)) & 0xFF
    _F[_i] = _j
    _B[_i ^ _j] = _i
    _e = _i
    for _ in range(8):
        _e = (_e >> 1) ^ (0xD8018001 if _e & 1 else 0)
    _EDC[_i] = _e


def edc(data):
    e = 0
    for b in data:
        e = (e >> 8) ^ _EDC[(e ^ b) & 0xFF]
    return e


def _ecc_block(s, major_count, minor_count, major_mult, minor_inc, dest):
    size = major_count * minor_count
    for major in range(major_count):
        index = (major >> 1) * major_mult + (major & 1)
        a = b = 0
        for _ in range(minor_count):
            t = s[0xC + index]
            index += minor_inc
            if index >= size:
                index -= size
            a ^= t
            b ^= t
            a = _F[a]
        a = _B[_F[a] ^ b]
        s[dest + major] = a
        s[dest + major + major_count] = a ^ b


def fix_form1(sector):
    """Recompute EDC and ECC of a mode 2 form 1 sector (bytearray of 2352) in place."""
    struct.pack_into("<I", sector, 0x818, edc(sector[0x10:0x818]))
    addr = bytes(sector[12:16])
    sector[12:16] = b"\0\0\0\0"  # mode 2: ECC is computed with a zero header
    _ecc_block(sector, 86, 24, 2, 86, 0x81C)
    _ecc_block(sector, 52, 43, 86, 88, 0x8C8)
    sector[12:16] = addr


def layout_xml(overlay):
    """disc/layout.xml with absolute source paths; files present in overlay get it as their source."""
    tree = ET.parse(LAYOUT)
    track = tree.find("track")
    track.find("license").set("file", str(TREE / "license_data.dat"))
    dt = track.find("directory_tree")
    dt.set("source", str(TREE))
    for t in tree.findall("track"):
        if t.get("source"):
            t.set("source", str(TREE / Path(t.get("source")).relative_to("tree")))

    def walk(el, rel):
        for c in el:
            if c.tag == "dir":
                walk(c, rel / c.get("name"))
            elif c.tag == "file" and overlay and (overlay / rel / c.get("name")).is_file():
                c.set("source", str(overlay / rel / c.get("name")))
    walk(dt, Path())
    return tree


def fix_image(data):
    """data: bytearray of the mkpsxiso image (with the pregap stored). Returns the fixed image bytes and the
    track-2 start sector in the .bin."""
    sec = lambda n: data[n * SEC:(n + 1) * SEC]
    pvd = sec(16)
    root_lba = struct.unpack_from("<I", pvd, 24 + 156 + 2)[0]
    vol = struct.unpack_from("<I", pvd, 24 + 80)[0]
    # data track length: the first DA file's extent starts at track 2 INDEX 01 (= stored pregap + data track)
    track2 = None
    dirty = {16}
    touched = {}

    def put(n, s):
        data[n * SEC:(n + 1) * SEC] = s

    pvd[24 + 156 + 18:24 + 156 + 25] = ROOT_DATE
    pvd[18] = pvd[22] = PVD_SUBMODE
    touched[16] = pvd
    # walk every directory: set the root's date wherever a record points at the root extent; find DA files
    todo, seen = [root_lba], set()
    while todo:
        lba = todo.pop()
        if lba in seen:
            continue
        seen.add(lba)
        size = None
        n = lba
        while size is None or (n - lba) * 2048 < size:
            s = touched.get(n) or sec(n)
            o = 24
            while o < 24 + 2048 and s[o]:
                rl = s[o]
                r_lba, r_size, flags = struct.unpack_from("<I", s, o + 2)[0], struct.unpack_from("<I", s, o + 10)[0], s[o + 25]
                if size is None:
                    size = r_size  # "." record gives the directory's own size
                if r_lba == root_lba and s[o + 18:o + 25] != ROOT_DATE:
                    s[o + 18:o + 25] = ROOT_DATE
                    touched[n] = s
                    dirty.add(n)
                if flags & 2 and s[o + 32] > 1:
                    todo.append(r_lba)
                if s[o + 33 + s[o + 32] + (1 - s[o + 32] % 2) + 4] & 0x40:  # XA attributes (BE u16) bit 14: CD-DA
                    track2 = r_lba if track2 is None else min(track2, r_lba)
                o += rl
            n += 1
    for n in dirty:
        fix_form1(touched[n])
        put(n, touched[n])
    assert track2 is not None, "no DA file in the directory: can't place the pregap"
    data_end = track2 - PREGAP  # sectors of the data track
    for n in range(data_end - POSTGAP, data_end - 2):
        s = sec(n)
        assert s[16:24] == b"\0\0\x20\0\0\0\x20\0", f"sector {n} isn't the layout's postgap dummy"
        s[16:24] = b"\0" * 8
        s[0x92C:0x930] = b"\0" * 4
        put(n, s)
    assert vol * SEC == len(data), (vol, len(data))
    del data[data_end * SEC:track2 * SEC]  # the pregap stays out of the .bin
    return data, data_end


def msf(n):
    return f"{n // 4500:02d}:{n // 75 % 60:02d}:{n % 75:02d}"


def build(out_bin, overlay=None):
    out_bin = Path(out_bin).resolve()
    out_bin.parent.mkdir(parents=True, exist_ok=True)
    xml = out_bin.with_suffix(".layout.xml")
    layout_xml(Path(overlay).resolve() if overlay else None).write(xml, encoding="utf-8")
    raw = out_bin.with_suffix(".mkpsxiso.bin")
    r = subprocess.run([str(MKPSXISO), "-q", "-y", "-o", str(raw), "-c", str(raw.with_suffix(".cue")), str(xml)],
                       capture_output=True, text=True)
    if r.returncode or not raw.is_file():
        sys.exit(f"mkpsxiso failed ({r.returncode}):\n{r.stdout}{r.stderr}")
    data, track2 = fix_image(bytearray(raw.read_bytes()))
    out_bin.write_bytes(data)
    raw.unlink()
    raw.with_suffix(".cue").unlink(missing_ok=True)
    out_bin.with_suffix(".cue").write_text(
        f'FILE "{out_bin.name}" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n'
        f"  TRACK 02 AUDIO\n    PREGAP 00:02:00\n    INDEX 01 {msf(track2)}\n", encoding="utf-8", newline="\n")
    return out_bin


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("--overlay")
    a = ap.parse_args()
    print(build(a.out, a.overlay))
