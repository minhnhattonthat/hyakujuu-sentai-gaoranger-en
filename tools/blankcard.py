"""Write a formatted, empty PS1 memory card image (128 KiB raw .mcd), for warp runs that must not share saves.

    python -X utf8 tools/blankcard.py OUT.mcd
"""
import sys


def blank_card():
    card = bytearray(128 * 1024)

    def frame(n, body):
        f = bytearray(128)
        f[:len(body)] = body
        x = 0
        for b in f[:127]:
            x ^= b
        f[127] = x
        card[n * 128:(n + 1) * 128] = f

    frame(0, b"MC")
    for n in range(1, 16):  # directory: free block, no next link
        frame(n, b"\xa0\0\0\0" + b"\0" * 4 + b"\xff\xff")
    for n in range(16, 36):  # broken-sector list: none
        frame(n, b"\xff\xff\xff\xff" + b"\0" * 4 + b"\xff\xff")
    frame(63, b"MC")
    return bytes(card)


if __name__ == "__main__":
    c = blank_card()
    assert len(c) == 131072 and c[:2] == b"MC" and c[127] == ord("M") ^ ord("C") and c[128] == 0xa0
    if len(sys.argv) == 2:
        open(sys.argv[1], "wb").write(c)
