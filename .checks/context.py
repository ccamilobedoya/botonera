#!/usr/bin/env python3
"""Static size of the startup context (piece N08).

  context.py

Run from the project root. Adds up the bytes of CLAUDE.md, the files it imports with @path (one
level), CLAUDE.local.md, .claude/agents/*.md and .mcp.json, and compares with context_kb from
project.toml (default 40; 1 KB = 1024 bytes). Exit 0 within the cap, 1 over it, 2 could not run.
"""

import re
import subprocess
import sys
import tomllib
from pathlib import Path

sys.dont_write_bytecode = True

DEFAULT_KB = 40
IMPORT = re.compile(r"(?:^|\s)@(\S+)", re.M)


def find_root():
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        return Path(out.stdout.strip())
    except (OSError, subprocess.CalledProcessError):
        return Path.cwd()


def inside(root, path):
    """The regular file `path`, only when it resolves to a file inside the repo."""
    try:
        real = path.resolve(strict=True)
        real.relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    return real if real.is_file() else None


def size(root, path):
    real = inside(root, path)
    return real.stat().st_size if real else 0


def imports(root, text):
    seen = []
    for m in IMPORT.finditer(text):
        rel = m.group(1).rstrip(".,;:)")
        if not rel or rel.startswith("/") or "\x00" in rel:
            continue
        if rel not in seen and inside(root, root / rel):
            seen.append(rel)
    return seen


def kb(n):
    return f"{n / 1024:.1f}"


def startup_files(root):
    """The startup files as a list of (name, bytes): CLAUDE.md, its @ imports, agents (one group),
    .mcp.json and CLAUDE.local.md when it exists. Raises OSError when CLAUDE.md cannot be read."""
    groups = [("CLAUDE.md", size(root, root / "CLAUDE.md"))]
    claude = inside(root, root / "CLAUDE.md")
    if claude:
        text = claude.read_text(encoding="utf-8", errors="replace")
        for rel in imports(root, text):
            if rel not in ("CLAUDE.md", "CLAUDE.local.md"):
                groups.append((rel, size(root, root / rel)))
    agents = sum(size(root, p) for p in sorted((root / ".claude" / "agents").glob("*.md")))
    groups.append(("agents", agents))
    groups.append((".mcp.json", size(root, root / ".mcp.json")))
    if inside(root, root / "CLAUDE.local.md"):
        groups.append(("CLAUDE.local.md", size(root, root / "CLAUDE.local.md")))
    return groups


def main():
    root = find_root()
    try:
        with open(root / "project.toml", "rb") as fh:
            cap = tomllib.load(fh).get("context_kb", DEFAULT_KB)
    except (OSError, tomllib.TOMLDecodeError) as err:
        print(f"context could not run: project.toml unreadable ({err}) → fix project.toml")
        return 2
    if isinstance(cap, bool) or not isinstance(cap, int) or cap < 1:
        print("context could not run: context_kb in project.toml must be an integer ≥ 1 → fix it")
        return 2
    try:
        groups = startup_files(root)
    except OSError as err:
        print(f"context could not run: CLAUDE.md unreadable ({err}) → fix the file")
        return 2
    total = sum(n for _, n in groups)
    if total <= cap * 1024:
        print(f"context: {kb(total)} KB of {cap} KB")
        return 0
    parts = ", ".join(f"{name} {kb(n)}" for name, n in groups)
    print(f"context finding: {kb(total)} KB > {cap} KB ({parts}) → shorten them or raise context_kb in project.toml")
    return 1


if __name__ == "__main__":
    sys.exit(main())
