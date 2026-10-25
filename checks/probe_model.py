"""Probe local Ollama tool calling without file access or command execution."""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from starter.agent import create_model, DEFAULT_MODEL

os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool


@tool
def get_lab_status() -> str:
    """Return a known lab fixture status; no files are read or changed."""
    return "The supplied pricing baseline has nine tests: five fail and four pass."


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()
    model = create_model(args.model).bind_tools([get_lab_status])
    messages = [
        SystemMessage(content="Call get_lab_status exactly once, then report its result. Do not invent its result."),
        HumanMessage(content="What is the lab baseline status? Use the get_lab_status tool."),
    ]
    try:
        response = model.invoke(messages)
        response.pretty_print()
        if len(response.tool_calls) != 1:
            raise ValueError("Expected one structured tool call")
        call = response.tool_calls[0]
        if call["name"] != "get_lab_status" or call["args"]:
            raise ValueError("Unexpected tool or arguments")
        observation = ToolMessage(content=get_lab_status.invoke({}), tool_call_id=call["id"])
        observation.pretty_print()
        final = model.invoke([*messages, response, observation])
        final.pretty_print()
        if final.tool_calls or not final.content:
            raise ValueError("Expected a final text response after the observation")
    except Exception as exc:
        print(f"LIVE PROBE INCOMPLETE: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("LIVE PROBE PASSED: structured request, fixture observation, final response. No repair tested.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
