#!/usr/bin/env python3
"""Parity of the bilingual documents (piece I01).

  doc_parity.py

Run from the project root. With `docs_language = "en+es"` in project.toml, every `X.es.md` must have
its `X.md` and the same heading structure: the sequence of ATX heading levels outside fenced code
blocks (headings are translated, so the text is not compared). `X.md` without `X.es.md` is fine.
Exit 0 all pairs match (or single-language documents), 1 findings, 2 could not run.
"""

import difflib
import re
import subprocess
import sys
import tomllib
from pathlib import Path

sys.dont_write_bytecode = True

HEADING = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


class CannotRun(Exception):
    pass


def find_root():
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        return Path(out.stdout.strip())
    except (OSError, subprocess.CalledProcessError):
        return Path.cwd()


def listed_files(root):
    try:
        out = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                             cwd=root, capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        raise CannotRun("git ls-files failed → run it inside the project repository") from None
    return sorted(f for f in out.stdout.split("\0") if f)


def headings(text):
    """[(level, text)] of the ATX headings outside fenced code blocks."""
    found = []
    fence = None
    for line in text.splitlines():
        m = FENCE.match(line)
        if m:
            marker = m.group(1)
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence) and not line.strip(" `~"):
                fence = None
            continue
        if fence is not None:
            continue
        m = HEADING.match(line)
        if m:
            found.append((len(m.group(1)), m.group(2).strip()))
    return found


def read(root, rel):
    try:
        return (root / rel).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise CannotRun(f"{rel} cannot be read ({getattr(exc, 'strerror', None) or 'not UTF-8'}) → check the file") from None


def run_around(items, index):
    """Consecutive headings of the same level that contain items[index]."""
    level = items[index][0]
    lo = hi = index
    while lo > 0 and items[lo - 1][0] == level:
        lo -= 1
    while hi + 1 < len(items) and items[hi + 1][0] == level:
        hi += 1
    return items[lo:hi + 1]


def quoted(items):
    return ", ".join(f"«{text}»" for _, text in items)


def compare(en_name, es_name, en, es):
    """The first difference between the two heading structures, as a finding line, or None."""
    a = [level for level, _ in en]
    b = [level for level, _ in es]
    if a == b:
        return None
    prefix = f"parity finding: {en_name} / {es_name}:"
    for tag, i1, _i2, j1, _j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        if tag == "delete":
            return _unmatched(prefix, en, i1, en_name, es_name)
        if tag == "insert":
            return _unmatched(prefix, es, j1, es_name, en_name)
        level, text = en[i1]
        other_level, other_text = es[j1]
        return (f"{prefix} «{text}» ({'#' * level}) is «{other_text}» ({'#' * other_level}) in {es_name} "
                f"→ use the same heading level in both documents")
    return None


def _unmatched(prefix, items, index, owner, other):
    run = run_around(items, index)
    level = "#" * items[index][0]
    if len(run) == 1:
        subject = f"«{items[index][1]}» ({level}) has"
    else:
        # The levels alone cannot tell which of equal-level neighbours is the odd one out.
        subject = f"one of {quoted(run)} ({level}) has"
    return f"{prefix} {subject} no counterpart in {other} → add the translated heading to {other} or remove it from {owner}"


def main():
    root = find_root()
    try:
        with open(root / "project.toml", "rb") as fh:
            config = tomllib.load(fh)
    except OSError as exc:
        raise CannotRun(f"project.toml cannot be read ({exc.strerror}) → check project.toml") from None
    except tomllib.TOMLDecodeError as exc:
        raise CannotRun(f"project.toml is not valid TOML ({exc}) → fix project.toml") from None
    if config.get("docs_language") != "en+es":
        print("SKIP: single-language documents")
        return 0
    files = [f for f in listed_files(root) if (root / f).is_file()]
    present = set(files)
    findings = []
    pairs = 0
    for es_name in files:
        if not es_name.endswith(".es.md"):
            continue
        en_name = es_name[: -len(".es.md")] + ".md"
        if en_name not in present:
            findings.append(f"parity finding: {es_name} has no {en_name} → create {en_name} or remove {es_name}")
            continue
        pairs += 1
        line = compare(en_name, es_name, headings(read(root, en_name)), headings(read(root, es_name)))
        if line:
            findings.append(line)
    if findings:
        print("\n".join(findings))
        return 1
    print(f"parity: {pairs} document {'pair' if pairs == 1 else 'pairs'} with the same structure")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except CannotRun as exc:
        print(f"parity cannot-run: {exc}")
        sys.exit(2)
