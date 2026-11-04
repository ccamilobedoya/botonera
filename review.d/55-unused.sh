#!/bin/sh
# Unused files, exports and dependencies (knip).

stack=$(python3 -c 'import tomllib;print(tomllib.load(open("project.toml","rb"))["stack"])') || {
  echo "unused cannot-run: cannot read the stack from project.toml → check project.toml"
  exit 2
}
if [ "$stack" = docs ]; then
  echo "SKIP: no unused-code check for stack docs"
  exit 0
fi
tool=node_modules/.bin/knip
if [ ! -x "$tool" ]; then
  echo "knip cannot-run: not installed → run scripts/setup"
  exit 2
fi
"$tool"
rc=$?
case $rc in
  0) exit 0 ;;
  1)
    echo "unused finding: knip reported unused code → remove it"
    exit 1
    ;;
  *) exit 2 ;;
esac
