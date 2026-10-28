#!/usr/bin/env python3
"""PostToolUse(Edit|Write) hook: ruff-fix edited .py files; exit 2 feeds leftover errors back."""
import json
import shutil
import subprocess
import sys

path = json.load(sys.stdin).get("tool_input", {}).get("file_path", "")
if not path.endswith(".py") or not shutil.which("ruff"):  # ruff is optional, not a dependency
    sys.exit(0)

r = subprocess.run(["ruff", "check", "--fix", "--quiet", path], capture_output=True, text=True)
if r.returncode:
    print(r.stdout + r.stderr, file=sys.stderr)
    sys.exit(2)
