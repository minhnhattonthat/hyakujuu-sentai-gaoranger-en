"""stepdown.py DIR [--max-start N]: u16 RAM values (ram_*.bin dumps from probes/ramdump.lua) that never go up,
drop at least twice and stay put in between: a health value under occasional hits (ramsearch.py's `dec` needs a
drop at every step). Prints address and the value per dump.
"""
import argparse
import glob
import os

import numpy as np

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("dir")
ap.add_argument("--max-start", type=int, default=2000)
ap.add_argument("--max", type=int, default=40)
a = ap.parse_args()
files = sorted(glob.glob(os.path.join(a.dir, "ram_*.bin")))
v = np.stack([np.frombuffer(open(f, "rb").read(), "<u2") for f in files]).astype(np.int32)
d = np.diff(v, axis=0)
ok = (d <= 0).all(0) & ((d < 0).sum(0) >= 2) & ((d == 0).sum(0) >= 2) & (v[0] <= a.max_start) & (v[-1] < v[0])
idx = np.nonzero(ok)[0]
print(len(idx), "candidates")
for i in idx[:a.max]:
    print(f"{0x80000000 + 2 * i:08X}", " ".join(str(x) for x in v[:, i]))
