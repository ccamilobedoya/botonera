#!/bin/sh
# Private terms, personal data and secret shapes in every tracked and untracked file.

if ! python3 .checks/privacy.py --self-test >/dev/null 2>&1; then
  echo "privacy cannot-run: self-test failed → the scanner is broken"
  exit 2
fi
python3 .checks/privacy.py --tree
exit $?
