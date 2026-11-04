#!/usr/bin/env python3
"""Validates the status line that closes an agent report (piece A04).

  report_status.py [FILE] [--json]

Reads FILE or stdin. With --json the input is the JSON printed by `claude -p --output-format json`
and the report is its `result` string. The last non-empty line must be `STATUS: OK` (exit 0) or
`STATUS: STOPPED — <reason>` (exit 1, prints the reason). Anything else is never a pass (exit 1).
Unreadable input or invalid JSON: exit 2.

  report_status.py --hook

SubagentStop hook: reads the hook JSON on stdin and, for the agents of this project
(.claude/agents/<agent_type>.md under $CLAUDE_PROJECT_DIR), warns with a systemMessage when the
final message has no valid status line or is STOPPED. It never blocks and always exits 0.
"""

import json
import os
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

NO_STATUS = "no status line: the report must end with STATUS: OK or STATUS: STOPPED — <reason>"
OK = re.compile(r"STATUS:\s*OK")
STOPPED = re.compile(r"STATUS:\s*STOPPED\s*(?:—|-|:)\s*(\S.*)")


def validate(report):
    """Returns (exit code, message) for a report text."""
    lines = [line.strip() for line in report.splitlines() if line.strip()]
    if not lines:
        return 1, NO_STATUS
    last = lines[-1]
    if OK.fullmatch(last):
        return 0, "report status: OK"
    stopped = STOPPED.fullmatch(last)
    if stopped:
        return 1, f"report status: STOPPED — {stopped.group(1).strip()}"
    return 1, NO_STATUS


def hook():
    """SubagentStop: a warning for the person, never a decision."""
    try:
        data = json.load(sys.stdin)
        kind = data.get("agent_type")
        project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or ".")
        if not isinstance(kind, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", kind) \
                or not (project / ".claude" / "agents" / f"{kind}.md").is_file():
            return 0
        message = data.get("last_assistant_message")
        code, text = validate(message if isinstance(message, str) else "")
        if code == 0:
            return 0
        if text.startswith("report status: STOPPED"):
            out = f"Subagent {kind} stopped: {text.split('— ', 1)[1]}"
        else:
            out = (f"Subagent {kind} ended without a STATUS line → its report is not a pass; "
                   f"ask it to finish with STATUS: OK or STATUS: STOPPED — <reason>")
        print(json.dumps({"systemMessage": out}, ensure_ascii=False))
    except Exception as exc:  # noqa: BLE001  a hook that fails must not keep the subagent going
        print(f"report_status hook could not run: {type(exc).__name__}: {exc}", file=sys.stderr)
    return 0


def main(argv):
    if "--hook" in argv:
        return hook()
    args = [a for a in argv if a != "--json"]
    as_json = "--json" in argv
    try:
        if args:
            with open(args[0], encoding="utf-8") as fh:
                text = fh.read()
        else:
            text = sys.stdin.read()
    except (OSError, UnicodeDecodeError) as err:
        print(f"report_status could not run: cannot read the report ({err}) → check the path")
        return 2
    if as_json:
        try:
            doc = json.loads(text)
            text = doc["result"]
            if not isinstance(text, str):
                raise TypeError("result is not a string")
        except (ValueError, KeyError, TypeError) as err:
            print(f"report_status could not run: invalid JSON from claude ({err}) → pass the output of claude -p --output-format json")
            return 2
    code, message = validate(text)
    print(message)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
