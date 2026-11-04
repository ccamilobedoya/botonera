#!/bin/sh
# Unit tests (node --test). A skipped test is a finding unless ALLOW_SKIPS=1.

stack=$(python3 -c 'import tomllib;print(tomllib.load(open("project.toml","rb"))["stack"])') || {
  echo "tests cannot-run: cannot read the stack from project.toml → check project.toml"
  exit 2
}
if [ "$stack" = docs ]; then
  echo "SKIP: no tests for stack docs"
  exit 0
fi
if ! command -v node >/dev/null 2>&1; then
  echo "tests cannot-run: node not found → install Node.js"
  exit 2
fi

out=$(node --test --test-reporter=tap 2>&1)
rc=$?
summary() {
  printf '%s\n' "$out" | sed -n "s/^# $1 \([0-9][0-9]*\).*/\1/p" | tail -n 1
}
tests=$(summary tests)
fail=$(summary fail)
skipped=$(summary skipped)
[ -n "$skipped" ] || skipped=$(summary skip)
if [ -z "$tests" ] || [ -z "$fail" ]; then
  printf '%s\n' "$out"
  echo "tests cannot-run: no TAP summary from node --test → run npm test to see why"
  exit 2
fi
if [ "$fail" -gt 0 ]; then
  printf '%s\n' "$out"
  echo "tests finding: $fail failing → fix the failing tests"
  exit 1
fi
if [ "$rc" -ne 0 ]; then
  printf '%s\n' "$out"
  echo "tests finding: node --test exited with $rc → run npm test to see why"
  exit 1
fi
if [ -n "$skipped" ] && [ "$skipped" -gt 0 ]; then
  if [ "$skipped" -eq 1 ]; then noun="test"; else noun="tests"; fi
  if [ "${ALLOW_SKIPS:-}" = 1 ]; then
    echo "WARN: $skipped skipped $noun allowed by ALLOW_SKIPS=1"
  else
    printf '%s\n' "$out"
    echo "tests finding: $skipped skipped $noun → remove the skip or run with ALLOW_SKIPS=1"
    exit 1
  fi
fi
echo "tests pass: $tests tests"
exit 0
