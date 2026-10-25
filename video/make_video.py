"""Encode slides/slideN.png (from make_slides.py) into a silent MP4, 30 s per slide. Usage: make_video.py OUT.mp4"""
import subprocess
import sys
from pathlib import Path

OUT = Path(sys.argv[1])
WORK = Path(__file__).parent / "slides"
SECONDS = 30

paths = sorted(WORK.glob("slide*.png"), key=lambda p: int(p.stem.removeprefix("slide")))
if not paths:
    raise SystemExit("no slides found; run make_slides.py first")
listing = WORK / "list.txt"
listing.write_text("".join(f"file '{p.resolve()}'\nduration {SECONDS}\n" for p in paths) + f"file '{paths[-1].resolve()}'\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
                "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-tune", "stillimage",
                "-t", str(SECONDS * len(paths)), str(OUT)], check=True)
print(OUT)
