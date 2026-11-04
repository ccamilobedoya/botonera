#!/bin/sh
# Startup context: CLAUDE.md, its @ imports, CLAUDE.local.md, agents and .mcp.json within context_kb.

if ! command -v python3 >/dev/null 2>&1; then
  echo "context cannot-run: python3 not found → install Python 3.11+"
  exit 2
fi
python3 .checks/context.py
exit $?
