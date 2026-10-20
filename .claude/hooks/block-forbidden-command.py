#!/usr/bin/env python3
"""PreToolUse(Bash) hook: block commands CLAUDE.md forbids. Exit 2 = block."""
import json
import re
import sys

RULES = [
    (r"\.instructor", "`.instructor/` holds the answer key; never open it"),
    (r"git\s+add\s+.*(?<![\w.])\.env(?!\.example)\b", "don't commit `.env`"),
    (r"git\s+push\b.*(--force|-f\b)", "no force pushes"),
    (r"git\s+push\b.*\bgitlab\b", "GitLab is a mirror: push only when asked"),
    (r"pip\s+install\s+(?!-r\b)", "no new dependencies; edit requirements.txt only if the ticket says so"),
]

cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "")
for pattern, why in RULES:
    if re.search(pattern, cmd):
        print(f"Blocked: {why}.", file=sys.stderr)
        sys.exit(2)
