# Decisions

Log of the decisions that shape this project. One entry per decision, numbered `D-NNN`, newest last. Entries are never deleted: a decision that stops applying is replaced. The full records (context, decision, consequences) are the ADRs in `docs/adr/`, in Spanish.

Each entry is a `##` heading followed by:

- **Status:** `proposed`, `accepted` or `replaced by D-NNN`.
- **Date:** when the status last changed.

## D-001 · Project structure

- **Status:** accepted
- **Date:** 2026-11-04

Project options live in `project.toml`. Specs live in `docs/specs/` (in Spanish, from `TEMPLATE.md`), what is left in `docs/pending.md`, decisions in this file with their ADR in `docs/adr/`, the development cycle in `docs/process.md`.

## D-002 · Specs before code

- **Status:** accepted
- **Date:** 2026-11-04

Nothing is built without a spec approved by the owner (ADR-0001). A spec closes when its acceptance criteria pass; closed specs keep no pending items.

## D-003 · Owner approves the stack (ADR-0001)

- **Status:** accepted
- **Date:** 2026-11-04

## D-004 · Name and languages (ADR-0002)

- **Status:** accepted
- **Date:** 2026-11-04

## D-005 · MIT licence and the QMK userspace files (ADR-0003)

- **Status:** accepted
- **Date:** 2026-11-04

## D-006 · QMK as an external userspace pinned to a commit (ADR-0004)

- **Status:** accepted
- **Date:** 2026-11-04

## D-007 · TinyUSB experiment only to learn (ADR-0005)

- **Status:** accepted
- **Date:** 2026-11-04

## D-008 · Per-OS commands: manual layer over the enumeration fingerprint (ADR-0006)

- **Status:** accepted
- **Date:** 2026-11-04

## D-009 · Agent workflow; commits and pushes by the integrator only (ADR-0007)

- **Status:** accepted
- **Date:** 2026-11-04

## D-010 · Nothing private in the repository (ADR-0008)

- **Status:** accepted
- **Date:** 2026-11-04

## D-011 · Test hooks only in test builds (ADR-0009)

- **Status:** accepted
- **Date:** 2026-11-04
