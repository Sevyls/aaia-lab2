"""Assemble the final demo: slides plus live VHS clips, each with Kokoro narration, 4:00 total.

Usage: make_demo.py OUT.mp4   (run make_slides.py and the tapes in video/tapes/ first)
A live clip longer than its slot is sped up; a shorter one is slowed (down to 0.5x), then holds its last frame.
"""
import subprocess
import sys
from pathlib import Path

from make_audio import NARRATION
from tts import duration, narrate

HERE = Path(__file__).parent
WORK = HERE / "demo"

LIVE_BASELINE = (
    "Now the live part. Pricing is reset to the baseline commit, and the student regression runs against it. "
    "Zero point three three five times three should round half up to one point zero one, "
    "but the original code returns one point zero zero five, so the test fails."
)
LIVE_RUN = (
    "This is a live run of the agent with Qwen 3 8 B through local Ollama. "
    "Every request on screen is a native tool call with its own call identifier. "
    "The model reads the business rules, then the acceptance tests, then pricing dot p y, "
    "and each tool message returns the file content to the model. "
    "Next it requests edit pricing, with the exact baseline text as old and a complete replacement as new. "
    "The tool confirms one update to orders pricing dot p y. "
    "The model then asks to run the fixed test command. The tool prints the exact command and working directory "
    "and waits for approval. In this recording, the yes is typed by the recording script, as noted on screen. "
    "The observation reports exit code zero, with all ten tests passing, including the student regression. "
    "The model claims success, but the verify node decides: tests passed after the latest edit, "
    "so the run is verified, and the process exits with code zero."
)
LIVE_VERIFY = (
    "Independent verification happens outside the agent. The diff shows the model's pricing change against the baseline. "
    "Running the suite directly passes all ten tests, and the protected file diff is empty. "
    "Next, the failure boundaries: reading a path outside the service root is rejected as traversal, "
    "and replacing the word Decimal is rejected because it occurs more than once. "
    "Finally, a read-only run. Here the model answered directly, without any tool call, "
    "so there is no passing test after an edit. The verify node returns incomplete, "
    "and the process exits with code two. A final reply alone cannot verify completion."
)

SEGMENTS = [  # (source relative to video/, seconds, narration)
    ("slides/slide1.png", 30, NARRATION[0]),
    ("slides/slide2.png", 30, NARRATION[1]),
    ("clips/1-baseline.mp4", 20, LIVE_BASELINE),
    ("clips/2-live.mp4", 80, LIVE_RUN),
    ("clips/3-verify.mp4", 50, LIVE_VERIFY),
    ("slides/slide8.png", 30, NARRATION[7]),
]


def segment(n, src, seconds, text):
    wav, out = WORK / f"seg{n}.wav", WORK / f"seg{n}.mp4"
    print(f"segment {n}: narration {narrate(text, wav, seconds):.1f}s / {seconds}s")
    if src.suffix == ".png":
        video = ["-loop", "1", "-framerate", "30", "-i", str(src)]
        vf = "fps=30,format=yuv420p"
    else:
        speed = max(duration(src) / seconds, 0.5)
        print(f"segment {n}: {src.name} {duration(src):.1f}s played at {speed:.2f}x")
        video = ["-i", str(src)]
        vf = f"setpts=PTS/{speed},tpad=stop_mode=clone:stop_duration={seconds},fps=30,scale=1920:1080,format=yuv420p"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *video, "-i", str(wav), "-map", "0:v", "-map", "1:a",
                    "-vf", vf, "-t", str(seconds), "-c:v", "libx264", "-tune", "stillimage",
                    "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "1", str(out)], check=True)
    return out


if __name__ == "__main__":
    WORK.mkdir(exist_ok=True)
    parts = [segment(n, HERE / src, s, text) for n, (src, s, text) in enumerate(SEGMENTS, 1)]
    listing = WORK / "list.txt"
    listing.write_text("".join(f"file '{p}'\n" for p in parts))
    out = Path(sys.argv[1])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-c", "copy", str(out)], check=True)
    print(out, f"{duration(out):.1f}s")
