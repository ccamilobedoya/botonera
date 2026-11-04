#!/bin/sh
# Shell scripts: shellcheck at warning level.
# Shell scripts are tracked or untracked (not ignored) files ending in .sh, or whose
# first line is a sh or bash shebang.

list=$(git -c core.quotepath=off ls-files --cached --others --exclude-standard) || {
  echo "shellcheck cannot-run: not inside a git repository → run git init"
  exit 2
}

shebang='^#![[:space:]]*(/usr/bin/env[[:space:]]+(-S[[:space:]]+)?)?([^[:space:]]*/)?(ba|da)?sh([[:space:]]|$)'
set --
while IFS= read -r file; do
  [ -f "$file" ] || continue
  case $file in
    *.sh) set -- "$@" "$file" ;;
    *)
      first=$(head -n 1 "$file" 2>/dev/null | tr -d '\000')
      if printf '%s\n' "$first" | grep -Eq "$shebang"; then
        set -- "$@" "$file"
      fi
      ;;
  esac
done <<LIST
$list
LIST

if [ "$#" -eq 0 ]; then
  echo "SKIP: no shell scripts"
  exit 0
fi

tool=.checks/bin/shellcheck
[ -x "$tool" ] || tool=$(command -v shellcheck 2>/dev/null) || tool=""
if [ -z "$tool" ]; then
  echo "shellcheck could not run: run scripts/setup"
  exit 2
fi
"$tool" -S warning "$@"
rc=$?
case $rc in
  0) exit 0 ;;
  1)
    echo "shellcheck finding: warnings in shell scripts → fix them"
    exit 1
    ;;
  *) exit 2 ;;
esac
