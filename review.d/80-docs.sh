#!/bin/sh
# Markdown: links (lychee, offline) and style (markdownlint-cli2).

stack=$(python3 -c 'import tomllib;print(tomllib.load(open("project.toml","rb"))["stack"])') || {
  echo "docs cannot-run: cannot read the stack from project.toml → check project.toml"
  exit 2
}
list=$(git -c core.quotepath=off ls-files --cached --others --exclude-standard -- '*.md') || {
  echo "docs cannot-run: not inside a git repository → run git init"
  exit 2
}
set --
while IFS= read -r file; do
  [ -f "$file" ] && set -- "$@" "$file"
done <<LIST
$list
LIST
if [ "$#" -eq 0 ]; then
  echo "SKIP: no markdown files"
  exit 0
fi

found=0
cannot=0

lychee=.checks/bin/lychee
[ -x "$lychee" ] || lychee=$(command -v lychee 2>/dev/null) || lychee=""
if [ -z "$lychee" ]; then
  echo "lychee could not run: run scripts/setup"
  cannot=1
else
  "$lychee" --offline --no-progress "$@"
  rc=$?
  case $rc in
    0) ;;
    2)
      echo "docs finding: broken links → fix the links"
      found=1
      ;;
    *)
      echo "lychee could not run: exit code $rc → run lychee --offline by hand"
      cannot=1
      ;;
  esac
fi

lint=node_modules/.bin/markdownlint-cli2
if [ -x "$lint" ]; then
  "$lint" "$@"
  rc=$?
  case $rc in
    0) ;;
    1)
      echo "docs finding: markdownlint reported problems → fix them"
      found=1
      ;;
    *)
      echo "markdownlint cannot-run: exit code $rc → run markdownlint-cli2 by hand"
      cannot=1
      ;;
  esac
elif [ "$stack" = docs ]; then
  echo "WARN: markdownlint not run (needs Node)"
else
  echo "markdownlint cannot-run: not installed → run scripts/setup"
  cannot=1
fi

[ "$found" -eq 0 ] || exit 1
[ "$cannot" -eq 0 ] || exit 2
exit 0
