#!/usr/bin/env python3
"""Privacy scan: private terms, personal data and secret shapes.

Second line behind gitleaks. Exit codes: 0 pass, 1 finding, 2 cannot run.

  privacy.py --staged                     staged files (content from the index)
  privacy.py --tree                       tracked and untracked, not ignored
  privacy.py --message-file FILE          a commit message (lines with # skipped)
  privacy.py --commits REV_LIST_ARGS...   message and files of every listed commit
  privacy.py --paths PATH...              the given files
  privacy.py --self-test [--cases FILE]   run the case set against the rules

The private-terms list lives outside the repository: env
CHECKS_PRIVATE_TERMS_FILE, else `git config checks.privateTermsFile`. One term
per line; `#` comments and blank lines are ignored. The matched text is never
printed.
"""

import base64
import bisect
import os
import re
import subprocess
import sys
import tomllib
import unicodedata
from pathlib import Path

MAX_BYTES = 10 * 1024 * 1024
BINARY_PROBE = 8192
EXCLUDED = {".checks/privacy-cases.toml"}
STRIP_MARKUP = str.maketrans("", "", "*_`~")

# Literals are built from pieces so that this file never matches its own rules.
_HOME = "/ho" + "me/"
_USERS = "/Us" + "ers/"

PATTERNS = {
    "note-link": re.compile("#" + "root/" + r"[A-Za-z0-9]{6,}"),
    "home-path": re.compile(
        "|".join(
            [
                _HOME + r"[A-Za-z0-9_.-]+",
                "/ho" + "me%2[Ff]",
                _USERS + r"[A-Za-z0-9_.-]+",
                "~" + r"\\[A-Za-z]",
                r"[A-Za-z]:" + r"\\Us" + r"ers\\",
            ]
        )
    ),
    "private-ip": re.compile(
        r"(?<![\w.])(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        r"|192\.168\.\d{1,3}\.\d{1,3}"
        r"|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})(?!\w)"
    ),
    "tailnet": re.compile(r"\b[\w-]+\.ts\.net\b"),
    "github-token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36}\b|\bgithub_pat_[A-Za-z0-9_]{22,}"),
    "aws-key": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "slack-token": re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}"),
    "jwt": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+"),
    "private-key": re.compile("-----BEGIN [A-Z ]*PRI" + "VATE KEY-----"),
    "anthropic-key": re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}"),
}

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,})\b")
EMAIL_OBFUSCATED = re.compile(r"\b[\w.+-]+\s*[\[(]at[\])]\s*[\w-]+(?:\.[\w-]+)+", re.I)
SAFE_DOMAIN = re.compile(
    r"(^|\.)example\.(com|org|net)$|\.(example|invalid|test|localhost)$|^users\.noreply\.github\.com$"
)

SELF_PATH = Path(os.path.abspath(__file__))


class CannotRun(Exception):
    pass


# --- scanning ---------------------------------------------------------------


def fold(text):
    """NFKD, no combining marks, casefolded: `José` and `jose` compare equal."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def load_terms(lines):
    terms = []
    for raw in lines:
        line = raw.strip()
        if line and not line.startswith("#"):
            folded = fold(line)
            if folded:
                terms.append(folded)
    return terms


def decode(data):
    if b"\0" in data[:BINARY_PROBE]:
        return data.decode("latin-1")
    return data.decode("utf-8", errors="replace")


def scan(path, data, terms):
    """Return a sorted list of (line, rule) for one file name and its content."""
    found = set()
    if any(t in fold(path) or t in fold(path).translate(STRIP_MARKUP) for t in terms):
        found.add((0, "file-name-term"))
    text = decode(data)
    if terms:
        folded = fold(text)
        if any(t in folded or t in folded.translate(STRIP_MARKUP) for t in terms):
            for number, line in enumerate(folded.split("\n"), 1):
                stripped = line.translate(STRIP_MARKUP)
                if any(t in line or t in stripped for t in terms):
                    found.add((number, "term"))
    newlines = [i for i, c in enumerate(text) if c == "\n"]

    def line_of(offset):
        return bisect.bisect_left(newlines, offset) + 1

    for rule, regex in PATTERNS.items():
        for m in regex.finditer(text):
            found.add((line_of(m.start()), rule))
    for m in EMAIL.finditer(text):
        if not SAFE_DOMAIN.search(m.group(1).lower()):
            found.add((line_of(m.start()), "email"))
    for m in EMAIL_OBFUSCATED.finditer(text):
        found.add((line_of(m.start()), "email"))
    return sorted(found)


# --- git and files ----------------------------------------------------------


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


def git_blob(root, spec):
    """Content of a blob (`:path` or `<commit>:path`), or None when unreadable."""
    try:
        proc = subprocess.Popen(
            ["git", "-c", "core.quotepath=off", "cat-file", "blob", spec],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        return None
    data = proc.stdout.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        proc.kill()
    proc.stdout.close()
    proc.wait()
    if len(data) > MAX_BYTES or proc.returncode != 0:
        return None
    return data


def is_gitlink(root, spec):
    proc = git(root, "cat-file", "-t", spec, check=False)
    return proc.stdout.strip() == b"commit"


def read_file(path):
    try:
        if os.path.getsize(path) > MAX_BYTES:
            return None
        with open(path, "rb") as fh:
            return fh.read(MAX_BYTES + 1)
    except OSError:
        return None


# --- private-terms list -----------------------------------------------------


def config_get(root, *args):
    if root is None:
        return ""
    proc = git(root, "config", *args, check=False)
    return proc.stdout.decode("utf-8", "replace").strip() if proc.returncode == 0 else ""


def private_terms(root):
    """Return (terms, skip_line). Raise CannotRun when the list is required and missing."""
    configured = os.environ.get("CHECKS_PRIVATE_TERMS_FILE") or config_get(root, "--get", "checks.privateTermsFile")
    required = (
        config_get(root, "--bool", "checks.requirePrivateTerms") == "true"
        or os.environ.get("CHECKS_REQUIRE_PRIVATE_TERMS") == "1"
    )
    lines = None
    if configured:
        try:
            lines = Path(os.path.expanduser(configured)).read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            lines = None
    if lines is not None:
        return load_terms(lines), None
    if required:
        shown = configured or "not configured"
        raise CannotRun(f"private-terms list not found ({shown}) → run scripts/setup")
    if os.environ.get("CI"):
        return [], "SKIP: CI runs without the private-terms list: private terms are not covered"
    return [], "SKIP: private terms not checked (no list) → set checks.privateTermsFile"


# --- reporting --------------------------------------------------------------


# The email rule is for data (file contents). A commit message may carry an address, like the
# author field and the Co-Authored-By trailers; every other rule still applies to it.
MESSAGE_ALLOWED = {"email"}

_CASE_SET = []


def is_case_set(data):
    """The case set next to this script holds seeds by design: an exact copy of it is not scanned."""
    if not _CASE_SET:
        try:
            _CASE_SET.append((SELF_PATH.parent / "privacy-cases.toml").read_bytes())
        except OSError:
            _CASE_SET.append(None)
    return data is not None and _CASE_SET[0] is not None and data == _CASE_SET[0]


class Report:
    def __init__(self, terms):
        self.terms = terms
        self.checked = 0
        self.findings = 0

    def add(self, label, path, data, skip_comments=False, message=False):
        if is_case_set(data):
            return
        self.checked += 1
        if data is None:
            self.finding(label, 0, "unreadable")
            return
        if skip_comments:
            lines = data.split(b"\n")
            data = b"\n".join(b"" if ln.startswith(b"#") else ln for ln in lines)
        for number, rule in scan(path, data, self.terms):
            if message and rule in MESSAGE_ALLOWED:
                continue
            self.finding(label, number, rule)

    def finding(self, label, number, rule):
        self.findings += 1
        print(f"privacy finding: {label}:{number}: {rule}")

    def finish(self):
        if self.findings:
            print(f"privacy finding: {self.findings} findings → rewrite the text; never loosen the patterns")
            return 1
        print(f"privacy pass: {self.checked} files checked")
        return 0


def relative(root, path):
    try:
        return os.path.relpath(os.path.abspath(path), root).replace(os.sep, "/")
    except ValueError:
        return path


# --- modes ------------------------------------------------------------------


def run_staged(root, report):
    out = git(root, "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR").stdout
    for name in names_z(out):
        if name in EXCLUDED:
            continue
        data = git_blob(root, ":" + name)
        if data is None and is_gitlink(root, ":" + name):
            continue
        report.add(name, name, data)


def run_tree(root, report):
    out = git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard").stdout
    for name in sorted(set(names_z(out))):
        if name in EXCLUDED:
            continue
        full = os.path.join(root, name)
        if not os.path.exists(full) or os.path.isdir(full):
            continue
        report.add(name, name, read_file(full))


def run_message(path, report):
    data = read_file(path)
    if data is None:
        raise CannotRun(f"cannot read the commit message file ({path}) → check the path")
    report.add("commit message", "", data, skip_comments=True, message=True)


def run_commits(root, rev_args, report):
    if not rev_args:
        raise CannotRun("--commits needs revision arguments → pass what git rev-list accepts")
    commits = git(root, "rev-list", *rev_args, hint="check the revision range").stdout.decode().split()
    for commit in commits:
        short = commit[:7]
        message = git(root, "log", "-1", "--format=%B", commit).stdout
        report.add(f"commit {short}: message", "", message, message=True)
        tree = git(root, "diff-tree", "-r", "--root", "--no-commit-id", "--name-only", "-z", "--diff-filter=ACMR", commit)
        for name in names_z(tree.stdout):
            if name in EXCLUDED:
                continue
            spec = f"{commit}:{name}"
            data = git_blob(root, spec)
            if data is None and is_gitlink(root, spec):
                continue
            report.add(f"commit {short}: {name}", name, data)


def run_paths(root, paths, report):
    for path in paths:
        rel = relative(root or os.getcwd(), path)
        if rel in EXCLUDED:
            continue
        report.add(path, rel, read_file(path))


def case_content(case, parts):
    if "content_b64" in case:
        return base64.b64decode(case["content_b64"])
    text = case.get("content", "")
    for key, pieces in parts.items():
        text = text.replace("{" + key + "}", "".join(pieces))
    return text.encode("utf-8")


def run_self_test(cases_path):
    try:
        with open(cases_path, "rb") as fh:
            spec = tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError) as err:
        raise CannotRun(f"cannot read the case set ({cases_path}: {type(err).__name__}) → restore it") from err
    terms = load_terms(spec.get("terms", []))
    parts = spec.get("parts", {})
    cases = spec.get("case", [])
    bad = 0
    for number, case in enumerate(cases, 1):
        expected = set() if case.get("expect") == "clean" else {case.get("expect")}
        got = {rule for _, rule in scan(case.get("path", ""), case_content(case, parts), terms)}
        if got != expected:
            bad += 1
            ident = case.get("id", f"#{number}")
            want = case.get("expect")
            print(f"privacy self-test finding: {ident}: expected {want}, got {', '.join(sorted(got)) or 'clean'}")
    if bad:
        return 1
    print(f"privacy self-test pass: {len(cases)} cases")
    return 0


# --- entry point ------------------------------------------------------------


def toplevel():
    try:
        proc = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True)
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    return os.fsdecode(proc.stdout.strip())


def usage():
    print("usage: privacy.py --staged | --tree | --message-file F | --commits <rev-list args> | --paths P... | --self-test [--cases F]", file=sys.stderr)
    return 2


def main(argv):
    if not argv:
        return usage()
    mode, rest = argv[0], argv[1:]
    if mode == "--self-test":
        cases = SELF_PATH.parent / "privacy-cases.toml"
        if rest[:1] == ["--cases"] and len(rest) == 2:
            cases = Path(rest[1])
        elif rest:
            return usage()
        return run_self_test(cases)
    if mode not in ("--staged", "--tree", "--message-file", "--commits", "--paths"):
        return usage()
    if mode == "--message-file" and len(rest) != 1:
        return usage()
    if mode in ("--staged", "--tree") and rest:
        return usage()
    if mode == "--paths" and not rest:
        return usage()
    root = toplevel()
    if root is None and mode not in ("--paths", "--message-file"):
        raise CannotRun("not inside a git repository → run it from the project")
    terms, skip = private_terms(root)
    if skip:
        print(skip)
    report = Report(terms)
    if mode == "--staged":
        run_staged(root, report)
    elif mode == "--tree":
        run_tree(root, report)
    elif mode == "--message-file":
        run_message(rest[0], report)
    elif mode == "--commits":
        run_commits(root, rest, report)
    else:
        run_paths(root, rest, report)
    return report.finish()


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.exit(main(sys.argv[1:]))
    except CannotRun as err:
        print(f"privacy cannot-run: {err}")
        sys.exit(2)
    except Exception as err:  # never let a crash read as a pass or a finding
        print(f"privacy cannot-run: internal error ({type(err).__name__}) → report it")
        sys.exit(2)
