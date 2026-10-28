"""Transcribe wav files with Groq's hosted Whisper, writing the same word-level JSON as transcribe.py.

Usage: groq_transcribe.py <out_dir> <wav> [<wav> ...] [--lang xx] [--model whisper-large-v3]

Reads GROQ_API_KEY from the environment or from a .env.local in the current folder.
"""
import json
import os
import sys
from pathlib import Path

import requests

URL = "https://api.groq.com/openai/v1/audio/transcriptions"


def api_key():
    if os.environ.get("GROQ_API_KEY"):
        return os.environ["GROQ_API_KEY"]
    env = Path(".env.local")
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("GROQ_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("GROQ_API_KEY not found in environment or .env.local")


def main():
    args = sys.argv[1:]
    opts = {"--lang": None, "--model": "whisper-large-v3"}
    for flag in list(opts):
        if flag in args:
            i = args.index(flag)
            opts[flag] = args[i + 1]
            del args[i:i + 2]
    out_dir, wavs = Path(args[0]), args[1:]
    out_dir.mkdir(parents=True, exist_ok=True)
    key = api_key()

    for wav in wavs:
        data = [
            ("model", opts["--model"]),
            ("response_format", "verbose_json"),
            ("timestamp_granularities[]", "word"),
            ("timestamp_granularities[]", "segment"),
            ("temperature", "0"),
        ]
        if opts["--lang"]:
            data.append(("language", opts["--lang"]))
        with open(wav, "rb") as f:
            r = requests.post(URL, headers={"Authorization": f"Bearer {key}"},
                              data=data, files={"file": (Path(wav).name, f, "audio/wav")},
                              timeout=600)
        if r.status_code != 200:
            sys.exit(f"{wav}: HTTP {r.status_code} {r.text[:500]}")
        res = r.json()

        # Groq returns words as one flat list; hand each to the segment its midpoint falls in
        words = res.get("words") or []
        segs = res.get("segments") or []
        out = {
            "file": wav,
            "language": res.get("language"),
            "language_probability": None,
            "duration": res.get("duration"),
            "segments": [],
        }
        wi = 0
        for k, s in enumerate(segs):
            end = segs[k + 1]["start"] if k + 1 < len(segs) else float("inf")
            seg_words = []
            while wi < len(words) and (words[wi]["start"] + words[wi]["end"]) / 2 < end:
                w = words[wi]
                seg_words.append({"w": " " + w["word"].strip(), "s": round(w["start"], 2), "e": round(w["end"], 2)})
                wi += 1
            out["segments"].append({
                "start": round(s["start"], 2),
                "end": round(s["end"], 2),
                "text": s["text"].strip(),
                "words": seg_words,
            })

        name = Path(wav).stem
        (out_dir / f"{name}.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"== {name} lang={out['language']}")
        for s in out["segments"]:
            print(f"[{s['start']:6.2f}-{s['end']:6.2f}] {s['text']}")
        sys.stdout.flush()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
