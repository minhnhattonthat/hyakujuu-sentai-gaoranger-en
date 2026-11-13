"""relscan.py FILE WORD [--strides 1,2,4] : relative search in JIS kana order with any element stride/width.

Like relsearch.py but also tries 16/32-bit elements and strides (text kept as structs). Prints offset, stride,
width and the code of the first letter. Kana outside hiragana/katakana are not supported in WORD."""
import argparse
import struct


def jis(c):
    o = ord(c)
    if 0x3041 <= o <= 0x3093:
        return o - 0x3041
    if 0x30A1 <= o <= 0x30F6:
        return o - 0x30A1
    raise SystemExit(f"unsupported letter {c}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("word")
    ap.add_argument("--strides", default="1,2,4,8")
    a = ap.parse_args()
    d = open(a.file, "rb").read()
    want = [jis(c) for c in a.word]
    diffs = [w - want[0] for w in want]
    for width, fmt in ((1, "B"), (2, "<H"), (4, "<I")):
        for stride in map(int, a.strides.split(",")):
            if stride < width:
                continue
            span = stride * (len(want) - 1) + width
            for o in range(0, len(d) - span):
                b0 = struct.unpack_from(fmt, d, o)[0]
                ok = True
                for k in range(1, len(want)):
                    if struct.unpack_from(fmt, d, o + k * stride)[0] - b0 != diffs[k]:
                        ok = False
                        break
                if ok and b0 != struct.unpack_from(fmt, d, o + stride)[0] if len(want) > 1 else ok:
                    print(f"{o:#08x} width {width} stride {stride} first {b0:#x}")


if __name__ == "__main__":
    main()
