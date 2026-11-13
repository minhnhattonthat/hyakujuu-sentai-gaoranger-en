"""pac.py: GaoRanger PAC containers ("add" archives, "lzs" blocks). See docs/re/pac.md.

    python tools/pac.py list FILE.PAC            # tree of entries: offset, size, kind (+ unpacked size for lzs)
    python tools/pac.py unpack FILE.PAC OUTDIR   # every leaf as OUTDIR/<i>[_<j>..].bin (lzs blocks decompressed)
"""
import os
import struct
import sys


def kind(d, off):
    m = d[off:off + 4]
    if m == b"add\0":
        return "add"
    if m == b"lzs\0":
        return "lzs"
    if m == b"\x10\0\0\0":
        return "tim"
    return m.hex()


def add_entries(d, off):
    """add header: magic, u32 4, u32 0x20 (entry table offset), u32 count, u32 0x10 (entry size);
    entries are (u32 offset relative to this add, u32 size, 0, 0). Zero-size entries are empty slots."""
    _, ver, tab, count, esz = struct.unpack_from("<4sIIII", d, off)
    out = []
    for i in range(count):
        o, s = struct.unpack_from("<II", d, off + tab + i * esz)
        out.append((i, off + o, s))
    return out


def lzs_header(d, off):
    """lzs block (EXE 0x8002f628 checks, 0x8002f700 decodes): "lzs\\0", u32 0, u32 1, pad to 0x20; then at +0x20:
    u16 3, u16 hdrlen (0x18), u32 unpacked size, u16 flag bits (8/16/32), u16 length bits (2..7),
    u32 packed size of the whole block, 8-byte name; stream at +0x20+hdrlen."""
    assert d[off:off + 4] == b"lzs\0" and struct.unpack_from("<I", d, off + 8)[0] == 1
    typ, hlen, usize, fbits, lbits, psize = struct.unpack_from("<HHIHHI", d, off + 0x20)
    assert typ == 3 and fbits in (8, 16, 32) and 2 <= lbits <= 7, (typ, fbits, lbits)
    return dict(hlen=hlen, usize=usize, fbits=fbits, lbits=lbits, psize=psize, name=d[off + 0x30:off + 0x38],
                data=off + 0x20 + hlen)


def lzs_decode(d, off):
    """Returns (unpacked bytes, end offset of the stream). Flag word little-endian, LSB first, 1 = literal byte;
    0 = big-endian u16: length = (w & ((1 << lbits) - 1)) + 3, distance back = w >> lbits."""
    h = lzs_header(d, off)
    p, n, fb, lb = h["data"], h["usize"], h["fbits"] // 8, h["lbits"]
    mask = (1 << lb) - 1
    out = bytearray()
    while len(out) < n:
        flags = int.from_bytes(d[p:p + fb], "little")
        p += fb
        for _ in range(fb * 8):
            if len(out) >= n:
                break
            if flags & 1:
                out.append(d[p])
                p += 1
            else:
                w = (d[p] << 8) | d[p + 1]
                p += 2
                ln, dist = (w & mask) + 3, w >> lb
                assert 0 < dist <= len(out), f"bad back-reference at {p - 2:#x}"
                for _ in range(ln):
                    out.append(out[-dist])
            flags >>= 1
    # the game copies whole runs even past usize (EXE subtracts length, no clamp); keep exact size
    return bytes(out[:n]), p


def walk(d, off, size, path=()):
    """Yields (path, offset, size, kind) for this node and every add descendant (not into lzs payloads)."""
    k = kind(d, off)
    yield path, off, size, k
    if k == "add":
        for i, o, s in add_entries(d, off):
            if s:
                yield from walk(d, o, s, path + (i,))


def main():
    cmd, f = sys.argv[1], sys.argv[2]
    d = open(f, "rb").read()
    for path, off, size, k in walk(d, 0, len(d)):
        name = "_".join(map(str, path)) or "root"
        if cmd == "list":
            extra = ""
            if k == "lzs":
                h = lzs_header(d, off)
                extra = f" -> {h['usize']:x} f{h['fbits']} l{h['lbits']} {h['name'].rstrip(bytes(1)).decode('ascii', 'replace')}"
            print(f"{'  ' * len(path)}{name:>8} {off:08x} {size:8x} {k}{extra}")
        elif cmd == "unpack" and k != "add":
            os.makedirs(sys.argv[3], exist_ok=True)
            blob = lzs_decode(d, off)[0] if k == "lzs" else d[off:off + size]
            open(os.path.join(sys.argv[3], name + ".bin"), "wb").write(blob)


if __name__ == "__main__":
    main()
