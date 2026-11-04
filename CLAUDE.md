# botonera

## Resuming a session

1. Read `CLAUDE.local.md` if it exists. It is not versioned and holds what is specific to this machine.
2. Read `docs/pending.md`, the single list of what is left.
3. Read the spec in progress under `docs/specs/`.

## Rules

- **Specs first:** nothing is built without an approved spec in `docs/specs/` — not enforced yet.
- **Deterministic first:** a check that can be a script, a hook or a test is written that way; an agent is used only for judgement that cannot be coded — not enforced yet.
- **One command per call:** one shell command per tool call, no chains of unrelated steps; reading commands (`cd`, `head`, `tail`, `grep`, `wc`) are allowed — not enforced yet.
- **External input:** Every external input (network, files, headers, process output) is capped in size before it is parsed; paths are confined to the project; no eval or new Function. — not enforced yet.
- **MCP servers** are declared per project in `.mcp.json`, never globally — not enforced yet.
- **Startup context:** CLAUDE.md, the files it imports with `@`, CLAUDE.local.md, the agents and `.mcp.json` add up to at most `context_kb` KB — enforced by: .checks/context.py (scripts/review)
- **Commits per phase:** each phase ends with passing checks, an up-to-date `docs/pending.md` and one commit — not enforced yet.
- **Nothing private goes out:** no private terms, personal data or secrets in commits, messages or pushes — enforced by: scripts/hooks (pre-commit, commit-msg, pre-push) and scripts/review
- **Hooks:** never commit with `--no-verify` — enforced by: scripts/hooks/pre-push, which re-checks privacy and the never-commit list on every pushed commit

## Commands

- No project commands yet.
- `scripts/setup`: install the git hooks and the tools
- `scripts/review`: aggregated review (✅ / ❗ / –)
- `scripts/agent-bench`: runs three fixed briefs with `claude -p` and compares tokens and calls with the last run; manual, it costs tokens, `scripts/review` never calls it

## Agents

- Roles: `implementer` and `reviewer`.
- At most 2 review rounds (`review_rounds` in `project.toml`).
- A fresh agent every 3 briefs (`briefs_per_agent` in `project.toml`).
- `.checks/agents.py` (in `scripts/review`) checks the agents: closed `model:` and `tools:`, no write tools in read-only roles, no pointers to `CLAUDE.local.md`.
- Every report ends with one last line, `STATUS: OK` or `STATUS: STOPPED — <reason>`; `.checks/report_status.py` validates it (and warns from the SubagentStop hook), and a report without it is never a pass.

## Configuration

<!-- generated: project.toml -->
- `name`: `botonera`
- `visibility`: `public`
- `stack`: `docs`
- `license`: `MIT`
- `docs_language`: `en+es`
- `agents`: `subagents`
- `ci`: `github`
- `claude_language`: `en`
- `review_rounds`: `2`
- `briefs_per_agent`: `3`
- `context_kb`: `40`
- `commits`: `per_phase`
- `budget.session_warn_pct`: `50`
- `budget.session_limit_pct`: `80`
- `budget.on_limit`: `ask`
<!-- end generated -->
