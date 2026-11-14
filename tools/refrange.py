"""refrange.py: list code in the EXE / PRG overlays that builds an address inside [LO, HI) (lui + addiu/ori/load/store
pairs within 16 instructions, and raw pointer words). Used to prove an EXE gap is free before putting data there.

    python -X utf8 tools/refrange.py LO HI
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT / "work" / "disc" / "tree"


def images():
    exe = (TREE / "SLPS_033.53").read_bytes()
    yield "EXE", exe[0x800:], struct.unpack_from("<I", exe, 0x18)[0]
    for p in sorted((TREE / "DATA").glob("*.PRG")):
        yield p.name, p.read_bytes(), 0x800A6AE8  # overlay load address (docs/re/flow.md)


def refs(code, base, lo, hi):
    n = len(code) // 4
    words = struct.unpack_from(f"<{n}I", code)
    for i, w in enumerate(words):
        if lo <= w < hi:
            yield base + 4 * i, "word", w
        if w >> 26 != 0x0F:  # lui
            continue
        rt, hi16 = (w >> 16) & 31, w & 0xFFFF
        for j in range(i + 1, min(i + 17, n)):
            x = words[j]
            op, rs = x >> 26, (x >> 21) & 31
            if rs == rt and op in (0x08, 0x09, 0x0D, 0x20, 0x21, 0x23, 0x24, 0x25, 0x28, 0x29, 0x2B):
                imm = x & 0xFFFF
                a = (hi16 << 16) + (imm if op == 0x0D else (imm - 0x10000 if imm & 0x8000 else imm))
                if lo <= (a & 0xFFFFFFFF) < hi:
                    yield base + 4 * j, "pair", a & 0xFFFFFFFF
            if op in (0x0F,) and ((x >> 16) & 31) == rt:
                break  # rt redefined


if __name__ == "__main__":
    lo, hi = int(sys.argv[1], 16), int(sys.argv[2], 16)
    total = 0
    for name, code, base in images():
        for pc, kind, a in refs(code, base, lo, hi):
            print(f"{name:12} {pc:08x} {kind} {a:08x}")
            total += 1
    print(total, "references")
