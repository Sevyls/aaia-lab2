"""Narrate each slide with Kokoro (see tts.py), 30 s per slide, and mux onto the silent video.

Usage: make_audio.py SILENT.mp4 OUT.mp4
"""
import subprocess
import sys
from pathlib import Path

SECONDS = 30

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

if __name__ == "__main__":
    from tts import narrate

    silent, out = Path(sys.argv[1]), Path(sys.argv[2])
    work = Path(__file__).parent / "audio"
    work.mkdir(exist_ok=True)
    clips = []
    for n, text in enumerate(NARRATION, 1):
        fitted = work / f"n{n}.wav"
        print(f"slide {n}: {narrate(text, fitted, SECONDS):.1f}s")
        clips.append(fitted)
    listing = work / "list.txt"
    listing.write_text("".join(f"file '{c}'\n" for c in clips))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(silent), "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest",
                    str(out)], check=True)
    print(out)
