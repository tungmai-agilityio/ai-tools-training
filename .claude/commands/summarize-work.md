---
description: Summarize what the team did from N days ago (or "yesterday", "monday", a date) until now, from git history
allowed-tools: Bash(git log:*), Bash(git fetch:*), Bash(git diff:*), Bash(git show:*), Bash(grep:*), Bash(echo:*), Bash(sort:*), Bash(uniq:*), Bash(head:*), Bash(true)
argument-hint: "[N days | yesterday | 2026-10-12, default: 1]"
disable-model-invocation: true
---
```!
S=$(cat <<'ARGS_END'
$ARGUMENTS
ARGS_END
)
S="${S:-1}"
case "$S" in *[!0-9A-Za-z:\ -]*) echo "bad argument"; exit 0;; *[!0-9]*) ;; *) S="$S days ago";; esac
GIT_SSH_COMMAND='ssh -o BatchMode=yes' GIT_TERMINAL_PROMPT=0 git fetch -q origin develop 2>/dev/null || true
echo "Window starts: $S"; echo
echo "Commits on all branches, oldest first:"
git log --all --reverse --since="$S" --format='%h %ad %an | %s' --date=format:'%a %H:%M'; echo
echo "Merged into develop (origin, just fetched):"
git log origin/develop --merges --first-parent --since="$S" --format='%h %s'; echo
echo "Files touched:"
git log --all --since="$S" --name-only --format= | sort | uniq -c | sort -rn | head -15
```

Explain what happened in that window, for someone who missed it:
1. **One-line headline** of the window.
2. **Shipped** (merged into develop): one bullet per ticket — `T-0NN` and what changed for a user or a developer, not the commit text. Read `tickets/T-0NN.md` when the subject is unclear.
3. **In progress** (commits on branches not merged yet): branch, author, what it is heading for.
4. **Worth knowing**: changes to `docs/business-rules.md`, `.env.example`, `data/seed.json`, `.claude/`, or tests removed — only if the data shows them.
Group by ticket, not by commit. No commits in the window → say so in one line and stop.
