#!/usr/bin/env bash
# Rebuild the demo videos in the lab root.
#   video/build.sh         slides, demo-silent.mp4, demo-narrated.mp4, and demo-final.mp4
#                          (demo-final is assembled from existing video/clips/; skipped if missing)
#   video/build.sh --live  first re-record the live clips with VHS. This runs qwen3:8b, resets
#                          target-service pricing to fed594c, and lets the agent repair it again.
# Needs python3.12 and ffmpeg; --live also needs vhs (brew install vhs) and Ollama with qwen3:8b.
# The Kokoro TTS model (~350 MB) is downloaded into the git-ignored video/kokoro/ on first run.
set -euo pipefail
cd "$(dirname "$0")"
PRICING=target-service/orders/pricing.py

if [ "${1:-}" = "--live" ]; then
  command -v vhs >/dev/null || { echo "vhs not found: brew install vhs" >&2; exit 1; }
  (cd .. && git diff --quiet HEAD -- "$PRICING") ||
    { echo "$PRICING has uncommitted changes; commit or stash them before --live" >&2; exit 1; }
fi

[ -x .venv/bin/python ] || python3.12 -m venv .venv
.venv/bin/python -m pip install -q -r requirements.txt

.venv/bin/python make_slides.py          # slides.toml -> slides/slideN.png
.venv/bin/python make_video.py ../demo-silent.mp4
.venv/bin/python make_audio.py ../demo-silent.mp4 ../demo-narrated.mp4

if [ "${1:-}" = "--live" ]; then
  (
    cd ..
    for t in 1-baseline 2-live 3-verify; do vhs "video/tapes/$t.tape"; done
    git reset -q -- "$PRICING"   # the baseline tape stages fed594c pricing; keep the agent's edit unstaged
    git diff --quiet HEAD -- "$PRICING" ||
      echo "note: the agent's new $PRICING differs from the committed repair; review git diff" >&2
  )
fi

if [ -f clips/1-baseline.mp4 ] && [ -f clips/2-live.mp4 ] && [ -f clips/3-verify.mp4 ]; then
  .venv/bin/python make_demo.py ../demo-final.mp4
else
  echo "skipping demo-final.mp4: live clips missing in video/clips/ (run with --live)" >&2
fi
