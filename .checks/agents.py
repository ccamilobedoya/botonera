#!/usr/bin/env python3
"""Static check of the project's agents (piece A02).

  agents.py

Run from the project root. Reads project.toml, .mcp.json and .claude/agents/*.md. Prints one
line per finding, naming the agent and the tool. Exit 0 all good (or no agents by design),
1 findings, 2 could not run.
"""

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

sys.dont_write_bytecode = True

KNOWN_TOOLS = {
    "Agent", "Task", "Bash", "BashOutput", "KillShell", "Edit", "MultiEdit", "Write", "Read",
    "NotebookEdit", "NotebookRead", "Glob", "Grep", "LS", "WebFetch", "WebSearch", "TodoWrite",
    "ExitPlanMode", "Skill", "SlashCommand", "ToolSearch", "Monitor",
}
READONLY_TEXT = re.compile(r"read-only|read only|solo lectura|never applies|nunca aplica", re.I)
WRITE_BUILTIN = {"Edit", "Write", "MultiEdit", "NotebookEdit", "Bash"}
# Words (split on _ and -) that make an MCP tool a writer: `set_note` writes, `get_settings` does not.
WRITE_WORDS = {"apply", "write", "create", "delete", "update", "undo", "remove", "edit", "set", "move",
               "put", "patch", "append", "rename", "insert", "upload"}
LOCAL_FILE = "CLAUDE.local.md"
KEY_LINE = re.compile(r"^([A-Za-z][\w-]*):[ \t]*(.*)$")


def find_root():
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        return Path(out.stdout.strip())
    except (OSError, subprocess.CalledProcessError):
        return Path.cwd()


def parse_frontmatter(text):
    """Flat `key: value` subset. Returns (dict, problem) where problem is None when fine."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "no frontmatter"
    fm = {}
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            return fm, None
        if not line.strip():
            continue
        m = KEY_LINE.match(line)
        if not m:
            return None, f"frontmatter outside the supported subset (line {i + 1}: use flat `key: value` lines)"
        if not m.group(2).strip():
            return None, f"frontmatter outside the supported subset (`{m.group(1)}:` has no value on its line)"
        fm[m.group(1)] = m.group(2).strip()
    return None, "frontmatter is not closed with ---"


def check_agent(path, servers, by_role):
    name = path.stem
    text = path.read_text(encoding="utf-8")
    problems = []
    fm, problem = parse_frontmatter(text)
    if problem:
        problems.append(f"agents finding: {name}: {problem} → use flat key: value lines between --- marks")
        fm = {}
    wanted = by_role.get(name)
    if fm.get("model") and isinstance(wanted, str) and fm["model"] != wanted:
        problems.append(f"agents finding: {name}: model: {fm['model']} but model_by_role says {wanted} "
                        f"→ make both the same (one configuration)")
    for key in ("name", "description", "model", "tools"):
        if problem is None and not fm.get(key):
            problems.append(f"agents finding: {name}: missing {key}: → add `{key}:` to the frontmatter")
    tools = [t.strip() for t in fm.get("tools", "").strip("[]").split(",") if t.strip()]
    readonly = READONLY_TEXT.search(text) is not None
    for raw in tools:
        tool = re.sub(r"\(.*\)$", "", raw)
        if tool.startswith("mcp__"):
            parts = tool.split("__")
            server = parts[1] if len(parts) > 1 else ""
            if not server or server not in servers:
                problems.append(f"agents finding: {name}: {raw} — server {server or '?'} is not in .mcp.json "
                                f"→ declare it there or drop the tool")
                continue
            writes = len(parts) > 2 and bool(WRITE_WORDS & set(re.split(r"[_-]", parts[-1].lower())))
        elif tool in KNOWN_TOOLS:
            writes = tool in WRITE_BUILTIN
        else:
            problems.append(f"agents finding: {name}: unknown tool {raw} → fix the name in tools:")
            continue
        if readonly and writes:
            problems.append(f"agents finding: {name}: read-only but has {raw} → remove it from tools:")
    if LOCAL_FILE in text:
        problems.append(f"agents finding: {name}: mentions {LOCAL_FILE}, which is not versioned "
                        f"→ put what it needs in a versioned file")
    return problems


def main():
    root = find_root()
    try:
        with open(root / "project.toml", "rb") as fh:
            config = tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError) as err:
        print(f"agents could not run: project.toml unreadable ({err}) → fix project.toml")
        return 2
    servers = set()
    mcp = root / ".mcp.json"
    if mcp.is_file():
        try:
            data = json.loads(mcp.read_text(encoding="utf-8"))
            servers = set((data.get("mcpServers") or {}).keys())
        except (OSError, ValueError, AttributeError) as err:
            print(f"agents could not run: .mcp.json unreadable ({err}) → fix .mcp.json")
            return 2
    files = sorted((root / ".claude" / "agents").glob("*.md"))
    if not files:
        if config.get("agents") == "subagents":
            print("agents finding: no agents in .claude/agents → add the roles or set agents = \"none\"")
            return 1
        print('SKIP: no agents (agents = "none")')
        return 0
    by_role = config.get("model_by_role")
    by_role = by_role if isinstance(by_role, dict) else {}
    problems = []
    for path in files:
        try:
            problems += check_agent(path, servers, by_role)
        except (OSError, UnicodeDecodeError) as err:
            print(f"agents could not run: {path.name} unreadable ({err}) → fix the file")
            return 2
    if problems:
        print("\n".join(problems))
        return 1
    print(f"agents: {len(files)} agents checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
