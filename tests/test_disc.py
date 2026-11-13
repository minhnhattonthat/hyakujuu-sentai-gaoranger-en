"""Phase 3 identity: the rebuilt disc and every repacked PAC equal the originals; our lzs encoder roundtrips."""
import hashlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import mkdisc  # noqa: E402
import pac  # noqa: E402

BIN = ROOT / "rom" / "Hyakujuu Sentai GaoRanger (Japan).bin"
PACS = sorted((mkdisc.TREE / "DATA").glob("*.PAC"))
need_tree = pytest.mark.skipif(not PACS, reason="no unpacked disc tree (tools/build.py makes it)")


def orig_sha1():
    return next(l.split()[0] for l in (ROOT / "rom.sha1").read_text().splitlines() if l.strip().endswith(".bin"))


@need_tree
def test_disc_identity(tmp_path):
    out = mkdisc.build(tmp_path / "ident.bin")
    with open(out, "rb") as f:
        assert hashlib.file_digest(f, "sha1").hexdigest() == orig_sha1()
    cue = out.with_suffix(".cue").read_text()
    assert "PREGAP 00:02:00" in cue and "INDEX 01 13:50:37" in cue


@pytest.mark.skipif(not BIN.is_file(), reason="no ROM")
def test_edc_ecc_matches_original():
    with open(BIN, "rb") as f:
        for n in (16, 22, 23, 193):  # PVD, root dir, EXE start, DATA dir: mode 2 form 1
            f.seek(n * mkdisc.SEC)
            s = f.read(mkdisc.SEC)
            t = bytearray(s)
            t[0x818:] = bytes(len(t) - 0x818)
            mkdisc.fix_form1(t)
            assert bytes(t) == s, n


@need_tree
def test_pac_repack_identity():
    for f in PACS:
        d = f.read_bytes()
        assert pac.build(pac.parse(d)) == d, f.name


@need_tree
def test_lzs_encode_roundtrip_real_blocks():
    for f in PACS:  # first lzs block of every PAC (tools/movetest.py re-encodes all of them)
        d = f.read_bytes()
        for _, off, _, k in pac.walk(d, 0, len(d)):
            if k == "lzs":
                h = pac.lzs_header(d, off)
                blob = pac.lzs_decode(d, off)[0]
                enc = pac.lzs_encode(blob, h["lbits"], h["name"], h["fbits"])
                assert pac.lzs_decode(enc, 0)[0] == blob, f.name
                break


def test_lzs_encode_edges():
    for lbits in (2, 4, 7):
        for data in (b"", b"a", b"aaaa" * 300, bytes(range(256)) * 3 + b"xyz", b"ab" * 1000 + bytes(5000)):
            enc = pac.lzs_encode(data, lbits)
            assert pac.lzs_decode(enc, 0)[0] == data
    blk = pac.lzs_encode(bytes(1000), 4)
    assert pac.lzs_header(blk, 0)["psize"] == len(blk)
