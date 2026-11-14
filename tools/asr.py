"""asr.py: transcribe voice WAVs (tools/xawav.py output) with faster-whisper -> one TSV of timed Japanese lines.

    tools/asr/Scripts/python -X utf8 tools/asr.py work/subs/audio/*.wav --out work/subs/asr.tsv [--model large-v3]

Setup (once, gitignored venv): python -m venv tools/asr && tools/asr/Scripts/python -m pip install faster-whisper
nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*". Output rows: file<TAB>start s<TAB>end s<TAB>japanese. Whisper's text
is a draft: check every line by ear/context before translating (names especially).
"""
import argparse
import os
import sys
import wave
from pathlib import Path

import numpy as np

# CUDA DLLs from the nvidia-* wheels
for p in (Path(sys.prefix) / "Lib/site-packages/nvidia").glob("*/bin"):
    os.add_dll_directory(str(p))
    os.environ["PATH"] = str(p) + os.pathsep + os.environ["PATH"]

from faster_whisper import WhisperModel  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wavs", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--cpu", action="store_true")
    ap.add_argument("--no-vad", action="store_true", help="voice under loud music: VAD can drop it all")
    a = ap.parse_args()
    m = WhisperModel(a.model, device="cpu" if a.cpu else "cuda", compute_type="int8" if a.cpu else "float16")
    with open(a.out, "w", encoding="utf-8") as f:
        for w in a.wavs:
            with wave.open(w) as r:  # own decode: faster-whisper 1.2.1's PyAV call breaks on av 19
                assert r.getframerate() == 16000 and r.getnchannels() == 1 and r.getsampwidth() == 2, w
                pcm = np.frombuffer(r.readframes(r.getnframes()), "<i2").astype(np.float32) / 32768
            segs, _ = m.transcribe(pcm, language="ja", vad_filter=not a.no_vad, beam_size=5, word_timestamps=True)
            for s in segs:
                # segment times span leading/trailing music; the words' own times are the subtitle's
                t0, t1 = (s.words[0].start, s.words[-1].end) if s.words else (s.start, s.end)
                row = f"{Path(w).stem}\t{t0:.2f}\t{t1:.2f}\t{s.text.strip()}"
                print(row, flush=True)
                f.write(row + "\n")


if __name__ == "__main__":
    main()
