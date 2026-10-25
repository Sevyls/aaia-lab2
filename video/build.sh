#!/usr/bin/env bash
# Rebuild demo-silent.mp4 and demo-narrated.mp4 in the lab root.
# Needs python3.12 and ffmpeg (with libx264). The Kokoro TTS model (~350 MB) is
# downloaded into video/kokoro/ on first run and is not tracked by git.
set -euo pipefail
cd "$(dirname "$0")"

[ -x .venv/bin/python ] || python3.12 -m venv .venv
.venv/bin/python -m pip install -q -r requirements.txt

.venv/bin/python make_slides.py          # slides.toml -> slides/slideN.png
.venv/bin/python make_video.py ../demo-silent.mp4
.venv/bin/python make_audio.py ../demo-silent.mp4 ../demo-narrated.mp4
