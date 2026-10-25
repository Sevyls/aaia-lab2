# Build a verified coding agent with LangGraph

Week 2 student lab | Advanced AI-Assisted Software Development

Last week you wrote an agent loop. This week you will build a fully functional
local agent with native tool calls, a LangGraph workflow, and an explicit
verification decision. A model's final answer cannot establish success.

## Learning outcomes

By the end of the lab, you can:

- implement a model/tool loop with shared message state and conditional routing;
- reject malformed model responses without executing JSON-looking text;
- link native tool requests to their observations and repository effects;
- verify completion from passing tests after the latest successful edit;
- demonstrate incomplete work after denied execution, failed tests, or a limit;
- supervise a live agent repair using independent tests and a protected-file diff.

## Your task

A customer reports incorrect totals in an order-pricing service. Build the
agent that reads the business rules and tests, repairs `orders/pricing.py`,
requests approval for the fixed test command, and reports verified completion.
The four supplied tools enforce workspace boundaries in Python. You implement
response validation, model invocation, graph wiring, and the verification node.

Use local Ollama with the target model `qwen3:8b`. A live model-selected read,
edit, and test sequence is required. Scripted checks help debug your graph;
a scripted run or manual pricing repair does not complete this lab. Human
approval of test execution is part of the supervised agent workflow.

You independently author one regression test in `tests/test_student.py` before
starting the repair. The agent can edit only pricing and cannot write that test.
Keep the public API, validation, persistence, original acceptance tests, and
business-rule documents unchanged.

## Workflow

Work through the checkpoints at your own pace. Use the diagnostics and completion
criteria to decide when to move on, and revisit earlier steps when needed.

1. Set up the local environment and pass the model preflight.
2. Reproduce the baseline and write a regression.
3. Inspect tools and demonstrate two denials.
4. Implement graph, validation, and verification; run diagnostics.
5. Run the live repair and inspect the native tool sequence.
6. Independently review the diff and verify the service.
7. Reflect on the evidence, complete the questionnaire, and record your video.

## Setup: install dependencies and check the model

Setup is the first part of this lab. Use the Python and Ollama installation
from Week 1, with Python 3.12 for this project. If `python3` is older, use
`python3.12` below. Extract the student ZIP, open a terminal in the extracted
`framework-agent-lab` directory, and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python -m pip check
ollama pull qwen3:8b
ollama list
python checks/probe_model.py --model qwen3:8b
```

The model download is approximately 5.2 GB. Use a computer with about 16 GB of
memory and close heavy applications before inference. Download and inference
speeds depend on your connection and computer. On
Windows, use WSL2 with Python and Ollama in the same environment. Start the
Ollama app or `ollama serve` if the local server is unavailable.

Expect `LIVE PROBE PASSED`: a native `get_lab_status` request, a linked tool
observation, and a final response. The probe changes no files and works before
completing the starter. If it fails, check that Ollama is running and that
`ollama list` includes `qwen3:8b`, then retry the probe. Ask the instructor for
help with setup or access to a suitable local lab machine if needed. Do not substitute a
cloud model or begin with a model that failed preflight.

`create_model` supplies the same configuration to the agent and preflight:
local endpoint `http://127.0.0.1:11434`, temperature 0, reasoning disabled,
16,384-token context, 2,048-token output limit, and 120-second HTTP timeout.
Hosted tracing is disabled. `--model` remains configurable, but any alternative
local model must pass preflight and perform the complete live repair.

Run commands from the lab directory unless shown otherwise. Keep the agent,
virtual environment, and runtime outputs outside `target-service`.

## Checkpoint 1: establish the defect

Read `target-service/docs/business-rules.md`, pricing, and the acceptance tests.
The local `docs/decimal-reference.md` provides the needed Decimal concepts.
Record the baseline:

```bash
cd target-service
git init
git add .
git -c user.name="Lab Student" -c user.email="student@example.invalid" \
  commit -m "Record framework lab baseline"
python -m unittest discover -s tests -v
cd ..
```

Expect nine tests: five pricing failures and four passes. Choose an additional
boundary case with a result derived from the business rules. Write it yourself
in `target-service/tests/test_student.py` and prove it fails against the original
pricing before the live repair. Complete this during graph construction if
needed, but add the test before starting the agent.

```bash
cd target-service
python -m unittest discover -s tests -p test_student.py -v
cd ..
```

Do not copy a supplied acceptance case. Explain why weakening an acceptance test
would leave the customer's problem in place.

## Checkpoint 2: inspect the boundary

Read `build_tools`. Its four tools list visible files, read bounded UTF-8 text,
replace one unique fragment in pricing, and run a fixed test command. The model
cannot select arbitrary commands or a different write path.

Demonstrate two denied requests before connecting the graph:

```bash
python - <<'PY'
from pathlib import Path
from starter.agent import build_tools
tools = {tool.name: tool for tool in build_tools(Path("target-service"))}
print(tools["read_file"].invoke({"path": "../HANDOUT.md"}))
print(tools["edit_pricing"].invoke({"old": "Decimal", "new": "float"}))
PY
```

Both return `ERROR` without changing the service. Explain traversal rejection
and why replacing a repeated fragment is ambiguous. Paths also reject hidden
components and symbolic links; reads and writes have a 12,000-byte limit.

The test tool shows the fixed command and working directory and requires exactly
`yes`. Read the pricing diff before approval. Executing tests imports modified
Python with your permissions. These application checks do not provide an
operating-system sandbox. Use only the supplied disposable service.

## Checkpoint 3: implement the workflow

Complete the four TODO sections in `starter/agent.py`. Keep the supplied tools,
model factory, CLI, and `build_agent(root, model_name, *, model=None)` interface.

1. **Response validation:** require `AIMessage` and reject `invalid_tool_calls`.
   Raise `ValueError` on an invalid response. Never turn message text into a call.
2. **Model node:** prepend `SystemMessage(SYSTEM_INSTRUCTION)`, invoke the bound
   model with current history, validate its response, and return just the new
   response under `messages`. `MessagesState` appends that update.
3. **Graph:** use `AgentState` with `model`, `tools`, and `verify` nodes. START
   enters the model, `ToolNode` returns observations to the model, and
   `tools_condition` routes native calls to tools. Map its END result to the
   verification node, then connect verification to END.
4. **Verification:** inspect the final response and trusted `ToolMessage`
   observations in order. A successful pricing edit clears earlier test success.
   Each later test replaces the test status: exit code 0 passes, while failure,
   denial, or error clears success. Require a nonempty final response without
   tool calls and current passing tests. Return `completion_status` as
   `verified` or `incomplete`, with a clear `reason`.

The workflow is:

```text
START -> model -- native call --> tools -> model
             \-- final response --> verify -> END
```

`AgentState` adds `completion_status` and `reason` to message state. The CLI
starts with `running`, streams requests and observations, and uses the
verification result for its exit code: 0 verified, 2 incomplete/error, 130
interrupted. `RUN_CONFIG` permits 32 graph steps and serializes tool execution.
The graph limit counts steps, not calls or elapsed seconds. Failed tests return
to the model so it can repair and retry within that limit.

Run both diagnostics against your implementation:

```bash
python checks/smoke.py --agent starter/agent.py --root target-service
python checks/workflow.py --agent starter/agent.py
```

The smoke checks linked read observations and an incomplete verification result
for untested work. The workflow check uses a harmless temporary label fixture
and checks an edit, denied approval, approved execution, failing tests, stale
verification after another edit, premature final response, and the step limit.
It contains no pricing solution. Automatic approvals apply only to that known
fixture. Neither diagnostic establishes that a live model can repair pricing.

## Checkpoint 4: live agent repair

Confirm your student regression has failed against the baseline. Start the agent:

```bash
python starter/agent.py \
  --root target-service \
  --model qwen3:8b \
  --task "$(cat task.txt)"
```

`task.txt` supplies the repair instructions for the agent.
Inspect its requested read order and exact-replacement precondition. You may
edit the task for later experiments, while keeping the required business rules.
Inspect native requests, linked observations, and the proposed edit. Review the
diff in another terminal before typing `yes` for the fixed test command.
A failed test is feedback for the next model decision. A final model claim with
failed, denied, or stale test evidence must produce `INCOMPLETE` and exit code 2.

If the run is incomplete, inspect its reason, check the code and setup, and
rerun with a focused task or corrected agent implementation. You may change
instructions and agent code. The successful pricing repair must come from
model-selected edits through the supplied tool. A manual pricing patch cannot
be submitted as a successful live run. For a repeat demonstration, use a fresh
service copy rather than destroying work you need to retain.

## Checkpoint 5: independent verification

After `VERIFIED`, review the resulting service yourself:

```bash
cd target-service
git status --short
git diff -- orders/pricing.py
git diff --exit-code -- orders/validation.py orders/service.py orders/storage.py tests/test_acceptance.py docs
python -m unittest discover -s tests -v
cd ..
```

All nine original acceptance tests and your regression must pass. Only pricing
and your new regression should appear in service changes; the protected diff
must be empty. A model answer, framework termination, or passing preflight
alone cannot establish a correct repair.

## Reflection and submission

Use partner review to explain one request/observation pair, your verification
rule, and one incomplete result. Complete [questionnaire.md](questionnaire.md).

Submit exactly three items:

1. **Source:** repository URL or ZIP with agent, repaired service, your regression,
   and a short README containing setup, run commands, model tag, and actual
   results. Exclude virtual environments, models, credentials, and caches.
2. **Answered questionnaire:** two to five clear sentences for each question.
3. **One four-minute video:** record once your implementation and verification
   are complete, and show your own work.

Your video must demonstrate:

- Model/tool graph, explicit verification node, and bounded termination.
- Live native request, linked observation, and model-selected pricing edit.
- Agent's test observation, independent ten-test result, regression baseline
  failure, and diff.
- One failure boundary, incomplete result, and remaining limitations.

No separate logs, screenshots, trace exports, or diff files are required.

## Completion criteria

- Both graph diagnostics pass and incomplete work receives the correct result.
- The live local model selects read, pricing-edit, and test tools; observations
  return to the model and a final response passes the verification node.
- The agent's repair passes all original acceptance tests plus your distinct
  regression, with protected files unchanged.
- Passing tests precede no later successful edit or failed/denied test.
- Source, questionnaire, and four-minute video explain the evidence honestly.

## References

- [LangGraph Quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart)
- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [ChatOllama integration](https://docs.langchain.com/oss/python/integrations/chat/ollama/)
- [Qwen3 8B model](https://ollama.com/library/qwen3:8b)
