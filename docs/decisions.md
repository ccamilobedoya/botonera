# Decisions

Log of the decisions that shape this project. One entry per decision, numbered `D-NNN`, newest last. Entries are never deleted: a decision that stops applying is replaced.

Each entry is a `##` heading followed by:

- **Status:** `proposed`, `accepted` or `replaced by D-NNN`.
- **Date:** when the status last changed.

An entry that replaces another says "replaces D-NNN"; the replaced one changes its status to "replaced by D-NNN".

## D-001 · Project structure

- **Status:** accepted
- **Date:** 2026-11-04

Project options live in `project.toml`. Specs live in `docs/specs/`, what is left in `docs/pending.md` and decisions in this file.

## D-002 · Specs before code

- **Status:** accepted
- **Date:** 2026-11-04

Nothing is built without an approved spec. A spec closes when its acceptance criteria pass; closed specs keep no pending items.
