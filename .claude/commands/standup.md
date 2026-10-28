---
description: My standup — what I did since the last working day, what's in flight, what's blocked on Clinic Booking
allowed-tools: Bash(git log:*), Bash(git config:*), Bash(git branch:*), Bash(git status:*), Bash(date:*), Bash(head:*), Bash(grep:*), Bash(echo:*), Bash(gh issue list:*), Bash(true)
argument-hint: "[since, e.g. 2026-10-12 or monday; default: start of the last working day]"
disable-model-invocation: true
---
My commits (since: "$ARGUMENTS", empty = start of the last working day; Monday and Sunday → Friday):
```!
S=$(cat <<'ARGS_END'
$ARGUMENTS
ARGS_END
)
case "$S" in *[!0-9A-Za-z:\ -]*) echo "bad argument"; exit 0;; esac
[ -n "$S" ] || S="$(date -v-$(case "$(date +%u)" in 1) echo 3;; 7) echo 2;; *) echo 1;; esac)d +%F) 00:00"
git log --all --author="$(git config user.name)" --since="$S" --format='%h %ad %s' --date=short
```

My local branches, newest first:
!`git branch --sort=-committerdate --format='%(refname:short) %(committerdate:relative)' | head -8`

Uncommitted work:
!`git status --short`

Issues in flight:
!`gh issue list --label in-progress 2>/dev/null || true`

Write my standup in three short bullet groups — **Yesterday**, **Today**, **Blockers** — max 3 bullets each, plain words, issue numbers (`#N`) where they exist. Today = in-flight branches and issues. Blockers = only what the data shows (failing work, PRs waiting on review); otherwise "none". No preamble.
