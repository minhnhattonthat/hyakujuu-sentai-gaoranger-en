"""slotcalls.py: every call of the PAC slot getter 0x8002f8b8 (a0 = slot index, a1 = PAC) in the EXE and the PRGs,
with the index when a nearby `addiu/ori a0, zero, N` sets it (else "dyn": a register, e.g. a loop counter).
Used to show that no code asks for Y_TITLE slot 21 (the card table; docs/re/pac.md §Decode targets).

    python -X utf8 tools/slotcalls.py [--index 21]
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT / "work" / "disc" / "tree"
JAL = 0x0C000000 | (0x8002F8B8 >> 2 & 0x3FFFFFF)


def calls(d):
    """-> [(offset, index or None)]: the delay slot first, then up to 6 instructions back, until a0 is set."""
    out = []
    for o in range(0, len(d) - 7, 4):
        if struct.unpack_from("<I", d, o)[0] != JAL:
            continue
        idx = None
        for p in [o + 4] + list(range(o - 4, max(o - 28, -4), -4)):
            w = struct.unpack_from("<I", d, p)[0]
            if w >> 16 in (0x2404, 0x3404):  # addiu/ori a0, zero, imm
                idx = w & 0xFFFF
                break
            op = w >> 26
            if (w >> 16) & 0x1F == 4 and (8 <= op <= 15 or 32 <= op <= 38) or w >> 11 & 0x1F == 4 and op == 0:
                break  # something else writes a0 (ALU immediate, load, R-type): dynamic
            if op in (2, 3) or 4 <= op <= 7 or op == 1:
                break  # a jump or branch before it: a0 may come from another path
        out.append((o, idx))
    return out


if __name__ == "__main__":
    want = int(sys.argv[sys.argv.index("--index") + 1]) if "--index" in sys.argv else None
    files = [TREE / "SLPS_033.53"] + sorted((TREE / "DATA").glob("*.PRG"))
    hits = 0
    for f in files:
        cs = calls(f.read_bytes())
        idx = sorted({i for _, i in cs if i is not None})
        dyn = sum(1 for _, i in cs if i is None)
        print(f"{f.name}: {len(cs)} calls, constant indices {idx}, {dyn} dynamic")
        hits += sum(1 for _, i in cs if want is not None and i == want)
    if want is not None:
        print(f"index {want}: {hits} constant calls")
