# Week 2 verified coding-agent lab

This lab replaces Week 1's controller with a live local Ollama model,
LangGraph tool routing, and an explicit verification decision. You use
four supplied scoped tools and implement response validation, model invocation,
graph construction, and verification.

Start with [HANDOUT.md](HANDOUT.md). Begin the lab by setting up Python 3.12,
installing the dependencies from `requirements-lock.txt`, downloading
`qwen3:8b`, and running `checks/probe_model.py`.
The model uses native calls, with reasoning disabled and bounded context,
generation, and timeouts. A scripted or manual repair does not complete the lab.

- `starter/agent.py`: supplied tools, model factory, CLI, and four TODO sections.
- `checks/probe_model.py`: local native-tool preflight before granting file tools.
- `checks/smoke.py`: read-only graph/state diagnostic.
- `checks/workflow.py`: harmless temporary-fixture write/test/verification checks.
- `target-service/`: defective service and nine original acceptance tests.
- `task.txt`: the repair task, configurable through `--task`.
- `questionnaire.md`: required answer template.
- `requirements.txt` / `requirements-lock.txt`: pinned framework dependencies.

Keep the agent outside the service. Independently author a regression before
running the live repair, then show ten passing tests and an empty protected-file
diff. Submit source, questionnaire, and one four-minute explanation video.
