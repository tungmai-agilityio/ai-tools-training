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
SEPARATORS = "();<>|&`\n"

ENV_FILE = re.compile(r"(?<![\w.])\.env(?!\.example)\b")
NO_ENV = "don't commit `.env`"
NO_GITLAB = "GitLab is a mirror: push only when asked"
NO_PIP = "no new dependencies; edit requirements.txt only if the ticket says so"
# raw-text fallback, only for commands shlex can't parse
RAW_RULES = [
    (r"git\s+add\s+.*" + ENV_FILE.pattern, NO_ENV),
    (r"git\s+push\b.*\bgitlab\b", NO_GITLAB),
    (r"pip\s+install\s+(?!-r\b)", NO_PIP),
]


def segments(cmd):
    """Split a shell command into token lists, one per simple command."""
    # newlines and backticks also end a command, so `echo git\ngit push` and `...` bodies split correctly
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=SEPARATORS)
    lex.whitespace = " \t\r"
    lex.whitespace_split = True
    segs, inner = [[]], []
    for tok in lex:
        if set(tok) <= set(SEPARATORS):
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
    if any(re.search(r"\bgitlab\b", a) for a in args):  # all args: --repo gitlab / --repo=gitlab too
        return NO_GITLAB
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


def check_segment(seg):
    """Return why this simple command is forbidden, or None. Quoted text is one token, so it never matches."""
    args = git_args(seg, "push")
    if args is not None:
        return check_push(args)
    args = git_args(seg, "add")
    if args is not None and any(ENV_FILE.search(a) for a in args):
        return NO_ENV
    # ponytail: shlex doesn't know heredocs, so a heredoc line `pip install x` still blocks; parse heredocs if that bites
    for k, tok in enumerate(seg):
        if os.path.basename(tok) in {"pip", "pip3"} and seg[k + 1:k + 2] == ["install"] and seg[k + 2:k + 3] not in ([], ["-r"]):
            return NO_PIP
    return None


def main():
    cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "")
    why = None
    try:
        for seg in segments(cmd):
            why = why or check_segment(seg)
    except Exception:  # unparseable or a hook bug: only exit code 2 blocks, so fail closed on the raw text
        if re.search(r"\bgit\b.*\bpush\b", cmd, re.S):
            why = "could not parse this git push; simplify the command"
        for pattern, rule in RAW_RULES:
            why = why or (rule if re.search(pattern, cmd) else None)
    if why:
        print(f"Blocked: {why}.", file=sys.stderr)
        sys.exit(2)


main()
