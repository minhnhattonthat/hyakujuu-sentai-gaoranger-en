"""xawav.py: XA audio of an STR/XA file (dumpsxiso's 2336-byte sectors) to one WAV per channel, via ffmpeg.

    python -X utf8 tools/xawav.py work/disc/tree/XA/RB0.STR [..] --out work/subs/audio [--rate 16000]

ffmpeg's psxstr demuxer wants raw 2352-byte sectors, so each sector gets a sync + mode-2 header back
(MSF is fake; ffmpeg ignores it). Writes <out>/<NAME>_c<channel>.wav (mono at --rate, for transcription).
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

SYNC = b"\x00" + b"\xff" * 10 + b"\x00"


def to_raw(data):
    n = len(data) // 2336
    assert len(data) == n * 2336, "not 2336-byte sectors"
    out = bytearray()
    for i in range(n):
        out += SYNC + bytes([0, 2, 0, 2]) + data[i * 2336:(i + 1) * 2336]
    return bytes(out)


def channels(data):
    """XA audio channels present (subheader byte 1, submode bit 2 = audio)."""
    return sorted({data[i * 2336 + 1] for i in range(len(data) // 2336) if data[i * 2336 + 2] & 4})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--rate", type=int, default=16000)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for f in map(Path, a.files):
        data = f.read_bytes()
        for ch in channels(data):
            # keep only this channel's audio sectors (ffmpeg mixes channels otherwise)
            keep = b"".join(data[i * 2336:(i + 1) * 2336] for i in range(len(data) // 2336)
                            if data[i * 2336 + 2] & 4 and data[i * 2336 + 1] == ch)
            with tempfile.NamedTemporaryFile(suffix=".str", delete=False) as t:
                t.write(to_raw(keep))
            wav = out / f"{f.stem}_c{ch}.wav"
            r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "psxstr", "-i", t.name, "-vn", "-ac", "1",
                                "-ar", str(a.rate), str(wav)], capture_output=True, text=True)
            Path(t.name).unlink()
            print(wav, "ok" if r.returncode == 0 else r.stderr.strip()[:200])


if __name__ == "__main__":
    main()
