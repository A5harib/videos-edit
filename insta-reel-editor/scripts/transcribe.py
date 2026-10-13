"""Transcribe wav files with faster-whisper, writing word-level JSON per file.

Usage: transcribe.py <model> <out_dir> <wav> [<wav> ...] [--lang xx]
"""
import json
import sys
import wave
from pathlib import Path

import numpy as np

from faster_whisper import WhisperModel


def load_wav(path):
    # 16 kHz mono s16 wav -> float32 array; avoids faster-whisper's PyAV decoder
    with wave.open(path, "rb") as f:
        assert f.getframerate() == 16000 and f.getnchannels() == 1 and f.getsampwidth() == 2
        pcm = f.readframes(f.getnframes())
    return np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0


def main():
    args = sys.argv[1:]
    lang = None
    if "--lang" in args:
        i = args.index("--lang")
        lang = args[i + 1]
        del args[i:i + 2]
    model_name, out_dir, wavs = args[0], Path(args[1]), args[2:]
    out_dir.mkdir(parents=True, exist_ok=True)

    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    for wav in wavs:
        segments, info = model.transcribe(
            load_wav(wav),
            language=lang,
            word_timestamps=True,
            vad_filter=True,
            beam_size=5,
        )
        out = {
            "file": wav,
            "language": info.language,
            "language_probability": round(info.language_probability, 3),
            "duration": info.duration,
            "segments": [],
        }
        for s in segments:
            out["segments"].append({
                "start": round(s.start, 2),
                "end": round(s.end, 2),
                "text": s.text.strip(),
                "words": [
                    {"w": w.word, "s": round(w.start, 2), "e": round(w.end, 2)}
                    for w in (s.words or [])
                ],
            })
        name = Path(wav).stem
        (out_dir / f"{name}.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"== {name} lang={info.language} p={info.language_probability:.2f}")
        for s in out["segments"]:
            print(f"[{s['start']:6.2f}-{s['end']:6.2f}] {s['text']}")
        sys.stdout.flush()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
