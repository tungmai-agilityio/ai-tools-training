#!/usr/bin/env bash
# Prints full=false only when every changed file is docs or planning (the old paths-ignore meaning); any doubt prints full=true.
# Usage: ci_needs_tests.sh <base-sha> [head-sha]
base=$1 head=${2:-HEAD}
case $base in
  ''|0000000000000000000000000000000000000000) echo full=true; exit 0;;  # first push or new branch
esac
# a force-push can leave the base unreachable: run everything. --no-renames lists both sides of a rename.
files=$(git diff --name-only --no-renames "$base" "$head" 2>/dev/null) || { echo full=true; exit 0; }
if [ -n "$files" ] && ! grep -vqE '\.md$|^docs/|^plans/|^\.github/ISSUE_TEMPLATE/' <<<"$files"; then
  echo full=false
else
  echo full=true
fi
