#!/bin/sh
# The index of the documents lists every document under docs/ (docs/README.md, between its markers).

if ! command -v python3 >/dev/null 2>&1; then
  echo "docs-index cannot-run: python3 not found → install Python 3.11+"
  exit 2
fi
python3 .checks/docs_index.py --check
exit $?
