#!/bin/sh
# Test coverage against the thresholds in .c8rc.json (c8).

stack=$(python3 -c 'import tomllib;print(tomllib.load(open("project.toml","rb"))["stack"])') || {
  echo "coverage cannot-run: cannot read the stack from project.toml → check project.toml"
  exit 2
}
if [ "$stack" = docs ]; then
  echo "SKIP: no coverage for stack docs"
  exit 0
fi
tool=node_modules/.bin/c8
if [ ! -x "$tool" ]; then
  echo "c8 cannot-run: not installed → run scripts/setup"
  exit 2
fi
"$tool" node --test
rc=$?
case $rc in
  0) exit 0 ;;
  1)
    echo "coverage finding: c8 reported failures or low coverage → add tests"
    exit 1
    ;;
  *) exit 2 ;;
esac
