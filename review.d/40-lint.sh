#!/bin/sh
# Lint and format (biome check).

stack=$(python3 -c 'import tomllib;print(tomllib.load(open("project.toml","rb"))["stack"])') || {
  echo "lint cannot-run: cannot read the stack from project.toml → check project.toml"
  exit 2
}
if [ "$stack" = docs ]; then
  echo "SKIP: no lint for stack docs"
  exit 0
fi
tool=node_modules/.bin/biome
if [ ! -x "$tool" ]; then
  echo "biome cannot-run: not installed → run scripts/setup"
  exit 2
fi
"$tool" check .
rc=$?
case $rc in
  0) exit 0 ;;
  1)
    echo "lint finding: biome reported problems → fix them"
    exit 1
    ;;
  *) exit 2 ;;
esac
