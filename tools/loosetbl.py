"""loosetbl.py TABLE.bin: decode a string table, showing unknown bytes as [xx] (find new control codes).
    python -X utf8 tools/loosetbl.py work/pac/O_TITLE.PAC/1.bin"""
import struct, sys
sys.path.insert(0, "tools")
import make_tbl
CH = dict(make_tbl.entries())
d = open(sys.argv[1], "rb").read()
a, n = struct.unpack_from("<HH", d, 0)
offs = struct.unpack_from(f"<{n}H", d, 4)
print("a", a, "n", n, [hex(o) for o in offs])
for o in sorted(set(offs)):
    p, out = o, []
    while p < len(d) and len(out) < 200:
        b = d[p]
        if b == 0xFF:
            out.append("{end}"); p += 1; break
        if b in (0, 1) and p + 1 < len(d) and ((b << 8) | d[p + 1]) in CH:
            out.append(CH[(b << 8) | d[p + 1]]); p += 2; continue
        out.append(f"[{b:02x}]"); p += 1
    print(f"{o:04x}: " + "".join(out).replace("\n", "/"))
