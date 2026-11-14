"""PS1 STR (MDEC v2) video: list, decode, and re-encode frames (docs/re/fmv.md).

    python -X utf8 tools/strv.py info  XA/RB4.STR
    python -X utf8 tools/strv.py dump  XA/RB4.STR OUTDIR [--from N --to M] [--every K]
    python -X utf8 tools/strv.py check XA/RB4.STR      # decode -> re-encode every frame, bitstream must match

Files are the raw 2336-byte-sector form dumpsxiso writes (subheader + 2328). Video sectors are form 1
(submode 0x48): 32-byte STR header + 2016 bytes of frame data; mkpsxiso recomputes EDC/ECC when it builds the disc.
Frame data = 8-byte header (u16 mdec_words/2 rounded up to 32... see mdec_count, u16 0x3800, u16 qscale,
u16 version 2) + bitstream (u16 LE words, MSB first). Macroblocks run column by column; blocks Cr Cb Y1 Y2 Y3 Y4;
DC = 10-bit signed, AC = MPEG-1 dct_coeff_next VLC + sign, 000001 = escape (6-bit run, 10-bit level), 10 = EOB.
"""
import argparse
import os
import struct
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mkdisc  # noqa: E402

SECTOR = 2336
PAYLOAD = 2016
MAGIC = 0x80010160

# (code, run, level) for dct_coeff_next (MPEG-1 table B.14); a sign bit follows each code
VLC = """
11 0 1|011 1 1|0100 0 2|0101 2 1|00101 0 3|00111 3 1|00110 4 1|000110 1 2|000111 5 1|000101 6 1|000100 7 1|
0000110 0 4|0000100 2 2|0000111 8 1|0000101 9 1|00100110 0 5|00100001 0 6|00100101 1 3|00100100 3 2|00100111 10 1|
00100011 11 1|00100010 12 1|00100000 13 1|0000001010 0 7|0000001100 1 4|0000001011 2 3|0000001111 4 2|
0000001001 5 2|0000001110 14 1|0000001101 15 1|0000001000 16 1|000000011101 0 8|000000011000 0 9|
000000010011 0 10|000000010000 0 11|000000011011 1 5|000000010100 2 4|000000011100 3 3|000000010010 4 3|
000000011110 6 2|000000010101 7 2|000000010001 8 2|000000011111 17 1|000000011010 18 1|000000011001 19 1|
000000010111 20 1|000000010110 21 1|0000000011010 0 12|0000000011001 0 13|0000000011000 0 14|0000000010111 0 15|
0000000010110 1 6|0000000010101 1 7|0000000010100 2 5|0000000010011 3 4|0000000010010 5 3|0000000010001 9 2|
0000000010000 10 2|0000000011111 22 1|0000000011110 23 1|0000000011101 24 1|0000000011100 25 1|
0000000011011 26 1|00000000011111 0 16|00000000011110 0 17|00000000011101 0 18|00000000011100 0 19|
00000000011011 0 20|00000000011010 0 21|00000000011001 0 22|00000000011000 0 23|00000000010111 0 24|
00000000010110 0 25|00000000010101 0 26|00000000010100 0 27|00000000010011 0 28|00000000010010 0 29|
00000000010001 0 30|00000000010000 0 31|000000000011000 0 32|000000000010111 0 33|000000000010110 0 34|
000000000010101 0 35|000000000010100 0 36|000000000010011 0 37|000000000010010 0 38|000000000010001 0 39|
000000000010000 0 40|000000000011111 1 8|000000000011110 1 9|000000000011101 1 10|000000000011100 1 11|
000000000011011 1 12|000000000011010 1 13|000000000011001 1 14|0000000000010011 1 15|0000000000010010 1 16|
0000000000010001 1 17|0000000000010000 1 18|0000000000010100 6 3|0000000000011010 11 2|0000000000011001 12 2|
0000000000011000 13 2|0000000000010111 14 2|0000000000010110 15 2|0000000000010101 16 2|0000000000011111 27 1|
0000000000011110 28 1|0000000000011101 29 1|0000000000011100 30 1|0000000000011011 31 1
"""
DEC = {}
ENC = {}
for item in VLC.replace("\n", "").split("|"):
    code, run, lev = item.split()
    DEC[code] = (int(run), int(lev))
    ENC[(int(run), int(lev))] = code
ESC = "000001"
EOB = "10"
END = "0111111111"  # end of frame: DC field 0x1ff after the last block (MDEC 0xfe00)

ZIGZAG = [0, 1, 8, 16, 9, 2, 3, 10, 17, 24, 32, 25, 18, 11, 4, 5, 12, 19, 26, 33, 40, 48, 41, 34, 27, 20, 13, 6, 7, 14,
          21, 28, 35, 42, 49, 56, 57, 50, 43, 36, 29, 22, 15, 23, 30, 37, 44, 51, 58, 59, 52, 45, 38, 31, 39, 46, 53, 60,
          61, 54, 47, 55, 62, 63]
QTAB = [2, 16, 19, 22, 26, 27, 29, 34, 16, 16, 22, 24, 27, 29, 34, 37, 19, 22, 26, 27, 29, 34, 34, 38, 22, 22, 26, 27,
        29, 34, 37, 40, 22, 26, 27, 29, 32, 35, 40, 48, 26, 27, 29, 32, 35, 40, 48, 58, 26, 27, 29, 34, 38, 46, 56, 69,
        27, 29, 35, 38, 46, 56, 69, 83]  # natural (row-major) order
_C = np.array([[np.sqrt((1 if u == 0 else 2) / 8) * np.cos((2 * x + 1) * u * np.pi / 16) for x in range(8)]
               for u in range(8)])


# ---------- sectors and frames

def sectors(path):
    data = open(path, "rb").read()
    assert len(data) % SECTOR == 0, path
    return data


def frames(data):
    """[(frame_no, [sector index..], header dict)] in disc order; video sectors only."""
    out, cur = [], {}
    for i in range(len(data) // SECTOR):
        s = data[i * SECTOR:(i + 1) * SECTOR]
        if s[2] & 0x20 or struct.unpack_from("<I", s, 8)[0] != MAGIC:  # form 2 = XA audio
            continue
        chunk, nchunks, fno, size, w, h = struct.unpack_from("<HHIIHH", s, 12)
        if fno not in cur:
            cur[fno] = (fno, [None] * nchunks, dict(size=size, w=w, h=h))
            out.append(cur[fno])
        cur[fno][1][chunk] = i
    for fno, secs, hd in out:
        assert None not in secs, ("missing chunk", fno)
    return out


def frame_bytes(data, secs):
    """The frame's data, cut at the size its sector headers give (the slack after it is not always zero)."""
    size = struct.unpack_from("<I", data, secs[0] * SECTOR + 8 + 12)[0]
    return b"".join(data[i * SECTOR + 8 + 32:i * SECTOR + 8 + 32 + PAYLOAD] for i in secs)[:size]


# ---------- bitstream

def _bits(buf):
    words = np.frombuffer(buf[:len(buf) // 2 * 2], "<u2")
    return "".join(format(int(w), "016b") for w in words)


def parse(buf, w, h):
    """frame data -> (qscale, version, blocks) where blocks = [(dc, [(run, level)..])] in stream order."""
    _count, magic, q, ver = struct.unpack_from("<HHHH", buf, 0)
    assert magic == 0x3800 and ver == 2, (hex(magic), ver)
    bits = _bits(buf[8:])
    p, blocks = 0, []
    nblocks = ((w + 15) // 16) * ((h + 15) // 16) * 6
    for _ in range(nblocks):
        if "1" not in bits[p + 10:] and (bits.startswith(END, p) or "1" not in bits[p:]):
            break  # some OP0/RB0 frames stop a block early (the MDEC leaves it unwritten); to_rgb draws it flat
        dc = int(bits[p:p + 10], 2)
        dc -= 1024 if dc & 512 else 0
        p += 10
        acs = []
        while True:
            if "1" not in bits[p:]:
                p = len(bits)  # OP0 frame 394 stops mid-block: the outer test ends the frame
                break
            if bits.startswith(EOB, p):
                p += 2
                break
            if bits.startswith(ESC, p):
                run = int(bits[p + 6:p + 12], 2)
                lev = int(bits[p + 12:p + 22], 2)
                lev -= 1024 if lev & 512 else 0
                acs.append((run, lev))
                p += 22
                continue
            for n in range(2, 17):
                rl = DEC.get(bits[p:p + n])
                if rl:
                    break
            else:
                raise ValueError("bad vlc at bit %d" % p)
            p += n
            acs.append((rl[0], -rl[1] if bits[p] == "1" else rl[1]))
            p += 1
        blocks.append((dc, acs))
    return q, ver, blocks, p


def mdec_count(blocks, w=320, h=208):
    """The header's first u16, from the MDEC code count (each block: DC + one per AC + EOB; a block a truncated
    frame lacks still counts as DC + EOB)."""
    missing = ((w + 15) // 16) * ((h + 15) // 16) * 6 - len(blocks)
    n = sum(2 + len(a) for _, a in blocks) + 2 * missing
    return ((n + 1) // 2 + 31) & ~31


def emit(blocks):
    out = []
    for dc, acs in blocks:
        out.append(format(dc & 1023, "010b"))
        for run, lev in acs:
            code = ENC.get((run, abs(lev)))
            if code is None:
                out.append(ESC + format(run, "06b") + format(lev & 1023, "010b"))
            else:
                out.append(code + ("1" if lev < 0 else "0"))
        out.append(EOB)
    out.append(END)
    return "".join(out)


def pack(bits):
    bits += "0" * (-len(bits) % 16)
    return b"".join(struct.pack("<H", int(bits[i:i + 16], 2)) for i in range(0, len(bits), 16))


# ---------- pixels

def block_coeffs(dc, acs, q):
    c = np.zeros(64)
    c[0] = dc * QTAB[0]
    k = 0
    for run, lev in acs:
        k += run + 1
        if k > 63:
            break
        z = ZIGZAG[k]
        c[z] = lev * QTAB[z] * q / 8
    return c.reshape(8, 8)


def idct(c):
    return _C.T @ c @ _C


def to_rgb(blocks, q, w, h):
    mw, mh = (w + 15) // 16, (h + 15) // 16
    blocks = list(blocks) + [(0, [])] * (mw * mh * 6 - len(blocks))
    Y = np.zeros((mh * 16, mw * 16))
    Cb = np.zeros((mh * 8, mw * 8))
    Cr = np.zeros((mh * 8, mw * 8))
    i = 0
    for mx in range(mw):
        for my in range(mh):
            b = [idct(block_coeffs(*blocks[i + k], q)) for k in range(6)]
            i += 6
            Cr[my * 8:my * 8 + 8, mx * 8:mx * 8 + 8] = b[0]
            Cb[my * 8:my * 8 + 8, mx * 8:mx * 8 + 8] = b[1]
            y0, x0 = my * 16, mx * 16
            Y[y0:y0 + 8, x0:x0 + 8] = b[2]
            Y[y0:y0 + 8, x0 + 8:x0 + 16] = b[3]
            Y[y0 + 8:y0 + 16, x0:x0 + 8] = b[4]
            Y[y0 + 8:y0 + 16, x0 + 8:x0 + 16] = b[5]
    Cb = Cb.repeat(2, 0).repeat(2, 1)
    Cr = Cr.repeat(2, 0).repeat(2, 1)
    Y = Y + 128
    rgb = np.stack([Y + 1.402 * Cr, Y - 0.3437 * Cb - 0.7143 * Cr, Y + 1.772 * Cb], -1)
    return np.clip(rgb, 0, 255).astype(np.uint8)[:h, :w]


def fdct_quant(px, q, cut=63):
    """8x8 spatial block (Y-128 or chroma) -> (dc, [(run, level)]) at qscale q; zigzag coefficients past cut
    are dropped (to fit a frame's sectors)."""
    c = (_C @ px @ _C.T).reshape(64)
    dc = int(np.clip(round(c[0] / QTAB[0]), -512, 511))
    acs, run = [], 0
    for k in range(1, cut + 1):
        z = ZIGZAG[k]
        lev = int(np.clip(round(c[z] * 8 / (QTAB[z] * q)), -512, 511))
        if lev == 0:
            run += 1
        else:
            acs.append((run, lev))
            run = 0
    return dc, acs


def encode_mb(rgb16, q, cut=63):
    """16x16x3 RGB -> six blocks (Cr Cb Y1 Y2 Y3 Y4)."""
    f = rgb16.astype(float)
    R, G, B = f[..., 0], f[..., 1], f[..., 2]
    Y = 0.299 * R + 0.587 * G + 0.114 * B
    Cb = (B - Y) / 1.772
    Cr = (R - Y) / 1.402
    sub = lambda a: a.reshape(8, 2, 8, 2).mean((1, 3))
    Y = Y - 128
    return [fdct_quant(b, q, cut) for b in (sub(Cr), sub(Cb), Y[:8, :8], Y[:8, 8:], Y[8:, :8], Y[8:, 8:])]


# ---------- frame replace

def replace_blocks(data, secs, hd, blocks, q):
    """New sector bytes for a frame (same sectors) with these blocks at qscale q, or None if it does not fit."""
    body = pack(emit(blocks))
    buf = struct.pack("<HHHH", mdec_count(blocks), 0x3800, q, 2) + body
    cap = len(secs) * PAYLOAD
    if len(buf) > cap:
        return None
    size = (len(buf) + 3) & ~3
    buf = buf + bytes(cap - len(buf))
    out = {}
    for k, i in enumerate(secs):
        s = bytearray(data[i * SECTOR:(i + 1) * SECTOR])
        struct.pack_into("<I", s, 8 + 12, size)
        s[8 + 20:8 + 28] = buf[:8]
        s[8 + 32:8 + 32 + PAYLOAD] = buf[k * PAYLOAD:(k + 1) * PAYLOAD]
        full = bytearray(16) + s  # the dumped sectors carry real EDC/ECC: keep them valid
        mkdisc.fix_form1(full)
        out[i] = bytes(full[16:])
    return out


# ---------- CLI

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["info", "dump", "check"])
    ap.add_argument("str")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--from", dest="frm", type=int, default=0)
    ap.add_argument("--to", type=int, default=1 << 30)
    ap.add_argument("--every", type=int, default=1)
    a = ap.parse_args()
    data = sectors(a.str)
    fr = frames(data)
    if a.cmd == "info":
        print("%s: %d sectors, %d frames, %dx%d, first %d last %d" % (
            a.str, len(data) // SECTOR, len(fr), fr[0][2]["w"], fr[0][2]["h"], fr[0][0], fr[-1][0]))
        return 0
    if a.cmd == "dump":
        from PIL import Image
        os.makedirs(a.out, exist_ok=True)
        for fno, secs, hd in fr:
            if not (a.frm <= fno <= a.to) or (fno - a.frm) % a.every:
                continue
            q, _, blocks, _ = parse(frame_bytes(data, secs), hd["w"], hd["h"])
            Image.fromarray(to_rgb(blocks, q, hd["w"], hd["h"])).save(os.path.join(a.out, "f%05d.png" % fno))
        return 0
    bad = 0
    for fno, secs, hd in fr:
        buf = frame_bytes(data, secs)
        try:
            q, _, blocks, nbits = parse(buf, hd["w"], hd["h"])
        except ValueError as e:
            bad += 1
            print("frame %d: %s" % (fno, e))
            continue
        again = pack(emit(blocks))
        orig = buf[8:8 + len(again)]
        cnt = struct.unpack_from("<H", buf)[0]
        if again != orig or cnt != mdec_count(blocks):
            bad += 1
            print("frame %d: reencode %s, count %d vs %d" % (fno, "ok" if again == orig else "DIFF", cnt,
                                                              mdec_count(blocks)))
    print("%d frames, %d differ" % (len(fr), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
