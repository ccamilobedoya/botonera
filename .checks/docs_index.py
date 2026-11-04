#!/usr/bin/env python3
"""Generated index of the documents (piece N18).

  docs_index.py [--check | --write] [--root docs] [--index docs/README.md]

Run from the project root. Lists every `*.md` under --root (recursively, sorted by path), except the
index itself, dotfiles and symbolic links (never followed), between the markers
`<!-- docs-index -->` and `<!-- /docs-index -->` of the index:

  - [<title>](<path>) — <description>
    - [<## heading>](<path>#<slug>)        only for documents over `[docs_index] section_kb` KB (8)

title: `title:` of the frontmatter, else the first `# ` line. description: `description:` of the
frontmatter, else the first line of text after the title, cut at 120 characters.
--write writes the block (text outside the markers is kept; no markers → at the end; no index → created).
--check (default) compares it. Exit 0 the index is current, 1 findings, 2 could not run.
"""

import argparse
import os
import re
import stat
import sys
import tomllib
import urllib.parse
from pathlib import Path

sys.dont_write_bytecode = True

OPEN, CLOSE = "<!-- docs-index -->", "<!-- /docs-index -->"
MAX_BYTES = 1024 * 1024
DESC_MAX = 120
DEFAULT_SECTION_KB = 8
HEADING = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
RULE = re.compile(r"^ {0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*$")
LIST_ITEM = re.compile(r"^ {0,3}(?:[-*+]|\d+[.)])(?:[ \t]|$)")
ROW = re.compile(r"^- \[(?:\\.|[^\]\\])*\]\(([^)]*)\)")
BLOCK_SCALAR = re.compile(r"^[>|][+-]?$")


class CannotRun(Exception):
    pass


def plain(text):
    """Markdown links become their text; whitespace is collapsed."""
    return " ".join(LINK.sub(r"\1", text).split())


def unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


def split_frontmatter(lines):
    """(flat key/value pairs, the lines after the frontmatter)."""
    if not lines or lines[0].rstrip() != "---":
        return {}, lines
    for i in range(1, len(lines)):
        if lines[i].rstrip() == "---":
            pairs = {}
            for line in lines[1:i]:
                if ":" in line and not line.startswith((" ", "\t", "#")):
                    key, _, value = line.partition(":")
                    if not BLOCK_SCALAR.match(value.strip()):
                        pairs[key.strip()] = unquote(value)
            return pairs, lines[i + 1:]
    return {}, lines


def scan_lines(lines):
    """[(index, kind, text)] with kind heading level (int) or 'text'/'skip'; fences and comments are 'skip'."""
    out = []
    fence = None
    comment = False
    for i, line in enumerate(lines):
        if comment:
            out.append((i, "skip", line))
            comment = "-->" not in line
            continue
        m = FENCE.match(line)
        if m:
            marker = m.group(1)
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence) and not line.strip(" `~"):
                fence = None
            out.append((i, "skip", line))
            continue
        if fence is not None:
            out.append((i, "skip", line))
            continue
        m = HEADING.match(line)
        if m:
            out.append((i, len(m.group(1)), m.group(2).strip()))
            continue
        stripped = line.strip()
        if stripped.startswith("<!--"):
            comment = "-->" not in stripped
            out.append((i, "skip", line))
        elif (not stripped or stripped.startswith((">", "|", "![", "<")) or line.startswith(("    ", "\t"))
              or LIST_ITEM.match(line) or RULE.match(line) or re.match(r"^ {0,3}\[[^\]]+\]:", line)):
            out.append((i, "skip", line))
        else:
            out.append((i, "text", stripped))
    return out


def slugify(text):
    text = plain(text).lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def shorten(text):
    if len(text) <= DESC_MAX:
        return text
    cut = text.rfind(" ", 0, DESC_MAX + 1)
    head = (text[:cut] if cut > 0 else text[:DESC_MAX]).rstrip()
    for token in ("`", "**"):
        while head.count(token) % 2:
            head = head[:head.rfind(token)].rstrip()
    return head + "…"


def escape_text(text):
    return text.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def encode_path(path):
    return path.replace("%", "%25").replace(" ", "%20").replace("(", "%28").replace(")", "%29")


def describe(path_rel, data, size, section_kb, index_dir):
    """The lines of the block for one document."""
    link = encode_path(os.path.relpath(path_rel, index_dir).replace(os.sep, "/"))
    name = escape_text(path_rel.rsplit("/", 1)[-1])
    if data is None:
        return [f"- [{name}]({link}) (not read: over 1 MiB)"]
    lines = data.decode("utf-8", errors="replace").splitlines()
    meta, body = split_frontmatter(lines)
    items = scan_lines(body)
    title = plain(meta.get("title", ""))
    start = 0
    if not title:
        for i, kind, text in items:
            if kind == 1:
                title, start = plain(text), i + 1
                break
    desc = plain(meta.get("description", ""))
    if not desc:
        for i, kind, text in items:
            if i >= start and kind == "text":
                desc = plain(text)
                break
    desc = shorten(desc) if desc else ""
    label = f"[{escape_text(title)}]({link})" if title else f"[{name}]({link}) (no title)"
    row = f"- {label}" + (f" — {desc}" if desc else "")
    rows = [row]
    if size > section_kb * 1024:
        seen = {}
        for _, kind, text in items:
            if not isinstance(kind, int):
                continue
            slug = slugify(text)
            n = seen.get(slug, 0)
            seen[slug] = n + 1
            if kind == 2:
                rows.append(f"  - [{escape_text(plain(text))}]({link}#{slug}{f'-{n}' if n else ''})")
    return rows


def section_kb_of(project):
    try:
        with open(project / "project.toml", "rb") as fh:
            value = tomllib.load(fh).get("docs_index", {}).get("section_kb", DEFAULT_SECTION_KB)
    except (OSError, tomllib.TOMLDecodeError):
        return DEFAULT_SECTION_KB
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        return DEFAULT_SECTION_KB
    return value


def inside(project_real, path):
    real = Path(os.path.realpath(path))
    return real == project_real or project_real in real.parents


def documents(root_dir, index_path, project):
    """Project-relative paths of the documents, sorted."""
    found = []
    for base, dirs, files in os.walk(root_dir, followlinks=False):
        dirs[:] = [d for d in dirs if not d.startswith(".") and not os.path.islink(os.path.join(base, d))]
        for name in files:
            full = os.path.join(base, name)
            if not name.endswith(".md") or name.startswith("."):
                continue
            try:
                if not stat.S_ISREG(os.lstat(full).st_mode):
                    continue
            except OSError:
                continue
            if os.path.normpath(full) == index_path:
                continue
            found.append(os.path.relpath(full, project).replace(os.sep, "/"))
    return sorted(found)


def build(project, docs, index_rel, section_kb):
    """[(path, [lines])] in order."""
    index_dir = os.path.dirname(index_rel) or "."
    out = []
    for rel in docs:
        full = project / rel
        try:
            size = full.stat().st_size
            data = None if size > MAX_BYTES else full.read_bytes()
        except OSError as exc:
            raise CannotRun(f"{rel} cannot be read ({exc.strerror}) → check the file") from None
        out.append((rel, describe(rel, data, size, section_kb, index_dir)))
    return out


def render_block(entries):
    lines = [OPEN, ""]
    for _, rows in entries:
        lines += rows
    if entries:
        lines.append("")
    lines.append(CLOSE)
    return "\n".join(lines)


def find_block(text):
    """(start, end) of the block: the markers count only as whole lines."""
    start = None
    offset = 0
    for line in text.splitlines(keepends=True):
        bare = line.rstrip()
        if start is None and bare == OPEN:
            start = offset
        elif start is not None and bare == CLOSE:
            return start, offset + len(bare)
        offset += len(line)
    return None


def read_index(index_full):
    """The text of the index, or None when it does not exist."""
    try:
        if not os.path.lexists(index_full):
            return None
        info = os.stat(index_full)
        if not stat.S_ISREG(info.st_mode):
            raise CannotRun(f"{index_full.name} is not a regular file → check the index")
        if info.st_size > MAX_BYTES:
            raise CannotRun(f"{index_full.name} is over 1 MiB → shorten the index")
        return index_full.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise CannotRun(f"{index_full.name} cannot be read ({getattr(exc, 'strerror', None) or 'not UTF-8'}) → "
                        "check the file") from None


def existing_groups(block, index_dir):
    """{project path: [lines]} of the rows of a block."""
    groups = {}
    current = None
    for line in block.splitlines()[1:-1]:
        m = ROW.match(line)
        if m:
            target = m.group(1).split("#", 1)[0]
            current = os.path.normpath(os.path.join(index_dir, urllib.parse.unquote(target))).replace(os.sep, "/")
            groups[current] = [line]
        elif line.startswith("  - ") and current is not None:
            groups[current].append(line)
    return groups


def write_index(index_full, entries):
    block = render_block(entries)
    text = read_index(index_full)
    if text is None:
        new = "# Documents\n\n" + block + "\n"
    else:
        span = find_block(text)
        if span:
            new = text[:span[0]] + block + text[span[1]:]
        else:
            if text and not text.endswith("\n"):
                text += "\n"
            new = text + ("\n" if text else "") + block + "\n"
    if text != new:
        index_full.parent.mkdir(parents=True, exist_ok=True)
        index_full.write_bytes(new.encode("utf-8"))


def check_index(index_full, index_rel, entries):
    text = read_index(index_full) or ""
    span = find_block(text)
    if not span:
        return [f"no docs-index block in {index_rel}"]
    block = text[span[0]:span[1]]
    have = existing_groups(block, os.path.dirname(index_rel) or ".")
    want = dict(entries)
    findings = [f"missing row {p}" for p in want if p not in have]
    findings += [f"orphan row {p}" for p in sorted(have) if p not in want]
    findings += [f"row differs {p}" for p in want if p in have and have[p] != want[p]]
    if not findings and block != render_block(entries):
        findings.append(f"block differs in {index_rel} → run --write")
    return findings


def run(args):
    project = Path.cwd()
    project_real = Path(os.path.realpath(project))
    root_dir = Path(os.path.normpath(project / args.root))
    index_full = Path(os.path.normpath(project / args.index))
    if not inside(project_real, root_dir) or not inside(project_real, index_full):
        raise CannotRun("--root and --index must be inside the project → pass paths relative to the project root")
    if not root_dir.is_dir():
        raise CannotRun(f"{args.root} is not a folder → pass --root with an existing folder")
    index_rel = os.path.relpath(index_full, project).replace(os.sep, "/")
    docs = documents(root_dir, str(index_full), project)
    entries = build(project, docs, index_rel, section_kb_of(project))
    if args.write:
        write_index(index_full, entries)
        return 0
    findings = check_index(index_full, index_rel, entries)
    if findings:
        print("\n".join(findings))
        return 1
    print(f"docs-index pass: {len(entries)} document{'' if len(entries) == 1 else 's'}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="docs_index.py", description="Generated index of the documents.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="compare the block with the documents (default)")
    mode.add_argument("--write", action="store_true", help="write the block")
    parser.add_argument("--root", default="docs", help="folder with the documents (default: docs)")
    parser.add_argument("--index", default="docs/README.md", help="the index file (default: docs/README.md)")
    args = parser.parse_args(argv)
    try:
        return run(args)
    except CannotRun as exc:
        print(f"docs-index cannot-run: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
