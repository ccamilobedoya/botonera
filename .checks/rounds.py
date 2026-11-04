#!/usr/bin/env python3
"""Rounds without progress (piece B03): the same checks failing run after run.

  rounds.py --record [<check> ...]

Records the checks that ended in red (finding or could not run) in one review run, in
.checks/state/review-runs.jsonl. When the last budget.max_rounds_without_progress + 1 runs
share the same non-empty set, it prints a warning. Always exits 0.
"""

import json
import os
import sys
import time
import tomllib
from pathlib import Path

DEFAULT_ROUNDS = 2
KEEP_RUNS = 50


def max_rounds(root):
    try:
        with open(root / "project.toml", "rb") as fh:
            value = (tomllib.load(fh).get("budget") or {}).get("max_rounds_without_progress", DEFAULT_ROUNDS)
        return value if isinstance(value, int) and value >= 1 else DEFAULT_ROUNDS
    except (OSError, ValueError):
        return DEFAULT_ROUNDS


def load_runs(path):
    runs = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                runs.append(sorted(json.loads(line)["failed"]))
            except (ValueError, KeyError, TypeError):
                continue
    except OSError:
        pass
    return runs


def record(root, checks):
    path = root / ".checks" / "state" / "review-runs.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    failed = sorted(set(checks))
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "failed": failed}) + "\n")
    runs = load_runs(path)
    if len(runs) > KEEP_RUNS:
        path.write_text("".join(json.dumps({"failed": r}) + "\n" for r in runs[-KEEP_RUNS:]), encoding="utf-8")
    limit = max_rounds(root)
    last = runs[-(limit + 1):]
    if failed and len(last) == limit + 1 and all(r == failed for r in last):
        return (f"rounds: the last {limit + 1} reviews ended with the same checks in red "
                f"→ change approach: {', '.join(failed)} (budget.max_rounds_without_progress = {limit})")
    return None


def main(argv):
    if not argv or argv[0] != "--record":
        raise ValueError("usage: rounds.py --record [<check> ...]")
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".")
    message = record(root, argv[1:])
    if message:
        print(message)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as exc:  # noqa: BLE001
        print(f"B03 cannot-run: {type(exc).__name__}: {exc} → rounds not recorded", file=sys.stderr)
    sys.exit(0)
