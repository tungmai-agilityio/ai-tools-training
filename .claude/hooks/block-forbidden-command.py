#!/usr/bin/env python3
"""PreToolUse(Bash) hook: block commands CLAUDE.md forbids. Exit 2 = block.

A guardrail, not a control: real enforcement is branch protection on GitHub.
"""
import json
import os
import re
import shlex
import subprocess
import sys

PROTECTED = {"develop", "main"}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "mksh", "ash", "fish", "busybox", "eval"}
# git-push options that take a separate value argument
PUSH_VALUE_OPTS = {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}
# git global options that take a separate value argument
GIT_VALUE_OPTS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}

ENV_FILE = r"(?<![\w.])\.env(?!\.example)\b"
NO_ENV = "don't commit `.env`"
NO_PIP = "no new dependencies; edit requirements.txt only if the ticket says so"
PIP = re.compile(r"pip(\d+(\.\d+)?)?")
# raw-text rules run on every command (they also catch quoted `sh -c`/`$(...)` text); the token checks in main()
# add the forms they miss, such as `git -C . add .env` and `pip --quiet install x`
RULES = [
    (r"git\s+add\s+.*" + ENV_FILE, NO_ENV),
    (r"\bpip[\d.]*\s+install\s+(?!-r\b)", NO_PIP),
]
# a backslash-newline joins lines only when the backslash itself is unescaped (an odd run of backslashes)
CONTINUATION = re.compile(r"(?<!\\)((?:\\\\)*)\\\n")


NO_ALIAS = "no git aliases: they hide the real subcommand from this check"
NO_EXPANSION = "no `$` or backticks in a git push: write the values out"
NO_COMMENT = "no `#` comments in a command that pushes or installs: remove them"


def pip_install(seg):
    """True if the segment runs `pip [opts] install` with anything but exactly `-r requirements.txt`."""
    for k, tok in enumerate(seg):
        if PIP.fullmatch(os.path.basename(tok)) and "install" in seg[k + 1:]:
            j = seg.index("install", k + 1)
            return seg[j + 1:] != ["-r", "requirements.txt"]
    return False


def git_alias(seg):
    """True if the segment can hide git's real subcommand: an alias (`-c alias.x=`, `git config alias.x`,
    `--config-env`, `GIT_CONFIG_*` env) or shell expansion where the subcommand goes (`git $'push'`)."""
    git = [k for k, t in enumerate(seg) if os.path.basename(t) == "git"]
    if not git:
        return False
    rest = seg[git[0] + 1:]
    # config keys are case-insensitive, and include.path / includeIf can load aliases from another file
    hidden = ("alias.", "include")
    inline = any(a == "-c" and b.lower().startswith(hidden) for a, b in zip(rest, rest[1:]))
    config = any(a.lower().startswith(hidden) for a in (git_args(seg, "config") or []))
    env = any(t.startswith(("GIT_CONFIG", "--config-env")) for t in seg)
    i = git[0] + 1
    while i < len(seg) and seg[i].startswith("-"):
        i += 2 if seg[i] in GIT_VALUE_OPTS else 1
    expanded = any("$" in t or "`" in t for t in seg[git[0] + 1:i + 1])
    return inline or config or env or expanded


def segments(cmd):
    """Split a shell command into token lists, one per simple command."""
    # a newline or backtick also ends a command (main() has already joined backslash-newline continuations)
    lex = shlex.shlex(cmd, posix=True, punctuation_chars="();<>|&`\n")
    lex.whitespace = " \t\r"
    lex.whitespace_split = True
    lex.commenters = ""  # shlex would treat `a#b` as a comment and swallow the rest; bash doesn't, so read it all
    segs, inner = [[]], []
    for tok in lex:
        if set(tok) <= set("();<>|&`\n"):
            segs.append([])
        else:
            if re.search(r"\s", tok) and any(os.path.basename(t) in SHELLS for t in segs[-1]):
                inner += segments(tok)  # sh -c "git push ..." / eval "...": read the script too
            segs[-1].append(tok)
    return segs + inner


def git_args(seg, sub):
    """Arguments after `git [global opts] <sub>`, or None if this segment is not that git subcommand."""
    git = [k for k, t in enumerate(seg) if os.path.basename(t) == "git"]
    if not git:
        return None
    i = git[0] + 1
    while i < len(seg) and seg[i].startswith("-"):
        i += 2 if seg[i] in GIT_VALUE_OPTS else 1
    return seg[i + 1:] if i < len(seg) and seg[i] == sub else None


def current_branch():
    try:
        out = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def check_push(args):
    """Return why this push is forbidden, or None."""
    flags, positional, i = [], [], 0
    while i < len(args):
        a = args[i]
        if a.startswith("-"):
            flags.append(a)
            i += 2 if a in PUSH_VALUE_OPTS else 1
        else:
            positional.append(a)
            i += 1
    refspecs = positional[1:]  # first positional is the remote
    short = "".join(f[1:] for f in flags if not f.startswith("--"))
    hard = "--force" in flags or "f" in short or any(r.startswith("+") for r in refspecs)
    lease = any(f.startswith(("--force-with-lease", "--force-if-includes")) for f in flags)
    if hard:
        return "use --force-with-lease, never --force or a +refspec"
    if "--mirror" in flags or "--all" in flags:
        return "no --mirror or --all pushes"
    if not lease:
        return None
    # a lease push is fine on a feature branch; it must never reach a protected one
    targets = {r.split(":")[-1].removeprefix("refs/").removeprefix("heads/") for r in refspecs}
    if not refspecs or "HEAD" in targets:
        targets = (targets - {"HEAD"}) | {current_branch() or "unknown"}  # implicit target: fail closed
    if targets & (PROTECTED | {"unknown"}):
        return "never force-push develop or main"
    return None


def main():
    # join line continuations so `git push \<newline>--force` parses as one command, but keep `\\<newline>` as a break
    cmd = CONTINUATION.sub(r"\1", json.load(sys.stdin).get("tool_input", {}).get("command", ""))
    why = None
    try:
        for seg in segments(cmd):
            why = why or (NO_ALIAS if git_alias(seg) else None)
            args = git_args(seg, "push")
            if args is not None and any("$" in a or "`" in a for a in args):
                why = why or NO_EXPANSION  # $'--force', $F, "$(echo --force)": the shell expands what we can't see
            why = why or (check_push(args) if args is not None else None)
            added = git_args(seg, "add") or []
            why = why or (NO_ENV if any(re.search(ENV_FILE, a) for a in added) else None)
            why = why or (NO_PIP if pip_install(seg) else None)
    except Exception:  # unparseable or a hook bug: only exit code 2 blocks, so fail closed for anything push-like
        if re.search(r"\bgit\b.*\bpush\b", cmd, re.S):
            why = "could not parse this git push; simplify the command"
    if re.search(r"\bgit\b.*\bpush\b", cmd, re.S) and "`" in cmd:
        why = why or NO_EXPANSION  # an unquoted backtick splits off its body, so check the raw text
    if re.search(r"(?:^|\s)#", cmd) and re.search(r"\bgit\b.*\bpush\b|\bpip[\d.]*\b.*\binstall\b", cmd, re.S):
        why = why or NO_COMMENT  # segments() reads comments as code, so a quote opened in one can hide the next line
    for pattern, rule in RULES:
        why = why or (rule if re.search(pattern, cmd) else None)
    if why:
        print(f"Blocked: {why}.", file=sys.stderr)
        sys.exit(2)


main()
