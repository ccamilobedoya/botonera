#!/usr/bin/env python3
"""Never-commit list: file names that must stay local.

Exit codes: 0 pass, 1 finding, 2 cannot run.

  never_commit.py --staged                     staged files
  never_commit.py --tree                       tracked and untracked, not ignored
  never_commit.py --commits REV_LIST_ARGS...   files added or changed by the listed commits
  never_commit.py --paths PATH...              the given paths
  never_commit.py --self-test [--cases FILE]   run the case set against the list

The list is `never-commit.txt` next to this script (gitignore-like subset,
case-insensitive, `!` exceptions, last match wins).
"""

import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

SELF_PATH = Path(os.path.abspath(__file__))
LIST_PATH = SELF_PATH.parent / "never-commit.txt"


class CannotRun(Exception):
    pass


def translate(pattern):
    """Regex source for one glob: `*` and `?` stay inside a segment, `**/` spans directories."""
    out = []
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("/**", i) and i + 3 == len(pattern):
            out.append("/.*")
            i += 3
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return "".join(out)


def parse_rules(lines):
    rules = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        negate = line.startswith("!")
        pattern = (line[1:] if negate else line).strip().lower()
        if not pattern:
            continue
        if "/" in pattern:
            regex = re.compile(translate(pattern.lstrip("/")) + r"\Z")
            basename = False
        else:
            regex = re.compile(translate(pattern) + r"\Z")
            basename = True
        rules.append((negate, regex, basename))
    return rules


def is_listed(rules, path):
    """True when the last matching rule is not an exception."""
    path = path.replace("\\", "/").lower().lstrip("/")
    name = path.rsplit("/", 1)[-1]
    listed = False
    for negate, regex, basename in rules:
        if regex.match(name if basename else path):
            listed = not negate
    return listed


def load_rules(path=LIST_PATH):
    try:
        return parse_rules(Path(path).read_text(encoding="utf-8", errors="replace").splitlines())
    except OSError as err:
        raise CannotRun(f"list not found ({path}) → restore .checks/never-commit.txt") from err


def git(root, *args, check=True, hint="run it from inside the project repository"):
    cmd = ["git", "-c", "core.quotepath=off", *args]
    try:
        proc = subprocess.run(cmd, cwd=root, capture_output=True)
    except OSError as err:
        raise CannotRun(f"git could not run ({err.strerror}) → install git") from err
    if check and proc.returncode != 0:
        raise CannotRun(f"git {args[0]} failed → {hint}")
    return proc


def names_z(raw):
    return [n.decode("utf-8", "surrogateescape") for n in raw.split(b"\0") if n]


def toplevel():
    try:
        proc = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True)
    except OSError:
        return None
    return os.fsdecode(proc.stdout.strip()) if proc.returncode == 0 else None


def report(hits, checked):
    for label in hits:
        print(f"never-commit finding: {label}")
    if hits:
        print(f"never-commit finding: {len(hits)} files → unstage them; they stay local (never git add -f)")
        return 1
    print(f"never-commit pass: {checked} files checked")
    return 0


def run_self_test(cases_path):
    try:
        with open(cases_path, "rb") as fh:
            spec = tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError) as err:
        raise CannotRun(f"cannot read the case set ({cases_path}: {type(err).__name__}) → restore it") from err
    rules = load_rules()
    cases = spec.get("case", [])
    bad = 0
    for case in cases:
        got = "finding" if is_listed(rules, case["path"]) else "clean"
        if got != case["expect"]:
            bad += 1
            print(f"never-commit self-test finding: {case['path']}: expected {case['expect']}, got {got}")
    if bad:
        return 1
    print(f"never-commit self-test pass: {len(cases)} cases")
    return 0


def usage():
    print("usage: never_commit.py --staged | --tree | --commits <rev-list args> | --paths P... | --self-test [--cases F]", file=sys.stderr)
    return 2


def main(argv):
    if not argv:
        return usage()
    mode, rest = argv[0], argv[1:]
    if mode == "--self-test":
        cases = SELF_PATH.parent / "never-commit-cases.toml"
        if rest[:1] == ["--cases"] and len(rest) == 2:
            cases = Path(rest[1])
        elif rest:
            return usage()
        return run_self_test(cases)
    if mode not in ("--staged", "--tree", "--commits", "--paths"):
        return usage()
    if mode in ("--staged", "--tree") and rest:
        return usage()
    if mode == "--paths" and not rest:
        return usage()
    rules = load_rules()
    if mode == "--paths":
        root = toplevel() or os.getcwd()
        names = [os.path.relpath(os.path.abspath(p), root) for p in rest]
        return report([n for n in names if is_listed(rules, n)], len(names))
    root = toplevel()
    if root is None:
        raise CannotRun("not inside a git repository → run it from the project")
    if mode == "--staged":
        names = names_z(git(root, "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR").stdout)
        return report([n for n in names if is_listed(rules, n)], len(names))
    if mode == "--tree":
        out = git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard").stdout
        names = [n for n in sorted(set(names_z(out))) if os.path.lexists(os.path.join(root, n))]
        return report([n for n in names if is_listed(rules, n)], len(names))
    if not rest:
        raise CannotRun("--commits needs revision arguments → pass what git rev-list accepts")
    commits = git(root, "rev-list", *rest, hint="check the revision range").stdout.decode().split()
    hits, checked = [], 0
    for commit in commits:
        tree = git(root, "diff-tree", "-r", "--root", "--no-commit-id", "--name-only", "-z", "--diff-filter=ACMR", commit)
        for name in names_z(tree.stdout):
            checked += 1
            if is_listed(rules, name):
                hits.append(f"{name} (commit {commit[:7]})")
    return report(hits, checked)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.exit(main(sys.argv[1:]))
    except CannotRun as err:
        print(f"never-commit cannot-run: {err}")
        sys.exit(2)
    except Exception as err:  # never let a crash read as a pass or a finding
        print(f"never-commit cannot-run: internal error ({type(err).__name__}) → report it")
        sys.exit(2)
