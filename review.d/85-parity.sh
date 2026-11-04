#!/bin/sh
# Parity of the bilingual documents: every X.es.md has an X.md with the same heading structure.

if ! command -v python3 >/dev/null 2>&1; then
  echo "parity cannot-run: python3 not found → install Python 3.11+"
  exit 2
fi
python3 .checks/doc_parity.py
exit $?
