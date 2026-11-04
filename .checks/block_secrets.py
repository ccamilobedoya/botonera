#!/usr/bin/env python3
"""Claude Code PreToolUse hook for Bash: stop commands that touch secrets or skip the hooks.

Reads the hook JSON on stdin. Denies by printing a permissionDecision JSON;
allows by printing nothing. It always exits 0: a bug here must never block the
session, so its own errors go to stderr.

Denied: tokens that name a .env file, local.env, ~/.config (also by glob), *.pem,
*.key, id_rsa*, id_ed25519*; `git commit --no-verify|-n`; `git push --force|-f|--no-verify`.
Only the first line that holds `<<` is read: heredoc bodies are text, not commands.
"""

import fnmatch
import json
import re
import shlex
import sys

SEPARATORS = {";", "&&", "||", "|", "&", "(", ")", ";;", "|&"}
WRAPPERS = {"sudo", "env", "command", "time", "nohup", "exec", "nice", "xargs"}
GIT_OPTIONS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}
COMMIT_OPTIONS_WITH_VALUE = {"-m", "--message", "-F", "--file", "-C", "-c", "--reuse-message", "--reedit-message", "-t", "--template", "--author", "--date"}


def command_head(command):
    """Keep lines up to and including the first one with `<<`; the rest is heredoc body."""
    kept = []
    for line in command.split("\n"):
        kept.append(line)
        if "<<" in line:
            break
    return "\n".join(kept)


def lex(text):
    lexer = shlex.shlex(text, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    return list(lexer)


def tokenize(text):
    """Line by line, so a newline ends a command; whole text when a quote spans lines."""
    try:
        tokens = []
        for line in text.split("\n"):
            tokens += lex(line) + [";"]
        return tokens
    except ValueError:
        pass
    try:
        return lex(text)
    except ValueError:
        return text.split()


def normalize(token):
    return token.lower().replace("${home}", "~").replace("$home", "~")


def secret_reason(token):
    """Why this token is off limits, or None."""
    for candidate in {normalize(token), normalize(token).split("=")[-1]}:
        base = candidate.rstrip("/").rsplit("/", 1)[-1]
        if base == ".env" or (base.startswith(".env.") and base != ".env.example"):
            return "a .env file"
        if base == "local.env":
            return "local.env"
        if base.endswith(".pem") or base.endswith(".key"):
            return "a key or certificate file"
        if base.startswith("id_rsa") or base.startswith("id_ed25519"):
            return "an SSH key"
        if candidate == "~" or candidate.startswith("~/"):
            first = candidate[2:].split("/")[0]
            if first == ".config" or (first.startswith(".") and re.search(r"[*?\[]", first) and fnmatch.fnmatchcase(".config", first)):
                return "~/.config"
        if re.match("/ho" + r"me/[^/]+/\.config(/|$)", candidate):
            return "~/.config"
    return None


def segments(tokens):
    current = []
    for token in tokens:
        if token in SEPARATORS:
            if current:
                yield current
            current = []
        else:
            current.append(token)
    if current:
        yield current


def short_flag(arg, wanted, takes_value):
    """True when the short-option cluster `arg` holds `wanted` before any option that takes a value."""
    if not re.fullmatch(r"-[A-Za-z]+", arg):
        return False
    for letter in arg[1:]:
        if letter == wanted:
            return True
        if letter in takes_value:
            return False
    return False


def git_reason(segment):
    """Why this command line is a forbidden git call, or None."""
    words = list(segment)
    while words and (("=" in words[0] and not words[0].startswith("-")) or words[0].strip("`$") in WRAPPERS):
        words.pop(0)
    if not words or words[0].strip("`").rsplit("/", 1)[-1] != "git":
        return None
    words.pop(0)
    while words and words[0].startswith("-"):
        option = words.pop(0)
        if option in GIT_OPTIONS_WITH_VALUE and words:
            words.pop(0)
    if not words:
        return None
    sub, args = words[0], words[1:]
    if sub == "commit":
        skip = False
        for arg in args:
            if skip:
                skip = False
            elif arg in ("--no-verify", "-n"):
                return "git commit --no-verify skips the hooks"
            elif arg in COMMIT_OPTIONS_WITH_VALUE:
                skip = True
            elif short_flag(arg, "n", "mFCct"):
                return "git commit -n skips the hooks"
    elif sub == "push":
        for arg in args:
            if arg in ("--force", "-f"):
                return "git push --force can overwrite remote history"
            if arg == "--no-verify":
                return "git push --no-verify skips the pre-push check"
            if short_flag(arg, "f", "o"):
                return "git push -f can overwrite remote history"
            if arg.startswith("+") and len(arg) > 1:
                return "git push +ref forces the update"
    return None


def decide(command):
    tokens = tokenize(command_head(command))
    for token in tokens:
        what = secret_reason(token)
        if what:
            return f"blocked: the command reads or writes {what} → ask the user to run it, or use an example file instead"
    for segment in segments(tokens):
        why = git_reason(segment)
        if why:
            return f"blocked: {why} → fix what the hook reports instead of bypassing it"
    return None


def main():
    data = json.load(sys.stdin)
    command = (data.get("tool_input") or {}).get("command")
    if not isinstance(command, str):
        return
    reason = decide(command)
    if reason:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}))


if __name__ == "__main__":
    try:
        main()
    except Exception as err:  # never block the session on our own bug
        print(f"block_secrets error: {type(err).__name__}: {err}", file=sys.stderr)
    sys.exit(0)
