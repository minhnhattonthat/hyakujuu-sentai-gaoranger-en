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


def full_card():
    """Every block used by another game's one-block save (the game's "not enough free space" message)."""
    card = bytearray(blank_card())
    for n in range(1, 16):
        f = bytearray(128)
        f[:10] = b"\x51\0\0\0\0\x20\0\0\xff\xff"
        f[10:10 + 20] = b"BISLPS-00000FULL%04d" % n
        x = 0
        for b in f[:127]:
            x ^= b
        f[127] = x
        card[n * 128:(n + 1) * 128] = f
        card[n * 8192:n * 8192 + 4] = b"SC\x11\x01"  # block title frame: icon, 1 block
    return bytes(card)


def corrupt_card(src):
    """A copy of a card with one byte of the game's save data flipped (the game's "data is corrupted" message)."""
    card = bytearray(open(src, "rb").read())
    # block 1 data (savedone.mcd: header + 3 icon frames at 0x2000-0x21ff), then the game's record twice (0x8c bytes
    # each, u16 a5ae + "GAO-ranger MemoryCard ID" + progress): damage the progress bytes of both copies
    card[0x2250] ^= 0x02
    card[0x2250 + 0x8c] ^= 0x02
    return bytes(card)


if __name__ == "__main__":
    c = blank_card()
    assert len(c) == 131072 and c[:2] == b"MC" and c[127] == ord("M") ^ ord("C") and c[128] == 0xa0
    f = full_card()
    assert len(f) == 131072 and all(f[n * 128] == 0x51 for n in range(1, 16)) and f[15 * 8192:15 * 8192 + 2] == b"SC"
    if len(sys.argv) == 2:
        open(sys.argv[1], "wb").write(c)
