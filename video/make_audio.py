"""Narrate each slide with Kokoro (local neural TTS), fit each clip to 30 s, and mux onto the silent video."""
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

import espeakng_loader
import soundfile as sf
from kokoro_onnx import EspeakConfig, Kokoro

SILENT, OUT = Path(sys.argv[1]), Path(sys.argv[2])
HERE = Path(__file__).parent
WORK = HERE / "audio"
WORK.mkdir(exist_ok=True)
VOICE, SPEED, SECONDS = "af_heart", 1.0, 30
MODELS = HERE / "kokoro"
RELEASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
for name in ("kokoro-v1.0.onnx", "voices-v1.0.bin"):
    if not (MODELS / name).exists():
        MODELS.mkdir(exist_ok=True)
        print(f"downloading {name} ...")
        urllib.request.urlretrieve(f"{RELEASE}/{name}", MODELS / name)
# ponytail: espeak-ng truncates data paths at 160 bytes, so its data is copied to a short /tmp path.
ESPEAK_DATA = Path("/tmp/espeak-ng-data")
if not (ESPEAK_DATA / "phontab").exists():
    shutil.copytree(espeakng_loader.get_data_path(), ESPEAK_DATA, dirs_exist_ok=True)
TTS = Kokoro(str(MODELS / "kokoro-v1.0.onnx"), str(MODELS / "voices-v1.0.bin"),
             espeak_config=EspeakConfig(lib_path=espeakng_loader.get_library_path(),
                                        data_path=str(ESPEAK_DATA)))

NARRATION = [
    "This is the week two verified coding agent. LangGraph replaces the hand-written loop from week one. "
    "The model node sends the system instruction and message history to a local Qwen 3 8 B model and validates the reply. "
    "Native tool calls route to the tool node, which always returns to the model. "
    "A final response routes to an explicit verify node, then ends. The run is bounded by a limit of 32 graph steps.",

    "The verify node ignores the model's claim and walks the trusted tool messages in order. "
    "A successful pricing edit makes earlier test results stale. Each test run replaces the status: "
    "only exit code zero passes, while failures, denials, or errors clear it. "
    "Completion is verified only with a final answer and passing tests after the latest edit. "
    "Both the smoke and the workflow diagnostics pass.",

    "In the live run, Qwen 3 selected the tools itself. It requested read file for the business rules, "
    "then the acceptance tests, then pricing dot p y. Each request carries a call identifier, "
    "and the tool node answers with a linked tool message that goes back to the model for its next decision. "
    "Message text is never executed as a call.",

    "Next, the model requested edit pricing, replacing the exact baseline text in a single call. "
    "The tool answered: updated orders pricing dot p y once. The diff, reviewed before approval, "
    "rounds each line to cents with round half up, rounds the discount amount, subtracts it, "
    "and only then decides shipping from the discounted goods. The tool can write only this one file, "
    "and only for a unique match.",

    "The model then requested the fixed test command. The tool showed the exact command and working directory, "
    "and the human reviewer typed yes. The observation reported exit code zero: all ten tests passed, "
    "including the student regression. The model claimed success, but the run is verified only because "
    "passing tests followed the latest edit. The process exited with code zero.",

    "Independent verification happens outside the agent. Against the baseline commit, the student regression fails: "
    "zero point three three five times three should round to one point zero one, "
    "but the original code returns one point zero zero five. On the repaired service, all ten tests pass. "
    "The protected file diff is empty. Only pricing and the student regression changed.",

    "Failure boundaries. Reading a path outside the service root is rejected as traversal, "
    "and replacing the word Decimal is rejected because it occurs more than once. "
    "In the first live run, the test command was denied. The model only asked for approval, "
    "and the verify node returned incomplete, because the latest test run did not pass. "
    "A final reply alone cannot verify completion.",

    "What remains unverified. The tests cover specific cases, so correctness for other inputs is not proven. "
    "One verified run at temperature zero does not show reliability across runs. "
    "The tool checks are application policy, not an operating system sandbox, so the diff is reviewed "
    "before tests are approved. And a step limit stops work. It never proves a repair.",
]

clips = []
for n, text in enumerate(NARRATION, 1):
    raw, fitted = WORK / f"k{n}.wav", WORK / f"n{n}.wav"
    samples, rate = TTS.create(text, voice=VOICE, speed=SPEED, lang="en-us")
    sf.write(raw, samples, rate)
    length = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "csv=p=0", str(raw)], capture_output=True, text=True, check=True).stdout)
    print(f"slide {n}: {length:.1f}s")
    if length > SECONDS - 0.5:
        raise SystemExit(f"slide {n} narration too long ({length:.1f}s); shorten text or raise RATE")
    # 0.5 s lead-in, then pad with silence to exactly one slide length.
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af",
                    f"adelay=500:all=1,apad,atrim=0:{SECONDS}", "-ar", "48000", "-ac", "1", str(fitted)], check=True)
    clips.append(fitted)

listing = WORK / "list.txt"
listing.write_text("".join(f"file '{c}'\n" for c in clips))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(SILENT), "-f", "concat", "-safe", "0", "-i", str(listing),
                "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest",
                str(OUT)], check=True)
print(OUT)
