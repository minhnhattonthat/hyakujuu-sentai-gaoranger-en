"""Which files each script-bearing file loads next: scans PAC leaves, PRGs and the EXE for the sequence-script op
`03 00 <u16 id>` (load file, docs/re/flow.md) with an id from the file table. Coarse (byte scan, not a full
disassembly): an aligned hit on a real id is almost always the op.

    python -X utf8 tools/loadgraph.py
"""
import glob
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))
from filetable import entries  # noqa: E402

ids = {ident & 0xFFFF: name.split("\\")[1].split(".")[0].strip().upper() for _, name, ident in entries(
    "work/disc/tree/SLPS_033.53")}
files = sorted(glob.glob("work/pac/**/*.bin", recursive=True)) + sorted(glob.glob("work/disc/tree/DATA/*.PRG")) + [
    "work/disc/tree/SLPS_033.53"]
for f in files:
    d = open(f, "rb").read()
    hits = []
    for i in range(0, len(d) - 4, 2):
        if d[i] == 3 and d[i + 1] == 0:
            (v,) = struct.unpack_from("<H", d, i + 2)
            if v in ids:
                hits.append(f"{i:x}:{ids[v]}")
    if hits:
        print(os.path.relpath(f, "work").replace("\\", "/"), " ".join(hits))
