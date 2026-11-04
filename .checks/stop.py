#!/usr/bin/env python3
"""Claude Code Stop hook: warn when too many lines are not committed.

Counts added + deleted lines of tracked files (against HEAD, or the empty tree
before the first commit) plus the lines of untracked files that are not
ignored. Over `commit_warn_lines` in project.toml (default 200) it prints a
systemMessage. It never commits and never runs `git add`. Any error goes to
stderr; the exit code is always 0.
"""

import json
import os
import subprocess
import sys
import tomllib

DEFAULT_LIMIT = 200
FILE_CAP = 1024 * 1024


def git(root, *args):
    proc = subprocess.run(["git", "-c", "core.quotepath=off", *args], cwd=root, capture_output=True)
    return proc


def project_root():
    start = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    proc = git(start, "rev-parse", "--show-toplevel")
    if proc.returncode != 0:
        return None
    return os.fsdecode(proc.stdout.strip())


def limit(root):
    try:
        with open(os.path.join(root, "project.toml"), "rb") as fh:
            value = tomllib.load(fh).get("commit_warn_lines", DEFAULT_LIMIT)
    except (OSError, tomllib.TOMLDecodeError):
        return DEFAULT_LIMIT
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else DEFAULT_LIMIT


def tracked_lines(root):
    base = "HEAD"
    if git(root, "rev-parse", "--verify", "-q", "HEAD").returncode != 0:
        base = git(root, "hash-object", "-t", "tree", "/dev/null").stdout.decode().strip()
    proc = git(root, "diff", base, "--numstat")
    if proc.returncode != 0:
        raise RuntimeError("git diff failed")
    total = 0
    for line in proc.stdout.decode("utf-8", "replace").splitlines():
        added, deleted = line.split("\t")[:2]
        total += int(added) if added.isdigit() else 0
        total += int(deleted) if deleted.isdigit() else 0
    return total


def untracked_lines(root):
    proc = git(root, "ls-files", "-z", "--others", "--exclude-standard")
    total = 0
    for raw in proc.stdout.split(b"\0"):
        if not raw:
            continue
        path = os.path.join(root, os.fsdecode(raw))
        try:
            if os.path.islink(path) or not os.path.isfile(path):
                continue
            with open(path, "rb") as fh:
                data = fh.read(FILE_CAP)
        except OSError:
            continue
        if b"\0" in data[:8192]:
            continue
        total += data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)
    return total


def main():
    root = project_root()
    if root is None:
        return
    total = tracked_lines(root) + untracked_lines(root)
    warn_at = limit(root)
    if total > warn_at:
        message = f"{total} lines not committed (limit {warn_at}, commit_warn_lines in project.toml) → commit at the end of the phase"
        print(json.dumps({"systemMessage": message}))


if __name__ == "__main__":
    try:
        main()
    except Exception as err:  # a warning hook must never get in the way
        print(f"stop hook error: {type(err).__name__}: {err}", file=sys.stderr)
    sys.exit(0)
