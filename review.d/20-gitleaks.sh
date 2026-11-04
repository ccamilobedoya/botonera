#!/bin/sh
# Secrets in the working tree, with gitleaks.

gitleaks=.checks/bin/gitleaks
[ -x "$gitleaks" ] || gitleaks=$(command -v gitleaks 2>/dev/null) || gitleaks=""
if [ -z "$gitleaks" ]; then
  echo "gitleaks could not run: run scripts/setup"
  exit 2
fi
"$gitleaks" dir . --redact --no-banner --exit-code 1
rc=$?
case $rc in
  0 | 1) exit "$rc" ;;
  *) exit 2 ;;
esac
