#!/bin/sh
# Dependency licences: production dependencies against allowed_licenses, with license-exceptions.toml. Offline.

if ! command -v python3 >/dev/null 2>&1; then
  echo "licenses cannot-run: python3 not found → install Python 3.11+"
  exit 2
fi
python3 .checks/licenses.py
exit $?
