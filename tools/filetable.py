"""List the EXE's file table: 0x2c-byte entries {u32 id, u32 lba, u32 size, char name[0x20]}, lba/size filled
at boot by a CD directory lookup (docs/re/disc.md). The loader 0x800345c4 gets a pointer to the lba field.

    python -X utf8 tools/filetable.py [work/disc/tree/SLPS_033.53]
"""
import struct
import sys

EXE_BASE = 0x80010000 - 0x800  # RAM address of file offset 0 (PS-X EXE header is 0x800 bytes)


def entries(exe):
    d = open(exe, "rb").read()
    i = d.find(b"DATA\\o_logo") - 12
    assert i > 0, "table not found"
    while True:
        name = d[i + 12:i + 0x2C].split(b"\0")[0]
        if not name.upper().startswith(b"DATA\\"):
            break
        (ident,) = struct.unpack_from("<I", d, i)
        yield EXE_BASE + i, name.decode("ascii"), ident
        i += 0x2C


if __name__ == "__main__":
    for addr, name, ident in entries(sys.argv[1] if len(sys.argv) > 1 else "work/disc/tree/SLPS_033.53"):
        print(f"{addr:08x} {ident:08x} {name}")
