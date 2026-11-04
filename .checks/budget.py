#!/usr/bin/env python3
"""Budget thresholds and cache warning (piece B02). Hooks: they never block the main session.

  budget.py --pre-tool        PreToolUse: only Agent/Task calls can be asked or denied
  budget.py --stop            Stop: threshold warning and cache warning (never a decision)
  budget.py --session-start   SessionStart: remember the hashes of the files that break the cache

Always exits 0; an internal error is one line on stderr and no decision.
"""

import hashlib
import json
import os
import sys
import tomllib
from pathlib import Path

sys.dont_write_bytecode = True  # this folder is copied into projects: leave no cache in it
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import context  # noqa: E402  sits next to this script
import usage  # noqa: E402

DEFAULTS = {"session_warn_pct": 50, "session_limit_pct": 80, "on_limit": "warn", "cache_warn_pct": 80,
            "cache_min_turns": 10, "session_tokens": 0,
            "startup_tokens": 0}
WATCHED = ("CLAUDE.md", ".claude/settings.json", ".mcp.json")
KEEP_SESSIONS = 20


def load_budget(root):
    with open(root / "project.toml", "rb") as fh:
        table = tomllib.load(fh).get("budget") or {}
    return {**DEFAULTS, **table}


def read_state(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def write_state(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    while len(data) > KEEP_SESSIONS:
        del data[next(iter(data))]
    tmp = path.with_name(path.name + f".{os.getpid()}")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    os.replace(tmp, path)


def session_percentage(budget, state_dir, session_id, transcript):
    """(percentage, 'real' | 'estimated') or (None, None) when there is nothing to measure with."""
    snap = usage.statusline_snapshot(state_dir, session_id)
    five = ((snap or {}).get("rate_limits") or {}).get("five_hour") or {}
    if isinstance(five.get("used_percentage"), (int, float)):
        return five["used_percentage"], "real"
    limit = budget["session_tokens"]
    if not limit or not transcript:
        return None, None
    path = Path(transcript)
    parts = [usage.summarize(path)] + usage.subagents(path)
    used = sum(p["tokens"][k] for p in parts
               for k in ("input_tokens", "cache_creation_input_tokens", "output_tokens"))
    return used / limit * 100, "estimated"


def threshold(budget, pct, source, tool_decision):
    """Output dict for the percentage, or None. tool_decision: this call may be asked/denied."""
    label = f"{pct:.0f}%" + (" (estimated)" if source == "estimated" else "")
    warn, limit, action = budget["session_warn_pct"], budget["session_limit_pct"], budget["on_limit"]
    if pct >= limit:
        msg = f"Budget: session at {label}, over the limit of {limit}% (on_limit = {action})"
        if tool_decision and action == "ask":
            return decision("ask", f"{msg} → confirm to launch this agent, or raise budget.session_limit_pct")
        if tool_decision and action == "stop":
            return decision("deny", f"{msg} → raise budget.session_limit_pct or start a new session")
        return {"systemMessage": f"{msg} → raise budget.session_limit_pct if this is expected"}
    if pct >= warn:
        return {"systemMessage": f"Budget: session at {label}, over the warning of {warn}% "
                                 f"→ tune budget.session_warn_pct or wrap up"}
    return None


def decision(kind, reason):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": kind,
                                   "permissionDecisionReason": reason}}


def no_data_message(state_dir, session_id):
    path = state_dir / "budget-nodata.json"
    seen = read_state(path)
    if session_id in seen:
        return None
    seen[session_id] = True
    write_state(path, seen)
    return ("Budget: no percentage to compare (no fresh statusline snapshot and budget.session_tokens = 0) "
            "→ set budget.session_tokens to enable the estimate")


def startup_warning(budget, root, state_dir, session_id, transcript):
    """Once per session: the first API call is bigger than budget.startup_tokens."""
    cap = budget["startup_tokens"]
    if not isinstance(cap, int) or cap <= 0 or not transcript:
        return None
    first = usage.summarize(Path(transcript))["startup_tokens"]
    if first is None or first <= cap:
        return None
    path = state_dir / "budget-startup.json"
    seen = read_state(path)
    if session_id in seen:
        return None
    seen[session_id] = True
    write_state(path, seen)
    try:
        files = context.startup_files(root)
    except OSError:
        files = []
    guess = {name: n // 4 for name, n in files}
    detail = ", ".join(f"{name} {n:,}" for name, n in guess.items())
    rest = max(0, first - sum(guess.values()))
    return (f"Startup: {first:,} tokens in the first call (cap {cap:,}; first prompt included). "
            f"Files ≈ {sum(guess.values()):,} tokens estimated from bytes/4 ({detail}); the rest ≈ {rest:,} is "
            f"system prompt, tools, MCP servers and skills → check for unused MCP servers, plugins and agents, "
            f"trim CLAUDE.md, or raise budget.startup_tokens")


def hashes(root):
    out = {}
    for name in WATCHED:
        try:
            out[name] = hashlib.sha256((root / name).read_bytes()).hexdigest()
        except OSError:
            out[name] = None
    try:
        plugins = json.loads((root / ".claude" / "settings.json").read_text(encoding="utf-8")).get("enabledPlugins")
    except (OSError, ValueError, AttributeError):
        plugins = None
    out["enabledPlugins"] = hashlib.sha256(json.dumps(plugins, sort_keys=True).encode()).hexdigest()
    return out


def cache_warning(budget, root, state_dir, session_id, transcript):
    if not transcript:
        return None
    main = usage.summarize(Path(transcript))
    rate = main["cache_hit_rate"]
    if rate is None or main["messages"] < budget["cache_min_turns"] or rate >= budget["cache_warn_pct"] / 100:
        return None
    before = read_state(state_dir / "budget-session.json").get(session_id)
    now = hashes(root)
    edited = bool(before) and (before.get("CLAUDE.md") != now["CLAUDE.md"]
                               or before.get(".claude/settings.json") != now[".claude/settings.json"])
    mcp = bool(before) and (before.get(".mcp.json") != now[".mcp.json"]
                            or before.get("enabledPlugins") != now["enabledPlugins"])
    switched = len(main["models"]) > 1
    mark = lambda flag: " (detected)" if flag else ""  # noqa: E731
    return "\n".join([
        f"Cache: {round(rate * 100)}% (expected ≥ {budget['cache_warn_pct']}%) in {main['messages']} turns. Possible causes:",
        f"  - CLAUDE.md or .claude/settings.json edited during the session{mark(edited)}",
        f"  - MCP server or tool added (.mcp.json or enabledPlugins changed){mark(mcp)}",
        f"  - model changed during the session{mark(switched)}",
        "  → every one of these rebuilds the cached prefix: finish such changes before starting a session.",
    ])


def main(argv):
    mode = argv[0] if argv else ""
    data = json.load(sys.stdin)
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or ".")
    state_dir = root / ".checks" / "state"
    session_id = data.get("session_id") or "?"
    if mode == "--session-start":
        path = state_dir / "budget-session.json"
        sessions = read_state(path)
        sessions.pop(session_id, None)
        sessions[session_id] = hashes(root)
        write_state(path, sessions)
        return None
    if mode not in ("--pre-tool", "--stop"):
        raise ValueError(f"unknown mode {mode!r}")
    if mode == "--pre-tool" and data.get("tool_name") not in ("Agent", "Task"):
        return None
    budget = load_budget(root)
    transcript = data.get("transcript_path")
    pct, source = session_percentage(budget, state_dir, session_id, transcript)
    messages, result = [], None
    if pct is None:
        note = no_data_message(state_dir, session_id)
        if note:
            messages.append(note)
    else:
        result = threshold(budget, pct, source, mode == "--pre-tool")
    if mode == "--stop":
        cache = cache_warning(budget, root, state_dir, session_id, transcript)
        if cache:
            messages.append(cache)
        startup = startup_warning(budget, root, state_dir, session_id, transcript)
        if startup:
            messages.append(startup)
    if result and "hookSpecificOutput" in result:
        return result
    if result:
        messages.insert(0, result["systemMessage"])
    return {"systemMessage": "\n".join(messages)} if messages else None


if __name__ == "__main__":
    try:
        out = main(sys.argv[1:])
        if out:
            print(json.dumps(out, ensure_ascii=False))
    except Exception as exc:  # noqa: BLE001
        print(f"B02 cannot-run: {type(exc).__name__}: {exc} → no budget check this time", file=sys.stderr)
    sys.exit(0)
