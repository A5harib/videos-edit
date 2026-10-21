"""Set up a job folder for a batch of talking-head videos.

    init_job.py <job_dir> <source_dir>

Creates in <job_dir>:
    audio/vN.wav       16 kHz mono audio for transcription
    frames/vN.jpg      contact sheet (one frame every 6 s) to see what the video looks like
    cards/imgN.<ext>   copies of the supplied images, plus cards.css
    fonts/             caption fonts
    job.json           one entry per video, ready for the timeline to be filled in
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
VIDEO_EXT = {".mp4", ".mov", ".m4v"}
IMAGE_EXT = {".jpg", ".jpeg", ".png"}


def probe(path, entries):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", entries,
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout.strip()
    return out


def main():
    job, src = Path(sys.argv[1]), Path(sys.argv[2]).resolve()   # absolute, since render.py runs from the job folder
    for d in ("audio", "frames", "cards", "caps", "tr", "fonts"):
        (job / d).mkdir(parents=True, exist_ok=True)
    shutil.copy(SKILL / "assets" / "cards.css", job / "cards" / "cards.css")
    for f in (SKILL / "assets" / "fonts").glob("*.ttf"):
        shutil.copy(f, job / "fonts" / f.name)

    videos = sorted(p for p in src.iterdir() if p.suffix.lower() in VIDEO_EXT)
    images = sorted(p for p in src.iterdir() if p.suffix.lower() in IMAGE_EXT)
    spec = {"src_dir": str(src), "out_dir": str(src / "instagram"), "hflip": False, "videos": {}}

    for i, v in enumerate(videos, 1):
        vid = f"v{i}"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(v), "-vn", "-ac", "1", "-ar", "16000",
                        str(job / "audio" / f"{vid}.wav")], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(v), "-vf", "fps=1/6,scale=240:-1,tile=5x4",
                        "-frames:v", "1", str(job / "frames" / f"{vid}.jpg")], check=True)
        dur = float(probe(v, "format=duration"))
        size = probe(v, "stream=width,height")
        spec["videos"][vid] = {"src": v.name, "out": f"{i} - TITLE.mp4",
                               "trim": [0.0, round(dur - 0.05, 2)], "timeline": []}
        print(f"{vid}  {dur:6.1f}s  {size}  {v.name}")

    for i, img in enumerate(images, 1):
        dst = job / "cards" / f"img{i}{img.suffix.lower()}"
        shutil.copy(img, dst)
        print(f"{dst.name}  {probe(img, 'stream=width,height')}  {img.name}")

    (job / "job.json").write_text(json.dumps(spec, indent=1), encoding="utf-8")
    print("wrote", job / "job.json")


if __name__ == "__main__":
    main()
