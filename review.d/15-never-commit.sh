#!/bin/sh
# Files that must never be in the repository (keys, .env files, local settings).

if ! python3 .checks/never_commit.py --self-test >/dev/null 2>&1; then
  echo "never-commit cannot-run: self-test failed → the list or the matcher is broken"
  exit 2
fi
python3 .checks/never_commit.py --tree
exit $?
