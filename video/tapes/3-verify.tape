# Live clip 3: independent verification, tool-policy denials, and an incomplete run.
Output video/clips/3-verify.mp4
Source video/tapes/settings.tape

Type "echo '=== Live: independent verification outside the agent ==='" Enter
Type "git diff -- target-service/orders/pricing.py | head -30" Enter
Wait
Sleep 5s
Type "clear; (cd target-service && python -m unittest discover -s tests -v 2>&1 | tail -14)" Enter
Wait
Type "git diff --exit-code fed594c -- target-service/orders/validation.py target-service/orders/service.py target-service/orders/storage.py target-service/tests/test_acceptance.py target-service/docs && echo 'protected diff: empty'" Enter
Wait
Sleep 4s

Type "clear; echo '=== Live: tool policy denials ==='" Enter
Type `python -c 'from pathlib import Path; from starter.agent import build_tools; t = {x.name: x for x in build_tools(Path("target-service"))}; print(t["read_file"].invoke({"path": "../HANDOUT.md"})); print(t["edit_pricing"].invoke({"old": "Decimal", "new": "float"}))'` Enter
Wait
Sleep 3s
Type "echo '=== Live: read-only run without test evidence (stdin closed, so any test request is denied) ==='" Enter
Type `python starter/agent.py --root target-service --model qwen3:8b --task "Read docs/business-rules.md and summarize it in two sentences. Do not edit files or run tests." < /dev/null 2>&1 | tail -12; echo "exit code: ${PIPESTATUS[0]}"` Enter
Wait
Sleep 6s
