"""Put hand-written Roman Urdu onto a raw transcript, one line per caption line.

Usage: line_align.py <raw.tsv> <text.txt> <out.json>

Each text line takes the time span of the next raw .tsv line (as made by
captions.py dump). Within a line, words get the raw word times when the counts
match, otherwise the span is shared out by word length.
  -              skip one raw line (no caption)
  +S E text      insert a line with explicit times, without using a raw line
"""
import json
import sys
from pathlib import Path


def spread(text, s, e):
    toks = text.split()
    w = [len(t) + 1 for t in toks]
    total, acc, out = sum(w), 0.0, []
    for t, x in zip(toks, w):
        a = s + (e - s) * acc / total
        acc += x
        out.append({"w": t.replace("~", " "), "s": round(a, 2), "e": round(s + (e - s) * acc / total, 2)})
    return out


raw = [l.split("\t") for l in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines() if l.strip()]
lines = [l.strip() for l in Path(sys.argv[2]).read_text(encoding="utf-8").splitlines() if l.strip()]
words, i, prev_end = [], 0, 0.0
for l in lines:
    if l.startswith("+"):
        s, e, text = l[1:].split(None, 2)
        words += spread(text, float(s), float(e))
        continue
    s, e = float(raw[i][0]), float(raw[i][1])
    # Whisper lines can overlap; start each line where the last one ended so words stay in order
    s = min(max(s, prev_end), e - 0.1)
    prev_end = e
    i += 1
    if l != "-":
        words += spread(l, s, e)
if i != len(raw):
    print(f"WARNING: used {i} of {len(raw)} raw lines")
words.sort(key=lambda x: x["s"])
Path(sys.argv[3]).parent.mkdir(exist_ok=True)
Path(sys.argv[3]).write_text(json.dumps({"segments": [{"words": words}]}, ensure_ascii=False), encoding="utf-8")
print(f"{len(words)} words, {i}/{len(raw)} lines -> {sys.argv[3]}")
