"""unpack_all.py: unpack every DATA/*.PAC of the dumped disc tree into work/pac/<PAC>/ and report leaf kinds.

    python -X utf8 tools/unpack_all.py [work/disc/tree]   (dump first: see docs/re/pac.md)
Fails if any lzs stream doesn't end inside its block (decoder self-check)."""
import collections
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import pac  # noqa: E402

tree = sys.argv[1] if len(sys.argv) > 1 else "work/disc/tree"
kinds = collections.Counter()
bad = 0
def unpack(f, d, outdir, prefix=()):
    global bad
    for path, off, size, k in pac.walk(d, 0, len(d), prefix):
        if k == "add":
            continue
        name = "_".join(map(str, path)) or "root"
        if k == "lzs":
            blob, end = pac.lzs_decode(d, off)
            if not (off + size - 0x100 <= end <= off + size):
                print(f"{f} {name}: stream ends {end - off:#x} of {size:#x}")
                bad += 1
            k = "lzs:" + pac.kind(blob, 0)
            if blob[:4] == b"add\0":  # compressed archive: unpack its leaves too, path continues with "z"
                kinds[k] += 1
                unpack(f, blob, outdir, path + ("z",))
                continue
        else:
            blob = d[off:off + size]
        kinds[k] += 1
        open(os.path.join(outdir, name + ".bin"), "wb").write(blob)


for f in sorted(glob.glob(os.path.join(tree, "DATA", "*.PAC"))):
    outdir = os.path.join("work", "pac", os.path.basename(f))
    os.makedirs(outdir, exist_ok=True)
    unpack(f, open(f, "rb").read(), outdir)
for k, n in kinds.most_common():
    print(f"{n:6d} {k}")
sys.exit(1 if bad else 0)
