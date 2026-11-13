"""catpac.py: concatenate work/pac/**/*.bin (+ EXE, PRGs) into work/all.bin with work/all.idx (offset, size, path),
so one relsearch/scan covers every unpacked file. `python tools/catpac.py where 0xOFF` maps a blob offset back."""
import bisect
import glob
import os
import sys

if len(sys.argv) > 2 and sys.argv[1] == "where":
    rows = [l.split("\t") for l in open("work/all.idx", encoding="utf-8")]
    starts = [int(r[0]) for r in rows]
    for a in sys.argv[2:]:
        o = int(a, 0)
        i = bisect.bisect_right(starts, o) - 1
        print(f"{a} -> {rows[i][2].strip()} +{o - starts[i]:#x}")
    sys.exit()

files = sorted(glob.glob("work/pac/**/*.bin", recursive=True)) + sorted(glob.glob("work/disc/tree/DATA/*.PRG")) + [
    "work/disc/tree/SLPS_033.53"]
pos = 0
with open("work/all.bin", "wb") as out, open("work/all.idx", "w", encoding="utf-8") as idx:
    for f in files:
        d = open(f, "rb").read()
        out.write(d)
        idx.write(f"{pos}\t{len(d)}\t{f}\n")
        pos += len(d)
print(pos, "bytes,", len(files), "files")
