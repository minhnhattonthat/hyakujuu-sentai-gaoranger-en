"""Find a hex byte string in the disc tree and in every unpacked PAC leaf.

    python -X utf8 tools/binfind.py "03 00 10 50 10 00" [more hex strings...]
"""
import glob
import sys

files = glob.glob("work/disc/tree/**/*.*", recursive=True) + glob.glob("work/pac/**/*.bin", recursive=True)
for pat in sys.argv[1:]:
    b = bytes.fromhex(pat)
    for f in files:
        if f.endswith((".STR", ".XA", ".WAV")):
            continue
        d = open(f, "rb").read()
        i = d.find(b)
        while i >= 0:
            print(pat, f, hex(i))
            i = d.find(b, i + 1)
