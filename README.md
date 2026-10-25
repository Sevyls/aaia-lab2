# Week 2 verified coding-agent lab — submission

A LangGraph agent with a local Ollama model repairs `target-service/orders/pricing.py`
through four scoped tools. An explicit `verify` node accepts completion only when
tests pass after the latest successful edit. Lab instructions: [HANDOUT.md](HANDOUT.md).

## Environment

| Item | Value |
|---|---|
| OS | macOS, Apple Silicon (arm64) |
| Python | 3.12.15 (`.venv`, from `requirements-lock.txt`) |
| Ollama | 0.40.7, local endpoint `http://127.0.0.1:11434` |
| Model | `qwen3:8b` (ID `500a1f067a9f`), temperature 0, reasoning disabled |
| Preflight | `LIVE PROBE PASSED` |

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python -m pip check
ollama pull qwen3:8b
python checks/probe_model.py --model qwen3:8b
```

## Run

```bash
# Diagnostics (scripted, no Ollama call)
python checks/smoke.py --agent starter/agent.py --root target-service
python checks/workflow.py --agent starter/agent.py

# Live repair (approve the fixed test command with "yes" after reviewing the diff)
python starter/agent.py --root target-service --model qwen3:8b --task "$(cat task.txt)"

# Independent verification
cd target-service
git diff -- orders/pricing.py
git diff --exit-code -- orders/validation.py orders/service.py orders/storage.py tests/test_acceptance.py docs
python -m unittest discover -s tests -v
```

The service is tracked in this repository rather than in a nested Git repository, so
`git diff` above runs against the baseline commit `fed594c`.

## What was implemented

All changes are in [starter/agent.py](starter/agent.py):

- `validate_response`: raises `ValueError` unless the response is an `AIMessage` without
  `invalid_tool_calls`. Message text is never parsed into a call. The CLI reports the
  `ValueError` as `INCOMPLETE` (exit 2).
- `call_model`: prepends `SystemMessage(SYSTEM_INSTRUCTION)`, invokes the bound model,
  validates the result, and returns only the new message.
- Graph: `START → model`; `tools_condition` routes native calls to `ToolNode` and
  returns to `model`; its END route goes to `verify → END`.
- `verify`: walks `ToolMessage` observations in order. A successful `edit_pricing`
  clears earlier test success; each `run_tests` result replaces the status
  (`exit_code=0` passes; failure, `DENIED`, or `ERROR` clears it). `verified` also
  requires a nonempty final response without tool calls.

Student regression: [target-service/tests/test_student.py](target-service/tests/test_student.py).
Expected from the business rules: one line `0.335 × 3 = 1.005 → 1.01` (ROUND_HALF_UP),
shipping 5.00, total 6.01. Rounding the unit price first would give 1.02.

The acceptance tests are the customer's requirements, so they stay unchanged. Weakening one
(for example, accepting `1.005` or the old total) would make the suite pass while `quote`
still returns the wrong amount, so the reported totals would stay incorrect.

## Actual results

Live runs used `task.txt` unless noted, starting from baseline pricing each time.

| Check | Result |
|---|---|
| Baseline acceptance tests | 9 run: 5 failed, 4 passed |
| Student regression on baseline | Failed: `Decimal('1.005') != Decimal('1.01')` |
| Tool denials | `read_file("../HANDOUT.md")` → `ERROR: Use a visible relative path inside the service root`; `edit_pricing(old="Decimal", ...)` → `ERROR: old text must be nonempty and occur exactly once` |
| `checks/smoke.py` | `SMOKE PASSED` |
| `checks/workflow.py` | `WORKFLOW PASSED` |
| Malformed responses (scripted model) | `invalid_tool_calls` → `ValueError`; non-`AIMessage` → `ValueError`; JSON-looking text → no tool executed, `incomplete` |
| Live run 1: human typed `no` | Read rules, tests, and pricing; one pricing edit; `run_tests` → `DENIED`; verify: `INCOMPLETE: latest test run did not pass: DENIED: ...` (exit code not captured) |
| Live run 2: human typed `yes` | `read_file` ×3 → `edit_pricing` → `Updated orders/pricing.py once` → `run_tests` → `exit_code=0`, 10 tests OK → `VERIFIED` (exit 0); committed as `87566b7` |
| Live run 3: recorded with VHS, scripted `yes` | Same sequence; `run_tests` call `3f09b577…` → `exit_code=0`, 10 tests OK → `VERIFIED` (exit 0); edit identical to `87566b7` |
| Live run 4: read-only task, recorded | Model answered without any tool call → `INCOMPLETE: no test run was observed`, exit code 2 |
| Independent rerun | 10 tests OK |
| Protected-file diff | Empty; only `orders/pricing.py` and `tests/test_student.py` differ from `fed594c` |

## Demo video

**Submitted video: [demo-final.mp4](demo-final.mp4)** (4:00, 1920×1080, AI-generated narration).

| Time | Content | Source |
|---|---|---|
| 0:00–1:00 | Graph wiring, `verify` rule, step limit, diagnostics | Slides 1–2 |
| 1:00–1:20 | Pricing reset to `fed594c`; student regression fails | Live recording (0.5×) |
| 1:20–2:40 | Live run 3: native calls, linked observations, pricing edit, tests, `VERIFIED`, exit 0 | Live recording (0.5×) |
| 2:40–3:30 | Diff, 10 tests, protected diff, denials, live run 4 (`INCOMPLETE`, exit 2) | Live recording (0.91×) |
| 3:30–4:00 | Remaining limitations | Slide 8 |

The live segments are real terminal recordings made with [VHS](https://github.com/charmbracelet/vhs).
VHS types the commands, including `yes` at the approval prompt, and the video says so on screen.
The human-approved repair is live run 2 above. The narration uses Kokoro TTS (`af_heart`),
which every slide notes.

`demo-silent.mp4` and `demo-narrated.mp4` are earlier slide-only versions (8 slides of 30 s,
showing captured outputs from runs 1 and 2). They are kept for reference but are not the
submitted video.

Rebuild (needs python3.12, ffmpeg, and `brew install vhs`; the first run downloads the
Kokoro model, about 350 MB, into the git-ignored `video/kokoro/`):

```bash
video/build.sh                                       # slides, demo-silent.mp4, demo-narrated.mp4
for t in 1-baseline 2-live 3-verify; do vhs video/tapes/$t.tape; done   # live clips; runs qwen3:8b
video/.venv/bin/python video/make_demo.py demo-final.mp4
```

Slide content is in [video/slides.toml](video/slides.toml). Slide narration is in
[video/make_audio.py](video/make_audio.py), and narration for the live segments is in
[video/make_demo.py](video/make_demo.py).

## AI usage

Claude Opus 5.5 (Claude Code) assisted with this submission. It implemented the four TODOs
in `starter/agent.py`, drafted `tests/test_student.py`, the README, and the questionnaire,
and built the demo video tooling and narration. The pricing repair itself was made by
`qwen3:8b` through `edit_pricing` in the live runs.

## Limitations

- Tests cover specific cases; passing them does not prove pricing is correct for all inputs.
- Two verified runs at temperature 0 produced the same edit. That does not establish
  reliability for other tasks, models, or settings.
- Tool checks are application policy, not an OS sandbox: approved tests import
  model-edited code with the user's permissions, so the diff is reviewed before approval.
- The repaired `quote` returns shipping as `Decimal("5")` or `Decimal("0")`, not quantized to
  cents. The tests pass because Decimal equality ignores the exponent, but the printed value
  is `5`, not `5.00`.
- VS Code test discovery uses pytest via `pytest.ini`, a local convenience only.
  pytest is not in the lock file, and the handout's unittest commands are the
  evidence of record.
