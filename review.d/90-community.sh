#!/bin/sh
# Community files of a public project: CONTRIBUTING, SECURITY, templates and CODEOWNERS.

if ! command -v python3 >/dev/null 2>&1; then
  echo "community cannot-run: python3 not found → install Python 3.11+"
  exit 2
fi
visibility=$(python3 -c 'import tomllib;print(tomllib.load(open("project.toml","rb"))["visibility"])') || {
  echo "community cannot-run: cannot read the visibility from project.toml → check project.toml"
  exit 2
}
if [ "$visibility" != public ]; then
  echo "SKIP: community files are for public projects"
  exit 0
fi

missing=0
for f in CONTRIBUTING.md SECURITY.md .github/pull_request_template.md .github/ISSUE_TEMPLATE/bug.md .github/CODEOWNERS; do
  if [ ! -f "$f" ]; then
    echo "community finding: $f is missing → add it"
    missing=1
  fi
done
[ "$missing" -eq 0 ] || exit 1

if ! grep -q '^[[:space:]]*[^[:space:]#]' .github/CODEOWNERS; then
  echo "WARN: CODEOWNERS has no owner → set one"
fi
echo "community pass: files present"
exit 0
