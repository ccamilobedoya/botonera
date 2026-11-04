# Botonera

Desk macropad on an RP2040 that Windows, iPadOS and macOS see as a plain keyboard, with no driver, and that sends different commands per operating system. The product firmware is QMK (external userspace in `firmware/`); the experiments under `experiments/` teach or measure and are never shipped. Design, status and private context live in the owner's knowledge base, not here.

## Resuming a session

1. Read `CLAUDE.local.md` if it exists. It is not versioned and says where the status note and the private pointers are. Without it (fresh clone), ask the owner for the pointer before working.
2. Read `docs/pending.md`, the single list of what is left, and the spec in progress under `docs/specs/`.
3. `docs/process.md` says how a spec moves from approval to `main`; `docs/MAP.md` says what is in each folder.

## Rules for everyone

- **The spec rules.** Only what an approved spec (`docs/specs/F-NNN-*.md`) says gets programmed. If something does not fit, stop and report.
- **ADRs bind** (`docs/adr/`, index in `docs/decisions.md`). Security rules are in `docs/security.md`.
- **Languages** (ADR-0002): code, identifiers, comments, file names, README and everything public in **English**; specs, ADRs, reports and process documents in **Spanish**.
- **Commits and pushes are made only by the `integrator` agent**, at the end of each phase. Nobody else (not even the architect) commits or pushes. Never `--force`, `reset` or `rebase` — enforced by: `.checks/block_secrets.py` and `tools/launch-agent` (closed tool lists).
- **Nothing private goes out:** no private terms, personal data, local paths or secrets in commits, messages or pushes; the owner's personal keymap lives outside the repository — enforced by: scripts/hooks (pre-commit, commit-msg, pre-push) and scripts/review.
- **Builds run in pinned containers** (`tools/build`); nothing is installed on the owner's PC; containers have no network and no USB — enforced by: `tools/build` (`--network none`, digests in `docker/`).
- **Every input from the host is size-capped before it is parsed** (S1) and **test hooks exist only in test builds** (S2) — enforced by: `review.d/36-firmware-artifacts.sh` for the artifacts; the rest by the reviewer.
- **One command per call:** one shell command per tool call, no chains of unrelated steps; reading commands (`cd`, `head`, `tail`, `grep`, `wc`) are allowed — not enforced yet.
- **No temporary files** in the repository: delete what you created to test before delivering.
- **No background tasks** in agents: a task that ends later reopens the session and the report is lost.
- **Hooks:** never commit with `--no-verify` — enforced by: scripts/hooks/pre-push, which re-checks privacy and the never-commit list on every pushed commit.
- **Startup context:** CLAUDE.md, the files it imports with `@`, CLAUDE.local.md, the agents and `.mcp.json` add up to at most `context_kb` KB — enforced by: .checks/context.py (scripts/review)

## Who touches what (checked by `tools/check-scope`)

- **Programmer:** `firmware/`, `experiments/`, `tools/host/` and unit tests. Never `docs/specs/`, `docs/adr/`, `docs/templates/`, `tests/acceptance/`, `tests/agents/`, `tools/` (except `tools/host/`), `.claude/`, `CLAUDE.md`.
- **Verifier:** only `tests/acceptance/`.
- **Reviewer:** nothing.
- **Architect** (main session): specs, ADRs, reports, agents, tools and this file (writes them; the integrator saves them).
- **Integrator:** git only; changes no file.

## Commands

- `tools/build qmk | hid-from-scratch | blink`: compile in pinned containers; output in `build/`
- `npm ci && npm run typecheck && npm test && npm run format:check`: the Node tooling under `tools/`
- `tools/check-scope <role> [--base <ref>]`: did the role change only what it owns?
- `tools/launch-agent <role> <model> <folder> <brief> [cap-usd]` · `tools/integrator-brief …`: run the cycle (`docs/process.md`)
- `tools/publish-spec docs/specs/F-NNN-*.md`: copy a spec to the owner's knowledge base
- `tools/map`: regenerate `docs/MAP.md`
- `scripts/setup`: install the git hooks and the tools
- `scripts/review`: aggregated review (✅ / ❗ / –)
- `scripts/agent-bench`: runs three fixed briefs with `claude -p` and compares tokens and calls with the last run; manual, it costs tokens, `scripts/review` never calls it

## Agents

- Roles: `programmer`, `verifier`, `reviewer`, `integrator` (`.claude/agents/`), launched with `tools/launch-agent` and a closed tool list.
- At most 2 review rounds (`review_rounds` in `project.toml`); three verification rounds without passing stop the spec.
- A fresh agent every 3 briefs (`briefs_per_agent` in `project.toml`).
- `.checks/agents.py` (in `scripts/review`) checks the agents: closed `model:` and `tools:`, no write tools in read-only roles, no pointers to `CLAUDE.local.md`.
- Every report ends with a status: `**Status:** OK` or `**Status:** STOPPED` for the integrator (checked by `tools/launch-agent`), and the fixed templates of `docs/templates/` for the others; a report without it is never a pass.

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
