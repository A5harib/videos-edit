"""Render one reel from a job folder.

    render.py <job_dir> <vid> [--preview SECONDS]

Reads <job_dir>/job.json (see init_job.py) plus, for the video being rendered:
    cards/<vid>.html   stacked .card elements, numbered from 0 in page order
    caps/<vid>.tsv     caption chunks: start<TAB>end<TAB>text
    tr_fix/<vid>.json  corrected word timings (falls back to tr/<vid>.json)

Output is 1080x1920 (or 1920x1080 with "landscape": true), 30 fps, H.264 (Main, no B-frames) + AAC at about -14 LUFS:
full-frame speaker, a small card floating over the bottom area, word-highlight
captions above it.
--preview writes <job_dir>/preview_<vid>.mp4 instead of the real output.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
BROWSERS = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]

CELL_W, CELL_H = 1080, 680        # one card plus its shadow margin in the screenshot
SCALE = 0.72                      # card size on screen; small enough that the video shows around it
CELL_X, CELL_Y = 151, 1151        # card sits at about y=1180..1612, clear of Instagram's bottom UI
# "landscape": true in job.json -> 1920x1080 for YouTube, card on the right, captions at the bottom
LAND_SCALE, LAND_X, LAND_Y = 0.56, 1275, 190
FADE = 0.3


def render_cards(vid):
    html = Path("cards") / f"{vid}.html"
    n = html.read_text(encoding="utf-8").count('class="card')
    png = Path("cards") / f"{vid}.png"
    browser = next(b for b in BROWSERS if Path(b).exists())
    subprocess.run([browser, "--headless=old", "--disable-gpu", "--hide-scrollbars",
                    "--default-background-color=00000000", f"--window-size={CELL_W},{CELL_H * n}",
                    f"--screenshot={png.resolve()}", html.resolve().as_uri()], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return png, n


def build(job, vid, preview=None):
    os.chdir(job)                 # the filter graph uses relative paths (no drive-letter colons)
    spec = json.loads(Path("job.json").read_text(encoding="utf-8"))
    v = spec["videos"][vid]
    t0, t1 = v["trim"]
    dur = t1 - t0 if preview is None else min(preview, t1 - t0)
    cards_png, n_cards = render_cards(vid)
    words = f"tr_fix/{vid}.json" if Path(f"tr_fix/{vid}.json").exists() else f"tr/{vid}.json"
    land = spec.get("landscape", False)
    fontsize = v.get("fontsize", spec.get("fontsize", None))
    fs_args = ["--fontsize", str(fontsize)] if fontsize else []
    subprocess.run([sys.executable, str(SCRIPTS / "captions.py"), "ass", f"caps/{vid}.tsv", words,
                    f"caps/{vid}.ass", "--offset", str(t0)] + (["--landscape"] if land else []) + fs_args, check=True)

    tl = [(max(0.0, s - t0), idx) for s, idx in v["timeline"]]
    assert all(idx < n_cards for _, idx in tl), f"timeline uses a card index >= {n_cards}"
    n = len(tl)
    W, H = (1920, 1080) if land else (1080, 1920)
    scale, cx, cy = (LAND_SCALE, LAND_X, LAND_Y) if land else (SCALE, CELL_X, CELL_Y)
    w, h = round(CELL_W * scale), round(CELL_H * scale)
    flip = "hflip," if v.get("hflip", spec.get("hflip")) else ""
    # "transpose": 2 in job.json turns footage that was saved sideways upright (1 = clockwise)
    if spec.get("transpose"):
        flip = f"transpose={spec['transpose']}," + flip
    g = [f"[0:v]{flip}scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},"
         f"unsharp=5:5:0.5:5:5:0.0,setsar=1[base0]"]
    last = "base0"
    if n:
        g.append(f"[1:v]format=rgba,split={n}" + "".join(f"[s{i}]" for i in range(n)))
    for i, (start, idx) in enumerate(tl):
        end = tl[i + 1][0] + FADE if i + 1 < n else dur + 1
        g.append(f"[s{i}]crop={CELL_W}:{CELL_H}:0:{CELL_H * idx},scale={w}:{h}:flags=lanczos,"
                 f"fade=t=in:st={start:.2f}:d={FADE}:alpha=1[c{i}]")
        # slow bob so the card reads as floating, plus a small rise as each card arrives
        y = f"{cy}+5*sin(2*PI*t/4.5)+26*pow(1-min(1,max(0,(t-{start:.2f})/{FADE})),2)"
        g.append(f"[{last}][c{i}]overlay=x={cx}:y='{y}':enable='between(t,{start:.2f},{end:.2f})'[base{i + 1}]")
        last = f"base{i + 1}"
    g.append(f"[{last}]subtitles=caps/{vid}.ass:fontsdir=fonts,format=yuv420p[vout]")
    g.append("[0:a]highpass=f=80,afftdn=nf=-28,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")

    out_dir = Path(spec["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / v["out"] if preview is None else Path(f"preview_{vid}.mp4")
    graph = f"graph_{vid}.txt"
    Path(graph).write_text(";\n".join(g), encoding="utf-8")
    cmd = ["ffmpeg", "-v", "error", "-y",
           "-ss", str(t0), "-t", str(dur), "-i", str(Path(spec["src_dir"]) / v["src"]),
           "-loop", "1", "-framerate", "30", "-t", str(dur), "-i", str(cards_png),
           "-/filter_complex", graph, "-map", "[vout]", "-map", "[aout]",
           # plain encode on purpose: Main profile, no B-frames, a keyframe every second.
           # Phone apps re-render the file when the user adds text in their editor, and a
           # long-GOP High-profile file gave "Couldn't export video" there.
           "-c:v", "libx264", "-preset", "faster", "-crf", "19", "-profile:v", "main", "-level", "4.0",
           "-bf", "0", "-g", "30", "-keyint_min", "30", "-sc_threshold", "0",
           "-r", "30", "-pix_fmt", "yuv420p",
           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
           "-video_track_timescale", "30000",
           "-c:a", "aac", "-b:a", "192k", "-ac", "2",
           "-brand", "mp42", "-movflags", "+faststart", "-t", str(dur), str(out)]
    subprocess.run(cmd, check=True)
    print("wrote", out)


if __name__ == "__main__":
    a = sys.argv[1:]
    prev = float(a[a.index("--preview") + 1]) if "--preview" in a else None
    build(a[0], a[1], prev)
