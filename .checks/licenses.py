#!/usr/bin/env python3
"""Dependency licence review (piece O02). Offline: it only reads files and runs nothing.

  licenses.py

Run from the project root. Reads project.toml (`stack`, `allowed_licenses`), package-lock.json
(production entries only; `node_modules/<path>/package.json` fills in a missing licence) and
license-exceptions.toml. Prints one line per package that is not allowed.
Exit 0 all allowed (or nothing to check), 1 findings, 2 could not run.
"""

import json
import re
import sys
import tomllib
from pathlib import Path

sys.dont_write_bytecode = True

UNKNOWN = "unknown license"
HINT = ("add it to allowed_licenses, replace the dependency, or add an exception with reason "
        "and approved_by in license-exceptions.toml")
TOKEN = re.compile(r"\(|\)|[^\s()]+")


MAX_MANIFEST = 1024 * 1024


class CannotRun(Exception):
    pass


def find_root():
    """Nearest directory upwards from the current one that holds project.toml (else the current one)."""
    here = Path.cwd()
    for folder in (here, *here.parents):
        if (folder / "project.toml").is_file():
            return folder
    return here


def load_toml(path, what):
    try:
        with open(path, "rb") as fh:
            return tomllib.load(fh)
    except OSError as exc:
        raise CannotRun(f"{what} cannot be read ({exc.strerror}) → check {path.name}") from None
    except tomllib.TOMLDecodeError as exc:
        raise CannotRun(f"{what} is not valid TOML ({exc}) → fix {path.name}") from None


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CannotRun(f"{path.name} cannot be read ({exc.strerror}) → check the file") from None
    except ValueError as exc:
        raise CannotRun(f"{path.name} is not valid JSON ({exc}) → regenerate it with scripts/setup") from None


def parse_expression(text, allowed):
    """True when the SPDX expression is satisfied: AND binds tighter than OR; anything odd is not allowed."""
    tokens = TOKEN.findall(text)
    pos = 0

    def peek():
        return tokens[pos] if pos < len(tokens) else None

    def term():
        nonlocal pos
        if peek() == "(":
            pos += 1
            value = either()
            if peek() != ")":
                raise ValueError("unbalanced")
            pos += 1
            return value
        words = []
        while peek() is not None and peek() not in ("(", ")", "AND", "OR"):
            words.append(tokens[pos])
            pos += 1
        if not words:
            raise ValueError("empty")
        return " ".join(words) in allowed

    def both():
        nonlocal pos
        value = term()
        while peek() == "AND":
            pos += 1
            right = term()
            value = value and right
        return value

    def either():
        nonlocal pos
        value = both()
        while peek() == "OR":
            pos += 1
            right = both()
            value = value or right
        return value

    try:
        result = either()
        return result and pos == len(tokens)
    except ValueError:
        return False


def manifest_license(manifest):
    """License string of a package.json: `license`, legacy `license: {type}` or `licenses: [{type}]`."""
    value = manifest.get("license")
    if isinstance(value, dict):
        value = value.get("type")
    if isinstance(value, str) and value.strip():
        return value.strip()
    legacy = manifest.get("licenses")
    if isinstance(legacy, list):
        types = [item.get("type") if isinstance(item, dict) else item for item in legacy]
        types = [t for t in types if isinstance(t, str) and t.strip()]
        if types:
            return " OR ".join(t.strip() for t in types)
    return None


def entry_license(root, key, entry):
    value = entry.get("license")
    if isinstance(value, dict):
        value = value.get("type")
    if isinstance(value, str) and value.strip():
        return value.strip()
    if key.startswith("node_modules/") and ".." not in key.split("/"):
        manifest_path = root / key / "package.json"
        try:
            # Confined to the project and capped: the lockfile and node_modules are external input.
            manifest_path.resolve(strict=True).relative_to(root.resolve())
            if manifest_path.stat().st_size > MAX_MANIFEST:
                return None
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if isinstance(manifest, dict):
            return manifest_license(manifest)
    return None


def load_exceptions(path):
    if not path.exists():
        return []
    data = load_toml(path, "license-exceptions.toml")
    items = data.get("exception", [])
    if not isinstance(items, list) or not all(isinstance(i, dict) for i in items):
        raise CannotRun("license-exceptions.toml: `exception` must be an array of tables → use [[exception]]")
    return items


def exception_for(exceptions, name, version):
    """(accepted, ignored_reason): an exception counts only with a reason and an approver."""
    ignored = None
    for item in exceptions:
        if item.get("package") != name or item.get("version") not in (version, "*"):
            continue
        reason = str(item.get("reason", "")).strip()
        approver = str(item.get("approved_by", "")).strip()
        if reason and approver:
            return True, None
        ignored = "no reason" if not reason else "no approved_by"
    return False, ignored


def package_name(key):
    return key.rsplit("node_modules/", 1)[-1]


def main():
    root = find_root()
    config = load_toml(root / "project.toml", "project.toml")
    stack = config.get("stack")
    if stack == "docs":
        print("SKIP: no dependencies for stack docs")
        return 0
    allowed = config.get("allowed_licenses")
    if not isinstance(stack, str) or not isinstance(allowed, list) or not all(isinstance(a, str) for a in allowed):
        raise CannotRun("project.toml needs `stack` and `allowed_licenses` (a list of strings) → fix project.toml")
    exceptions = load_exceptions(root / "license-exceptions.toml")
    lock_path = root / "package-lock.json"
    if not lock_path.exists():
        manifest = load_json(root / "package.json") if (root / "package.json").exists() else {}
        if isinstance(manifest, dict) and manifest.get("dependencies"):
            raise CannotRun("no package-lock.json → run scripts/setup")
        print("licenses: 0 production dependencies, all allowed")
        return 0
    lock = load_json(lock_path)
    packages = lock.get("packages") if isinstance(lock, dict) else None
    if not isinstance(packages, dict):
        raise CannotRun("package-lock.json has no `packages` map (lockfile v1?) → regenerate it with npm 7 or later")
    allowed_set = set(allowed)
    count = 0
    findings = []
    for key, entry in packages.items():
        if key == "" or not isinstance(entry, dict) or entry.get("link"):
            continue
        if entry.get("dev") is True or entry.get("devOptional") is True:
            continue
        count += 1
        name = package_name(key)
        version = str(entry.get("version", "?"))
        license_text = entry_license(root, key, entry)
        if license_text is not None and parse_expression(license_text, allowed_set):
            continue
        accepted, ignored = exception_for(exceptions, name, version)
        if accepted:
            continue
        note = f" (exception ignored: {ignored})" if ignored else ""
        findings.append(f"licenses finding: {name} {version} {license_text or UNKNOWN} not allowed → {HINT}{note}")
    if findings:
        print("\n".join(findings))
        return 1
    print(f"licenses: {count} production dependencies, all allowed")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except CannotRun as exc:
        print(f"licenses cannot-run: {exc}")
        sys.exit(2)
