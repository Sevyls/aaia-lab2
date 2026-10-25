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
  `invalid_tool_calls`. Message text is never parsed into a call.
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

## Actual results

| Check | Result |
|---|---|
| Baseline acceptance tests | 9 run: 5 failed, 4 passed |
| Student regression on baseline | Failed: `Decimal('1.005') != Decimal('1.01')` |
| Tool denials | `read_file("../HANDOUT.md")` → `ERROR: Use a visible relative path inside the service root`; `edit_pricing(old="Decimal", ...)` → `ERROR: old text must be nonempty and occur exactly once` |
| `checks/smoke.py` | `SMOKE PASSED` |
| `checks/workflow.py` | `WORKFLOW PASSED` |
| Live run 1 (test approval denied) | Read rules, tests, and pricing; one pricing edit; `run_tests` → `DENIED`; verify: `INCOMPLETE: latest test run did not pass: DENIED: ...` (exit 2) |
| Live run 2 (pricing reset, approval given) | `read_file` ×3 → `edit_pricing` → `Updated orders/pricing.py once` → `run_tests` → `exit_code=0`, 10 tests OK → `VERIFIED` (exit 0) |
| Independent rerun | 10 tests OK |
| Protected-file diff | Empty; only `orders/pricing.py` changed (commit `87566b7`) |

## Limitations

- Tests cover specific cases; passing them does not prove pricing is correct for all inputs.
- One verified run at temperature 0 does not establish that the model repairs reliably.
- Tool checks are application policy, not an OS sandbox: approved tests import
  model-edited code with the user's permissions, so the diff is reviewed before approval.
- VS Code test discovery uses pytest via `pytest.ini`, a local convenience only.
  pytest is not in the lock file, and the handout's unittest commands are the
  evidence of record.
