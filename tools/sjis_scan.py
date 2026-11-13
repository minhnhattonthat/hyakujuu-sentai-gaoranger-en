"""sjis_scan.py FILE.. [--min N] [--show K]: Shift-JIS runs that contain kana (filters out pixel noise).

Prints per file the count of runs with >= N kana and the first K runs (offset, text)."""
import argparse
import re
import sys

# a run: printable ASCII or valid 2-byte SJIS chars
SJ = re.compile(rb"(?:[\x20-\x7e]|[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc])+")
KANA = re.compile(r"[ぁ-ヿ]")


def runs(data, min_kana):
    for m in SJ.finditer(data):
        b = m.group()
        if len(b) < 4:
            continue
        try:
            s = b.decode("cp932")
        except UnicodeDecodeError:
            continue
        if len(KANA.findall(s)) >= min_kana:
            yield m.start(), s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--min", type=int, default=3)
    ap.add_argument("--show", type=int, default=5)
    a = ap.parse_args()
    for f in a.files:
        hits = list(runs(open(f, "rb").read(), a.min))
        print(f"{len(hits):6d} {f}")
        for off, s in hits[: a.show]:
            print(f"        {off:08x} {s[:80]}")


if __name__ == "__main__":
    sys.exit(main())
