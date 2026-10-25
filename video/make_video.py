"""Render Lab 2 demo slides (real captured outputs) and encode a silent 4-minute MP4."""
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(sys.argv[1])
WORK = Path(__file__).parent / "slides"
WORK.mkdir(exist_ok=True)
W, H, SECONDS = 1920, 1080, 30

BG, PANEL, BORDER = "#0d1117", "#161b22", "#30363d"
FG, DIM, ACCENT = "#e6edf3", "#8b949e", "#2f81f7"
COLORS = {"r": "#ff7b72", "g": "#7ee787", "d": "#8b949e", "b": "#79c0ff", "y": "#e3b341"}
SANS = "/System/Library/Fonts/SFNS.ttf"
MONO = "/System/Library/Fonts/SFNSMono.ttf"
AUTHOR = "Author: Michael Auß (se25m055@technikum-wien.at)  ·  AI usage: Claude Opus 5.5"


def font(path, size):
    return ImageFont.truetype(path, size)


SLIDES = [
    dict(section="1/4  Model/tool graph, verification node, bounded termination", time="0:00–0:30",
         title="LangGraph replaces the hand-written Week 1 loop", size=27, author=True, lines=[
        "!d# starter/agent.py :: build_agent()",
        "graph = StateGraph(AgentState)            !d# MessagesState + completion_status, reason",
        "graph.add_node(\"model\", call_model)       !d# SystemMessage + bound qwen3:8b + validate_response",
        "graph.add_node(\"tools\", ToolNode(tools))  !d# list_files, read_file, edit_pricing, run_tests",
        "graph.add_node(\"verify\", verify)",
        "graph.add_edge(START, \"model\")",
        "graph.add_conditional_edges(\"model\", tools_condition, {\"tools\": \"tools\", END: \"verify\"})",
        "graph.add_edge(\"tools\", \"model\")",
        "graph.add_edge(\"verify\", END)",
        "",
        "!bSTART -> model -- native call ----> tools -> model",
        "!b              \\-- final response --> verify -> END",
        "",
        "RUN_CONFIG = {\"recursion_limit\": 32, \"max_concurrency\": 1}",
        "!d# limit reached -> GraphRecursionError -> \"INCOMPLETE: graph step limit reached\", exit 2",
        "",
        "!d# validate_response: not AIMessage or invalid_tool_calls -> ValueError (text never parsed as a call)",
    ], caption="The framework runs the route; tool code and the verify node decide what counts"),
    dict(section="1/4  Model/tool graph, verification node, bounded termination", time="0:30–1:00",
         title="verify trusts tool observations, not the model's final claim", size=25, lines=[
        "!d# starter/agent.py :: verify(state)",
        "for message in state[\"messages\"]:            !d# trusted ToolMessages, in order",
        "    if message.name == \"edit_pricing\" and content.startswith(\"Updated \"):",
        "        tests_pass = False                     !d# a later edit makes earlier tests stale",
        "    elif message.name == \"run_tests\":",
        "        tests_pass = content.startswith(\"exit_code=0\\n\")   !d# fail / DENIED / ERROR clear it",
        "final = state[\"messages\"][-1]                 !d# must be nonempty, without tool calls",
        "-> {\"completion_status\": \"verified\" | \"incomplete\", \"reason\": ...}",
        "",
        "$ python checks/smoke.py --agent starter/agent.py --root target-service",
        "!gSMOKE PASSED: two linked observations; verify correctly marks untested work incomplete.",
        "",
        "$ python checks/workflow.py --agent starter/agent.py",
        "!gWORKFLOW PASSED: write, approval denial/retry, test failure, stale verification,",
        "!g                 final gate, and step limit.",
        "!dScripted harmless fixtures only; a live pricing repair is still required.",
    ], caption="Diagnostics exercise the routes; they do not show that a live model can repair pricing"),
    dict(section="2/4  Live native requests and linked observations", time="1:00–1:30",
         title="Live run: qwen3:8b selects the read tools", size=26, lines=[
        "$ python starter/agent.py --root target-service --model qwen3:8b --task \"$(cat task.txt)\"",
        "!dWorkspace: .../framework-agent-lab/target-service   Model: qwen3:8b",
        "",
        "!bNode: model  !yAI tool call  read_file (fdc1c16c-bd55-4cd6-b701-0b303e46721c)",
        "                            path: docs/business-rules.md",
        "!bNode: tools  !gToolMessage   name: read_file  -> \"# Customer pricing rules ...\"",
        "",
        "!bNode: model  !yAI tool call  read_file (847a97a1-41f7-493d-9e37-344f1c9b1a31)",
        "                            path: tests/test_acceptance.py",
        "!bNode: tools  !gToolMessage   name: read_file  -> acceptance tests (9 cases)",
        "",
        "!bNode: model  !yAI tool call  read_file (e3daddb9-8059-4d91-b0f0-db22203f35cd)",
        "                            path: orders/pricing.py",
        "!bNode: tools  !gToolMessage   name: read_file  -> baseline pricing.py",
        "",
        "!dToolNode answers each native request with a ToolMessage carrying its tool_call_id;",
        "!dthe observation returns to the model node for the next decision.",
    ], caption="Native structured calls only; the model's text is never executed"),
    dict(section="2/4  Model-selected pricing edit", time="1:30–2:00",
         title="edit_pricing: one exact replacement, pricing.py only", size=22, lines=[
        "!bNode: model  !yAI tool call  edit_pricing (d88fbb7b-6ea0-415d-b05d-734fef0c4e3d)",
        "!dold: <exact baseline text read above>   new: <complete replacement incl. imports>",
        "!bNode: tools  !gToolMessage   name: edit_pricing  -> Updated orders/pricing.py once",
        "",
        "$ git diff -- target-service/orders/pricing.py        !d# reviewed before approving tests",
        "!r-from decimal import Decimal",
        "!g+from decimal import Decimal, ROUND_HALF_UP",
        "  from .validation import validate_order",
        "  def quote(lines, discount=Decimal(\"0\")):",
        "      validate_order(lines, discount)",
        "!r-    subtotal = sum((line[\"unit_price\"] * line[\"quantity\"] for line in lines), Decimal(\"0\"))",
        "!r-    shipping = Decimal(\"0\") if subtotal >= Decimal(\"100\") else Decimal(\"5\")",
        "!r-    total = ((subtotal + shipping) * (1 - discount)).quantize(Decimal(\"0.01\"))",
        "!g+    subtotal = Decimal(\"0\")",
        "!g+    for line in lines:",
        "!g+        line_total = (line[\"unit_price\"] * line[\"quantity\"]).quantize(Decimal(\"0.01\"), rounding=ROUND_HALF_UP)",
        "!g+        subtotal += line_total",
        "!g+    discount_amount = (subtotal * discount).quantize(Decimal(\"0.01\"), rounding=ROUND_HALF_UP)",
        "!g+    discounted_goods = subtotal - discount_amount",
        "!g+    shipping = Decimal(\"0\") if discounted_goods >= Decimal(\"100\") else Decimal(\"5\")",
        "!g+    total = discounted_goods + shipping",
        "      return {\"subtotal\": subtotal, \"shipping\": shipping, \"total\": total}",
    ], caption="The model proposes; the tool enforces one path, one unique match, and a 12,000-byte limit"),
    dict(section="3/4  Agent's test observation", time="2:00–2:30",
         title="Fixed test command, human approval, verified result", size=25, lines=[
        "!bNode: model  !yAI tool call  run_tests (7e71bbed-ab3a-4369-97e9-a0a14c47da60)",
        "Proposed command: .venv/bin/python -m unittest discover -s tests -v",
        "Working directory: .../framework-agent-lab/target-service",
        "Approve this command only? Type yes: !gyes",
        "",
        "!bNode: tools  !gToolMessage   name: run_tests",
        "!gexit_code=0",
        "test_discount_amount_rounded_before_subtraction ... !gok",
        "!d... 7 further acceptance tests ... ok",
        "test_shipping_threshold_uses_discounted_goods ... !gok",
        "test_multi_quantity_line_rounded_after_multiplication (test_student) ... !gok",
        "!gRan 10 tests   OK",
        "",
        "!bNode: model  !dAI: \"All tests passed successfully. The pricing implementation has been repaired correctly.\"",
        "!bNode: verify !gVERIFIED: graph ended with successful tests after the latest edit.",
        "$ echo $?",
        "!g0",
    ], caption="VERIFIED comes from exit_code=0 after the latest edit, not from the model's sentence"),
    dict(section="3/4  Regression baseline failure, independent ten-test result, diff", time="2:30–3:00",
         title="Independent verification outside the agent", size=24, lines=[
        "!d# student regression: 0.335 x 3 = 1.005 -> 1.01 (ROUND_HALF_UP); shipping 5.00; total 6.01",
        "$ git archive fed594c target-service   !d# baseline pricing + my test_student.py",
        "$ python -m unittest discover -s tests -p test_student.py -v",
        "!rAssertionError: Decimal('1.005') != Decimal('1.01')",
        "!rFAILED (failures=1)",
        "",
        "$ cd target-service && python -m unittest discover -s tests -v     !d# repaired service",
        "!gRan 10 tests in 0.000s",
        "!gOK",
        "",
        "$ git diff --exit-code fed594c -- orders/validation.py orders/service.py \\",
        "      orders/storage.py tests/test_acceptance.py docs",
        "!gprotected diff: empty",
        "",
        "$ git diff --stat fed594c -- target-service",
        " target-service/orders/pricing.py     | 13 +++++++++----",
        " target-service/tests/test_student.py | 18 ++++++++++++++++++",
    ], caption="Only pricing (agent) and my regression (written before the run) changed"),
    dict(section="4/4  Failure boundary and incomplete result", time="3:00–3:30",
         title="Denied requests have no side effect; denial means INCOMPLETE", size=24, lines=[
        "!d# Checkpoint 2: tools called directly, before the graph",
        "read_file({\"path\": \"../HANDOUT.md\"})",
        "!r  -> ERROR: Use a visible relative path inside the service root      !d(traversal)",
        "edit_pricing({\"old\": \"Decimal\", \"new\": \"float\"})",
        "!r  -> ERROR: old text must be nonempty and occur exactly once         !d(ambiguous match)",
        "",
        "!d# Live run 1: same read/edit sequence, then the test request is denied",
        "Approve this command only? Type yes: !rno",
        "!bNode: tools  !rToolMessage   run_tests -> DENIED: the user did not approve this test command",
        "!bNode: model  !dAI: \"Please approve the test command to run the fixed acceptance tests.\"",
        "!bNode: verify !rINCOMPLETE: latest test run did not pass: DENIED: the user did not approve",
        "!r              this test command",
        "",
        "!d# pricing.py reset with git checkout before the verified run",
    ], caption="A final reply with denied, failed, or stale test evidence cannot verify completion"),
    dict(section="4/4  Remaining limitations", time="3:30–4:00",
         title="What remains unverified", size=27, author=True, lines=[
        "!y- Tests cover specific cases; correctness for untested inputs is not proven.",
        "!y- One VERIFIED live run at temperature 0 does not show reliable repair across runs.",
        "!y- Tool checks are application policy, not an OS sandbox: approved tests import",
        "!y  model-edited code with my permissions, so I read the diff before typing yes.",
        "!y- The 32-step limit stops work; it does not prove the repair.",
        "!y- \"The run stopped\" and \"the repair succeeded\" are different claims.",
        "",
        "!dSetup:  qwen3:8b (500a1f067a9f) via local Ollama 0.40.7, temperature 0, reasoning off",
        "!d        Python 3.12.15, LangGraph 1.2.15, preflight: LIVE PROBE PASSED",
        "!dSource: https://github.com/Sevyls/aaia-lab2",
    ], caption="Evidence: native requests, linked observations, verify node, independent tests and diff"),
]


def draw_line(draw, x, y, raw, mono):
    """Draw one line; '!x' switches colour for the rest of the segment."""
    color = FG
    for i, part in enumerate(raw.split("!")):
        if i and part[:1] in COLORS:
            color, part = COLORS[part[0]], part[1:]
        elif i:
            part = "!" + part
        draw.text((x, y), part, font=mono, fill=color)
        x += draw.textlength(part, font=mono)


def render(n, slide):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=ACCENT)
    d.text((70, 40), f"{slide['section']}  ·  {slide['time']}", font=font(SANS, 30), fill=DIM)
    d.text((70, 88), slide["title"], font=font(SANS, 54), fill=FG)
    d.rounded_rectangle([60, 172, W - 60, 950], radius=14, fill=PANEL, outline=BORDER, width=2)
    mono = font(MONO, slide["size"])
    step = int(slide["size"] * 1.45)
    for i, line in enumerate(slide["lines"]):
        draw_line(d, 94, 200 + i * step, line, mono)
    d.text((70, 975), slide["caption"], font=font(SANS, 32), fill=FG)
    if slide.get("author"):
        d.text((70, 1025), AUTHOR, font=font(SANS, 26), fill=DIM)
    path = WORK / f"slide{n}.png"
    img.save(path)
    return path


paths = [render(n, s) for n, s in enumerate(SLIDES, 1)]
listing = WORK / "list.txt"
listing.write_text("".join(f"file '{p}'\nduration {SECONDS}\n" for p in paths) + f"file '{paths[-1]}'\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
                "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-tune", "stillimage",
                "-t", str(SECONDS * len(SLIDES)), str(OUT)], check=True)
print(OUT)
