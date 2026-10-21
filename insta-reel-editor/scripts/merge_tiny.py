import sys
from pathlib import Path
# fold one-word captions shorter than 0.35 s into the caption before them
p = Path(sys.argv[1]); rows = [l.split("\t") for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
out = []
for r in rows:
    if out and len(r[2].split()) == 1 and float(r[1]) - float(r[0]) < 0.35:
        out[-1][1] = r[1]; out[-1][2] += " " + r[2]
    else:
        out.append(r)
p.write_text("\n".join("\t".join(r) for r in out) + "\n", encoding="utf-8")
print(len(rows), "->", len(out))
