# Week 2 verified agent questionnaire

Name / team:

Repository URL or source ZIP: https://github.com/Sevyls/aaia-lab2

Local model tag and preflight result: `qwen3:8b` (Ollama ID `500a1f067a9f`), `LIVE PROBE PASSED`

Answer each in two to five clear sentences and refer to your four-minute video.
Scripted diagnostics support development; completion requires a live repair.

1. Which part of the Week 1 loop did LangGraph replace? Explain the nodes,
   message updates, routes, and what the 32-step limit guarantees.

   Answer: LangGraph replaced the hand-written `while` loop that called the model, dispatched tool calls, and appended results. The `model` node prepends the system instruction, invokes the bound model, validates the reply, and returns only the new `AIMessage`, which `MessagesState` appends. `ToolNode` executes native tool calls and appends `ToolMessage`s linked by `tool_call_id`. `tools_condition` routes tool calls to `tools`, which always returns to `model`, and sends a final response to `verify` and then END. The 32-step recursion limit guarantees the run stops after at most 32 graph steps with `GraphRecursionError`, reported as INCOMPLETE; it bounds work but says nothing about whether the repair is correct.

2. Which boundaries do the supplied tools enforce regardless of the model's
   request? Explain both denials and why a fixed test command still needs review.

   Answer: `read_file` resolves paths only inside the service root and rejects absolute paths, `..`, hidden components, symbolic links, and files over 12,000 bytes. `edit_pricing` can only write `orders/pricing.py` and only when `old` occurs exactly once, and `run_tests` runs one fixed argument list with a fixed working directory, minimal environment, 30-second timeout, and an explicit `yes`. `read_file("../HANDOUT.md")` was denied as traversal outside the root, and `edit_pricing(old="Decimal")` was denied because `Decimal` appears several times, so the target of the replacement would be ambiguous. The fixed command still needs review because unittest imports the model-edited `pricing.py`, which runs as Python with my permissions and no OS sandbox. Before typing `yes` I checked the diff: only `pricing.py` changed, and it added only a `ROUND_HALF_UP` import and arithmetic.

3. How does your verification node distinguish a final response from verified
   completion? Explain failed/denied tests and an edit after a passing test.
   Identify one incomplete result you demonstrated.

   Answer: `verify` ignores the model's claim and walks the trusted `ToolMessage` observations in order. A successful `edit_pricing` clears any earlier test pass, and each `run_tests` result replaces the status: only `exit_code=0` passes, while a nonzero exit, `DENIED`, or `ERROR` clears it. Completion is `verified` only if tests currently pass and the final message is a nonempty response without tool calls, so an edit after a passing test makes the evidence stale and the result incomplete. In my first live run I answered `no` to the test prompt; the model only asked for approval, and verify returned `INCOMPLETE: latest test run did not pass: DENIED: the user did not approve this test command` with exit code 2.

4. What evidence shows that the live model read, edited, and tested the service?
   State the model tag, your regression's expected business result and baseline
   failure, the final test result, and protected files you checked. What remains
   unverified?

   Answer: With `qwen3:8b`, the streamed run shows native `read_file` calls for the rules, the acceptance tests, and pricing, then `edit_pricing` (`d88fbb7b…`) answered by `Updated orders/pricing.py once`, then `run_tests` (`7e71bbed…`) answered by `exit_code=0` with 10 tests OK, ending in VERIFIED with exit 0. My regression expects one line of 0.335 × 3 = 1.005 rounded half-up to 1.01, shipping 5.00, and total 6.01; on the baseline it failed with `Decimal('1.005') != Decimal('1.01')`. My independent rerun passed all 10 tests, and `git diff --exit-code` on `validation.py`, `service.py`, `storage.py`, `test_acceptance.py`, and `docs` was empty. Still unverified are correctness for inputs the tests do not cover, whether the model repairs reliably across runs, and any protection beyond application-level tool checks, since there is no OS sandbox.
