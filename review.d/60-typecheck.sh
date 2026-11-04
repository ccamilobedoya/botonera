#!/bin/sh
# Type check (tsc --noEmit), node-ts only.

stack=$(python3 -c 'import tomllib;print(tomllib.load(open("project.toml","rb"))["stack"])') || {
  echo "typecheck cannot-run: cannot read the stack from project.toml → check project.toml"
  exit 2
}
if [ "$stack" != node-ts ]; then
  echo "SKIP: no type check for stack $stack"
  exit 0
fi
tool=node_modules/.bin/tsc
if [ ! -x "$tool" ]; then
  echo "tsc cannot-run: not installed → run scripts/setup"
  exit 2
fi
"$tool" --noEmit
rc=$?
case $rc in
  0) exit 0 ;;
  1 | 2)
    echo "typecheck finding: tsc reported type errors → fix them"
    exit 1
    ;;
  *) exit 2 ;;
esac
