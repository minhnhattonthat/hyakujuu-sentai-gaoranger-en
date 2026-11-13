"""patscan.py FILE TEXT [--widths 1,2] [--strides 1,2,4]: encoding-agnostic search by letter-equality pattern.

Finds runs where equal letters of TEXT have equal codes and different letters have different codes (any table).
Use 10+ letters with a few repeats. Prints offset, width, stride and the codes found (to seed a table)."""
import argparse
import struct


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("text")
    ap.add_argument("--widths", default="1,2")
    ap.add_argument("--strides", default="1,2,4")
    ap.add_argument("--max", type=int, default=20)
    a = ap.parse_args()
    d = open(a.file, "rb").read()
    t = a.text
    n = len(t)
    first = {}
    pat = [first.setdefault(c, i) for i, c in enumerate(t)]
    hits = 0
    for width in map(int, a.widths.split(",")):
        fmt = {1: "B", 2: "<H", 4: "<I"}[width]
        for stride in map(int, a.strides.split(",")):
            if stride < width:
                continue
            span = stride * (n - 1) + width
            for o in range(0, len(d) - span):
                v = [struct.unpack_from(fmt, d, o + k * stride)[0] for k in range(2)]
                if (v[0] == v[1]) != (pat[1] == 0):
                    continue
                vals = [struct.unpack_from(fmt, d, o + k * stride)[0] for k in range(n)]
                seen = {}
                ok = True
                for k, x in enumerate(vals):
                    j = seen.setdefault(x, k)
                    if j != pat[k]:
                        ok = False
                        break
                if ok:
                    print(f"{o:#010x} w{width} s{stride} " + " ".join(f"{c}={x:x}" for c, x in zip(t, vals)))
                    hits += 1
                    if hits >= a.max:
                        return


if __name__ == "__main__":
    main()
