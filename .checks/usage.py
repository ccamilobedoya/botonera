#!/usr/bin/env python3
"""Usage log (piece B01): tokens, cache hit rate and calls per session and subagent.

Reads only what Claude Code already writes (the session transcript and its
subagents/ folder) and calls no model (R10). One line per session in
.checks/state/usage.jsonl, rewritten on every Stop/SubagentStop.

Each summarized transcript also has startup_tokens: the whole input (fresh + cache writes + cache
reads) of its first API message, i.e. what the session loaded before doing anything (None when
there is no assistant message). The schema stays 1: the key is additive.

  usage.py --hook                       hook mode: JSON on stdin, always exits 0
  usage.py --transcript <file.jsonl> [--out <usage.jsonl>]
                                        0 written · 2 could not read the transcript
"""

import argparse
import fcntl
import json
import os
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

SCHEMA = 1
TOKEN_KEYS = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
STATUSLINE_MAX_AGE_S = 600


def read_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except ValueError:
                    continue  # a line cut by a crash is skipped, not fatal


def is_prompt(entry):
    """A person's message: not a tool result, not injected by the harness."""
    if entry.get("type") != "user" or entry.get("isMeta"):
        return False
    content = entry.get("message", {}).get("content")
    if isinstance(content, str):
        return True
    return isinstance(content, list) and not any(c.get("type") == "tool_result" for c in content)


def summarize(path):
    """Totals of one transcript. One API message spans several lines with the same
    message.id and the same usage: it is counted once."""
    usage = {}
    tools, mcp, skills, agents = Counter(), Counter(), Counter(), Counter()
    seen_blocks, models, prompts = set(), set(), 0
    first_id = None
    for entry in read_jsonl(path):
        if is_prompt(entry):
            prompts += 1
        if entry.get("type") != "assistant":
            continue
        msg = entry.get("message", {})
        if msg.get("id") and isinstance(msg.get("usage"), dict):
            usage[msg["id"]] = msg["usage"]
            if first_id is None:
                first_id = msg["id"]
        if msg.get("model") and not msg["model"].startswith("<"):
            models.add(msg["model"])
        for block in msg.get("content") or []:
            if block.get("type") != "tool_use" or block.get("id") in seen_blocks:
                continue
            seen_blocks.add(block.get("id"))
            name, args = block.get("name", "?"), block.get("input") or {}
            tools[name] += 1
            if name.startswith("mcp__"):
                mcp[name.split("__")[1]] += 1
            elif name == "Skill":
                skills[args.get("skill", "?")] += 1
            elif name in ("Agent", "Task"):
                agents[args.get("subagent_type") or "general-purpose"] += 1
    tokens = {k: sum(u.get(k) or 0 for u in usage.values()) for k in TOKEN_KEYS}
    return {
        "models": sorted(models),
        "prompts": prompts,
        "messages": len(usage),
        "tokens": tokens,
        "startup_tokens": startup_tokens(usage.get(first_id)),
        "cache_hit_rate": cache_hit_rate(tokens),
        "calls": {"tool": dict(tools), "mcp": dict(mcp), "skill": dict(skills), "agent": dict(agents)},
    }


def startup_tokens(first):
    if not first:
        return None
    return sum(first.get(k) or 0 for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))


def cache_hit_rate(tokens):
    """Cache reads over all input (fresh + cache writes + cache reads), decision 19."""
    total = tokens["input_tokens"] + tokens["cache_creation_input_tokens"] + tokens["cache_read_input_tokens"]
    return round(tokens["cache_read_input_tokens"] / total, 4) if total else None


def subagents(transcript):
    folder = transcript.with_suffix("") / "subagents"
    found = []
    for path in sorted(folder.glob("agent-*.jsonl")):
        meta_path = path.with_name(path.stem + ".meta.json")
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            meta = {}
        found.append({
            "id": path.stem.removeprefix("agent-"),
            "type": meta.get("agentType"),
            "description": meta.get("description"),
        } | summarize(path))
    return found


def statusline_snapshot(state_dir, session_id):
    """Real cost and rate limits, only from a fresh snapshot of this same session."""
    try:
        snap = json.loads((state_dir / "statusline.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if snap.get("input", {}).get("session_id") != session_id:
        return None
    if time.time() - snap.get("received_at", 0) > STATUSLINE_MAX_AGE_S:
        return None
    data = snap["input"]
    return {
        "cost_usd": (data.get("cost") or {}).get("total_cost_usd"),
        "rate_limits": data.get("rate_limits"),
        "context_used_pct": (data.get("context_window") or {}).get("used_percentage"),
        "received_at": snap["received_at"],
    }


def record(transcript, session_id, state_dir):
    main = summarize(transcript)
    subs = subagents(transcript)
    total = {k: main["tokens"][k] + sum(s["tokens"][k] for s in subs) for k in TOKEN_KEYS}
    return {
        "schema": SCHEMA,
        "session": session_id,
        "updated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "main": main,
        "subagents": subs,
        "total": {"tokens": total, "cache_hit_rate": cache_hit_rate(total)},
        "statusline": statusline_snapshot(state_dir, session_id),
    }


def upsert(out, rec):
    """Replace this session's line (or append it), under a lock, atomically."""
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out.with_suffix(".lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        lines = []
        if out.exists():
            lines = [l for l in out.read_text(encoding="utf-8").splitlines()
                     if l.strip() and _session_of(l) != rec["session"]]
        lines.append(json.dumps(rec, ensure_ascii=False, sort_keys=True))
        fd, tmp = tempfile.mkstemp(dir=out.parent, prefix=".usage-")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        os.replace(tmp, out)


def _session_of(line):
    try:
        return json.loads(line).get("session")
    except ValueError:
        return None


def run(transcript, session_id, out):
    rec = record(Path(transcript), session_id or Path(transcript).stem, Path(out).parent)
    upsert(Path(out), rec)
    return rec


def default_out(project_dir):
    return Path(project_dir) / ".checks" / "state" / "usage.jsonl"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--hook", action="store_true")
    p.add_argument("--transcript")
    p.add_argument("--session")
    p.add_argument("--out")
    args = p.parse_args(argv)
    if args.hook:
        # A Stop hook that exits 2 would keep the session going: never block, only warn.
        try:
            data = json.load(sys.stdin)
            project = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or "."
            run(data["transcript_path"], data.get("session_id"), args.out or default_out(project))
        except Exception as exc:  # noqa: BLE001
            print(f"B01 cannot-run: {type(exc).__name__}: {exc} → usage not logged this turn", file=sys.stderr)
        return 0
    if not args.transcript:
        p.error("--transcript or --hook is required")
    try:
        run(args.transcript, args.session, args.out or default_out("."))
    except (OSError, ValueError, KeyError) as exc:
        print(f"B01 cannot-run: {exc} → check the transcript path", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
