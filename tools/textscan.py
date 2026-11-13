"""textscan.py: find GaoRanger string tables in unpacked files (work/pac/**) and print them decoded.

Table format (docs/re/text.md): u16 LE a, u16 LE count, count x u16 LE offsets (from file start), strings.
String: big-endian glyph codes 00A0..01F4, 82 = newline, FF = end.
    python -X utf8 tools/textscan.py [--show] [FILES..]    (default: every work/pac/**/*.bin)"""
import glob
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import make_tbl  # noqa: E402

CH = dict(make_tbl.entries())


def decode(d, p):
    """Returns (text, end) or None if not a clean string."""
    out = []
    while p < len(d):
        b = d[p]
        if b == 0xFF:
            return "".join(out), p + 1
        if b == 0x85 and p + 1 < len(d):
            out.append(f"{{col:{d[p + 1]:02X}}}")
            p += 2
            continue
        if b in (0x81, 0x82):
            out.append(" " if b == 0x81 else "\n")
            p += 1
            continue
        if b in (0, 1) and p + 1 < len(d):
            c = (b << 8) | d[p + 1]
            if c not in CH:
                return None
            out.append(CH[c])
            p += 2
            continue
        return None
    return None


def table(d):
    if len(d) < 8:
        return None
    a, n = struct.unpack_from("<HH", d, 0)
    if not 0 < n < 2000 or 4 + 2 * n > len(d):
        return None
    offs = struct.unpack_from(f"<{n}H", d, 4)
    if min(offs) < 4 + 2 * n or max(offs) > len(d):
        return None
    if max(offs) == len(d):  # O_TITLE.PAC/2: last entry points at the file end = empty string
        offs = tuple(o for o in offs if o < len(d))
    strings = {}
    for o in sorted(set(offs)):
        s = decode(d, o)
        if s is None:
            return None
        strings[o] = s
    return a, offs, strings


def main():
    show = "--show" in sys.argv
    files = [f for f in sys.argv[1:] if not f.startswith("--")] or sorted(glob.glob("work/pac/**/*.bin", recursive=True))
    total = 0
    for f in files:
        d = open(f, "rb").read()
        t = table(d)
        if not t:
            continue
        a, offs, strings = t
        total += len(strings)
        print(f"{f}  a={a} entries={len(offs)} strings={len(strings)} size={len(d)}")
        if show:
            for o, (s, end) in strings.items():
                print(f"   {o:04x}-{end:04x} " + s.replace("\n", "/"))
    print("total strings", total)


if __name__ == "__main__":
    main()
