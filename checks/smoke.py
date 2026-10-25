"""Read-only deterministic check of a completed student graph; no Ollama call."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage


class SmokeModel:
    """Return two known tool requests, then finish after their observations."""

    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        observations = [message for message in messages if isinstance(message, ToolMessage)]
        if not observations:
            name, arguments = "list_files", {}
        elif len(observations) == 1:
            if "docs/business-rules.md" not in observations[0].content:
                raise AssertionError("The listing did not include the business rules")
            name, arguments = "read_file", {"path": "docs/business-rules.md"}
        else:
            if "ROUND_HALF_UP" not in observations[-1].content:
                raise AssertionError("The graph did not return the rules as a tool observation")
            return AIMessage(content="Scripted smoke check finished; no repair attempted.")
        return AIMessage(content="", tool_calls=[{
            "name": name, "args": arguments, "id": f"smoke-{len(observations)}",
            "type": "tool_call",
        }])


def load_agent(path: Path):
    spec = importlib.util.spec_from_file_location("week02_student_agent", path.resolve())
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load agent: {path}")
    module = importlib.util.module_from_spec(spec)
    # Future annotations on AgentState resolve through its registered module.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def check_graph(builder, root: Path):
    graph = builder(root, "scripted", model=SmokeModel())
    if graph is None:
        raise ValueError("Complete the graph TODOs first")
    result = graph.invoke(
        {"messages": [HumanMessage(content="List files and read the business rules; do not edit.")],
         "completion_status": "running", "reason": "Awaiting verification"},
        config={"recursion_limit": 8, "max_concurrency": 1},
    )
    messages = result["messages"]
    expected = [HumanMessage, AIMessage, ToolMessage, AIMessage, ToolMessage, AIMessage]
    if len(messages) != len(expected) or any(
        not isinstance(message, kind) for message, kind in zip(messages, expected)
    ):
        raise AssertionError("Expected two model/tool cycles and a final response in shared state")
    for request, observation in [(messages[1], messages[2]), (messages[3], messages[4])]:
        if request.tool_calls[0]["id"] != observation.tool_call_id:
            raise AssertionError("Tool observation was not linked to its request")
    if messages[-1].tool_calls:
        raise AssertionError("The final response must have no tool calls")
    if result.get("completion_status") != "incomplete" or not result.get("reason"):
        raise AssertionError("Read-only smoke must finish incomplete because it has no passing test observation")
    return messages


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", type=Path, default=Path("starter/agent.py"))
    parser.add_argument("--root", type=Path, default=Path("target-service"))
    args = parser.parse_args()
    try:
        messages = check_graph(load_agent(args.agent).build_agent, args.root)
    except (ValueError, AssertionError, NotImplementedError) as exc:
        parser.exit(1, f"SMOKE FAILED: {exc}\n")
    for message in messages:
        message.pretty_print()
    print("SMOKE PASSED: two linked observations; verify correctly marks untested work incomplete. Diagnostic only.")


if __name__ == "__main__":
    main()
