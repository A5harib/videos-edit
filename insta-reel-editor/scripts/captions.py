"""Caption tooling.

  captions.py dump <whisper.json> <chunks.tsv>
      Split the word-level transcript into short caption chunks and write an
      editable file: start<TAB>end<TAB>text  (one caption per line).

  captions.py align <corrected.txt> <whisper.json> <fixed.json>
      Put hand-corrected text onto the transcript's word timings. Same token
      count maps word for word ('_' drops a word, '~' joins two in one slot);
      otherwise words are matched up and gaps spread evenly.

  captions.py ass <chunks.tsv> <whisper.json> <out.ass> [--offset S] [--landscape] [--size N]
      Build an ASS file with the active word highlighted. Word timing comes from
      the whisper words inside each chunk when the word count still matches the
      edited text, otherwise it is spread across the chunk by word length.
"""
import json
import sys
from pathlib import Path

MAX_CHARS = 18
MAX_WORDS = 4
GAP = 0.45          # a pause this long always starts a new caption
HOLD = 0.35         # how long a caption lingers after its last word
BREAK_AFTER = ".?!,;:"

WHITE = "&H00FFFFFF"
HILITE = "&H0038C8FF"   # BGR for #FFC838

HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Montserrat ExtraBold,66,&H00FFFFFF,&H00FFFFFF,&H00101010,&H96000000,0,0,0,0,100,100,0,0,1,6,2,2,60,60,772,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def load_words(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    words = []
    for seg in data["segments"]:
        for w in seg["words"]:
            text = w["w"].strip()
            if text:
                words.append({"w": text, "s": w["s"], "e": w["e"]})
    return words


def dump(whisper_json, out_tsv):
    words = load_words(whisper_json)
    chunks, cur = [], []
    for i, w in enumerate(words):
        if cur:
            length = len(" ".join(x["w"] for x in cur)) + 1 + len(w["w"])
            gap = w["s"] - cur[-1]["e"]
            if (length > MAX_CHARS or len(cur) >= MAX_WORDS or gap > GAP
                    or cur[-1]["w"][-1] in BREAK_AFTER):
                chunks.append(cur)
                cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    lines = [f"{c[0]['s']:.2f}\t{c[-1]['e']:.2f}\t{' '.join(x['w'] for x in c)}" for c in chunks]
    Path(out_tsv).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(words)} words -> {len(chunks)} captions -> {out_tsv}")


def align(text_path, whisper_json, out_json):
    """Put hand-corrected text onto the whisper word timings.

    Same token count -> word-for-word (used for the Roman Urdu transliteration);
    otherwise tokens are matched with difflib and gaps are spread evenly.
    '_' gives that slot's time to the previous word; '~' is a space inside one slot.
    """
    import difflib
    import re
    words = load_words(whisper_json)
    toks = Path(text_path).read_text(encoding="utf-8").split()
    timed = []
    if len(toks) == len(words):
        timed = [(t, w["s"], w["e"]) for t, w in zip(toks, words)]
    else:
        norm = lambda x: re.sub(r"[^a-z0-9]", "", x.lower())
        sm = difflib.SequenceMatcher(None, [norm(w["w"]) for w in words], [norm(t) for t in toks], autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                timed += [(toks[j1 + k], words[i1 + k]["s"], words[i1 + k]["e"]) for k in range(i2 - i1)]
            elif j2 > j1:
                a = words[i1]["s"] if i2 > i1 else (words[i1 - 1]["e"] if i1 else 0.0)
                b = words[i2 - 1]["e"] if i2 > i1 else (words[i1]["s"] if i1 < len(words) else a + 0.3)
                step = (b - a) / (j2 - j1)
                timed += [(toks[j1 + k], a + k * step, a + (k + 1) * step) for k in range(j2 - j1)]
        print(f"token count differs ({len(toks)} vs {len(words)}): aligned by matching")
    out = []
    for t, s, e in timed:
        if t == "_":
            if out:
                out[-1]["e"] = round(e, 2)
            continue
        out.append({"w": t.replace("~", " "), "s": round(s, 2), "e": round(e, 2)})
    Path(out_json).parent.mkdir(exist_ok=True)
    Path(out_json).write_text(json.dumps({"segments": [{"words": out}]}, ensure_ascii=False), encoding="utf-8")


def ts(t):
    t = max(0.0, t)
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def ass(chunks_tsv, whisper_json, out_ass, offset=0.0, landscape=False, size=None):
    words = load_words(whisper_json)
    chunks = []
    for line in Path(chunks_tsv).read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        s, e, text = line.split("\t", 2)
        chunks.append({"s": float(s), "e": float(e), "words": [w.rstrip(",.;:") for w in text.split()]})

    events, prev_end = [], 0.0
    for n, c in enumerate(chunks):
        src = [w for w in words if c["s"] - 0.01 <= w["s"] and w["e"] <= c["e"] + 0.01]
        if len(src) == len(c["words"]):
            starts = [w["s"] for w in src]
        else:
            weights = [len(w) + 1 for w in c["words"]]
            total, acc, starts = sum(weights), 0, []
            for wt in weights:
                starts.append(c["s"] + (c["e"] - c["s"]) * acc / total)
                acc += wt
        # Groq word times often overlap the next chunk. Clamp so only one caption is on screen at a time.
        first = max(starts[0], prev_end)
        nxt = chunks[n + 1]["s"] if n + 1 < len(chunks) else c["e"] + HOLD
        end = max(min(nxt, c["e"] + HOLD), first + 0.25)
        bounds, last = [], first
        for x in starts:
            last = min(max(x, last), end)
            bounds.append(last)
        bounds.append(end)
        prev_end = end
        for i in range(len(c["words"])):
            parts = []
            for j, w in enumerate(c["words"]):
                col = HILITE if j == i else WHITE
                parts.append(f"{{\\1c{col}&}}{w}")
            a, b = bounds[i] - offset, bounds[i + 1] - offset
            if b <= 0 or b - a < 0.01:
                continue
            events.append(f"Dialogue: 0,{ts(a)},{ts(b)},Cap,,0,0,0,,{' '.join(parts)}")
    header = HEADER
    if landscape:   # 1920x1080 frame, captions near the bottom edge
        header = header.replace("PlayResX: 1080\nPlayResY: 1920", "PlayResX: 1920\nPlayResY: 1080").replace(",772,1", ",70,1")
    if size:        # default 66; bigger captions need shorter chunks so they fit the width
        header = header.replace("Montserrat ExtraBold,66,", f"Montserrat ExtraBold,{size},")
        # thicker outline and shadow as the text grows, so it stays readable on bright backgrounds
        header = header.replace(",0,0,1,6,2,2,", f",0,0,1,{max(6, round(size * 0.095))},{max(2, round(size * 0.04))},2,")
    Path(out_ass).write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    print(f"{len(chunks)} captions, {len(events)} events -> {out_ass}")


if __name__ == "__main__":
    args = sys.argv[1:]
    off = 0.0
    if "--offset" in args:
        i = args.index("--offset")
        off = float(args[i + 1])
        del args[i:i + 2]
    size = None
    if "--size" in args:
        i = args.index("--size")
        size = int(args[i + 1])
        del args[i:i + 2]
    land = "--landscape" in args
    if land:
        args.remove("--landscape")
    if not args:
        sys.exit(__doc__)
    if args[0] == "dump":
        dump(args[1], args[2])
    elif args[0] == "align":
        align(args[1], args[2], args[3])
    elif args[0] == "ass":
        ass(args[1], args[2], args[3], off, land, size)
    else:
        sys.exit(__doc__)
