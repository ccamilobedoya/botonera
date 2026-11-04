#!/bin/sh
# Agents: closed model: and tools:, read-only roles without write tools, no pointers to CLAUDE.local.md.

if ! command -v python3 >/dev/null 2>&1; then
  echo "agents cannot-run: python3 not found → install Python 3.11+"
  exit 2
fi
python3 .checks/agents.py
exit $?
