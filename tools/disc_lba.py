"""disc_lba.py BIN: list ISO9660 files of a MODE2/2352 disc image with LBA and size (stdlib only).
    python -X utf8 tools/disc_lba.py "rom/Hyakujuu Sentai GaoRanger (Japan).bin" """
import struct
import sys


def sector(f, lba):
    f.seek(lba * 2352 + 24)  # MODE2 form 1: 12 sync + 4 header + 8 subheader
    return f.read(2048)


def walk(f, lba, size, path=""):
    data = b"".join(sector(f, lba + i) for i in range((size + 2047) // 2048))
    p = 0
    while p < len(data):
        n = data[p]
        if n == 0:
            p = (p // 2048 + 1) * 2048
            continue
        ext, sz = struct.unpack_from("<I", data, p + 2)[0], struct.unpack_from("<I", data, p + 10)[0]
        flags, nl = data[p + 25], data[p + 32]
        name = data[p + 33:p + 33 + nl].decode("ascii", "replace")
        if name not in ("\0", "\1"):
            if flags & 2:
                yield from walk(f, ext, sz, path + name + "/")
            else:
                yield ext, sz, path + name.split(";")[0]
        p += n


if __name__ == "__main__":
    with open(sys.argv[1], "rb") as f:
        pvd = sector(f, 16)
        root = pvd[156:156 + 34]
        for ext, sz, name in sorted(walk(f, struct.unpack_from("<I", root, 2)[0], struct.unpack_from("<I", root, 10)[0])):
            print(f"{ext:7d} {sz:9d} {name}")
