"""Contact sheet of evenly spaced frames, for checking a rendered reel by eye.

    sheet.py <video> <out.jpg> [frames=12]
"""
import subprocess
import sys

video, out = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 12
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video],
                           capture_output=True, text=True).stdout)
cols = min(n, 6)
rows = -(-n // cols)
# first frame at 3 s so the intro (which should have no card) is always included
step = max(0.1, (dur - 4) / max(1, n - 1))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "3", "-i", video,
                "-vf", f"fps=1/{step:.3f},scale=320:-1,tile={cols}x{rows}", "-frames:v", "1", out], check=True)
print("wrote", out)
