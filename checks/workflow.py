"""Check the completed graph's write/test/verification routes on harmless fixtures."""

from __future__ import annotations

import argparse
from pathlib import Path
import tempfile
from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.errors import GraphRecursionError
from smoke import load_agent

ORIGINAL = 'LABEL = "original"\n'
UPDATED = 'LABEL = "updated"\n'


class WorkflowModel:
    """Supply known native-message requests, without solving the pricing task."""

    def __init__(self, actions):
        self.actions = iter(actions)
        self.calls = 0

    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        action = next(self.actions, None)
        if action is None:
            return AIMessage(content="Fixture exercise finished.")
        self.calls += 1
        name, arguments = action
        return AIMessage(content="", tool_calls=[{
            "name": name, "args": arguments, "id": f"fixture-{self.calls}", "type": "tool_call",
        }])


def check_workflow(builder):
    with tempfile.TemporaryDirectory(prefix="week02-workflow-") as directory:
        root = Path(directory)
        (root / "orders").mkdir()
        (root / "orders/__init__.py").write_text("")
        (root / "orders/pricing.py").write_text(ORIGINAL)
        (root / "tests").mkdir()
        (root / "tests/test_fixture.py").write_text(
            'import unittest\nfrom orders.pricing import LABEL\n'
            'class Fixture(unittest.TestCase):\n'
            '    def test_label(self):\n'
            '        self.assertEqual(LABEL, "updated")\n'
        )

        def invoke(actions, approvals=()):
            graph = builder(root, "scripted", model=WorkflowModel(actions))
            if graph is None:
                raise ValueError("Complete the graph TODOs first")
            with patch("builtins.input", side_effect=list(approvals)):
                return graph.invoke(
                    {"messages": [HumanMessage(content="Exercise the harmless label fixture.")],
                     "completion_status": "running", "reason": "Awaiting verification"},
                    config={"recursion_limit": 32, "max_concurrency": 1},
                )

        failed = invoke([("run_tests", {})], ["yes"])
        if failed.get("completion_status") != "incomplete":
            raise AssertionError("Failing tests cannot verify completion")
        result = invoke([
            ("read_file", {"path": "orders/pricing.py"}),
            ("edit_pricing", {"old": ORIGINAL, "new": UPDATED}),
            ("run_tests", {}), ("run_tests", {}),
        ], ["no", "yes"])
        observations = [message for message in result["messages"] if isinstance(message, ToolMessage)]
        if len(observations) != 4 or not observations[2].content.startswith("DENIED:"):
            raise AssertionError("Expected read, edit, denied test, and approved test observations")
        if not observations[3].content.startswith("exit_code=0\n"):
            raise AssertionError("The approved fixture test must pass")
        requests = {call["id"] for message in result["messages"] if isinstance(message, AIMessage) for call in message.tool_calls}
        if any(message.tool_call_id not in requests for message in observations):
            raise AssertionError("Observations must link to actual requests")
        if result.get("completion_status") != "verified" or not result.get("reason"):
            raise AssertionError("Passing tests after the edit must verify completion")
        if (root / "orders/pricing.py").read_text() != UPDATED:
            raise AssertionError("The graph did not execute the fixture edit")

        stale = invoke([
            ("run_tests", {}),
            ("edit_pricing", {"old": UPDATED, "new": UPDATED + "# later edit\n"}),
        ], ["yes"])
        denied = invoke([("run_tests", {})], ["no"])
        premature = invoke([])
        for label, state in [("stale tests", stale), ("denied tests", denied), ("untested final", premature)]:
            if state.get("completion_status") != "incomplete" or not state.get("reason"):
                raise AssertionError(f"{label} must produce an incomplete result")

        class EndlessModel(WorkflowModel):
            def invoke(self, messages):
                return AIMessage(content="", tool_calls=[{
                    "name": "list_files", "args": {}, "id": f"endless-{len(messages)}", "type": "tool_call",
                }])

        graph = builder(root, "scripted", model=EndlessModel([]))
        try:
            graph.invoke({"messages": [HumanMessage(content="Keep listing.")]}, config={"recursion_limit": 4})
        except GraphRecursionError:
            pass
        else:
            raise AssertionError("An unfinished graph must hit its configured limit")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", type=Path, default=Path("starter/agent.py"))
    args = parser.parse_args()
    try:
        check_workflow(load_agent(args.agent).build_agent)
    except (ValueError, AssertionError, NotImplementedError) as exc:
        parser.exit(1, f"WORKFLOW FAILED: {exc}\n")
    print("WORKFLOW PASSED: write, approval denial/retry, test failure, stale verification, final gate, and step limit.")
    print("Scripted harmless fixtures only; a live pricing repair is still required.")


if __name__ == "__main__":
    main()
