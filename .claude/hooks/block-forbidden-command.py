#!/usr/bin/env python3
"""PreToolUse(Bash) hook: block commands CLAUDE.md forbids. Exit 2 = block.

A guardrail, not a control: real enforcement is branch protection on GitHub.
"""
import json
import re
import shlex
import subprocess
import sys

PROTECTED = {"develop", "main"}
# git-push options that take a separate value argument
PUSH_VALUE_OPTS = {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}
# git global options that take a separate value argument
GIT_VALUE_OPTS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}

RULES = [
    (r"git\s+add\s+.*(?<![\w.])\.env(?!\.example)\b", "don't commit `.env`"),
    (r"git\s+push\b.*\bgitlab\b", "GitLab is a mirror: push only when asked"),
    (r"pip\s+install\s+(?!-r\b)", "no new dependencies; edit requirements.txt only if the ticket says so"),
]


def segments(cmd):
    """Split a shell command into token lists, one per simple command."""
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    segs = [[]]
    for tok in lex:
        if set(tok) <= set("();<>|&"):
            segs.append([])
        else:
            segs[-1].append(tok)
    return segs


def push_args(seg):
    """Arguments after `git [global opts] push`, or None if this is not a push."""
    if "git" not in seg:
        return None
    i = seg.index("git") + 1
    while i < len(seg) and seg[i].startswith("-"):
        i += 2 if seg[i] in GIT_VALUE_OPTS else 1
    return seg[i + 1:] if i < len(seg) and seg[i] == "push" else None


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
    targets = {r.split(":")[-1].removeprefix("refs/heads/") for r in refspecs}
    if not refspecs or "HEAD" in targets:
        targets = (targets - {"HEAD"}) | {current_branch() or "unknown"}  # implicit target: fail closed
    if targets & (PROTECTED | {"unknown"}):
        return "never force-push develop or main"
    return None


def main():
    cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "")
    why = None
    try:
        for seg in segments(cmd):
            args = push_args(seg)
            why = why or (check_push(args) if args is not None else None)
    except ValueError:  # unbalanced quotes etc.: not a command we can reason about
        pass
    for pattern, rule in RULES:
        why = why or (rule if re.search(pattern, cmd) else None)
    if why:
        print(f"Blocked: {why}.", file=sys.stderr)
        sys.exit(2)


main()
