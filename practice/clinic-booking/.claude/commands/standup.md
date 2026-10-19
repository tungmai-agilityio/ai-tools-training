---
description: My standup — what I did since the last working day, what's in flight, what's blocked on Clinic Booking
allowed-tools: Bash(git log:*), Bash(git config:*), Bash(git branch:*), Bash(git status:*), Bash(date:*), Bash(head:*), Bash(grep:*), Bash(echo:*), Bash(true)
argument-hint: "[since, e.g. 2026-10-12 or monday; default: start of the last working day]"
---
My commits (since: "$ARGUMENTS", empty = start of the last working day; Monday → Friday):
!`S='$ARGUMENTS'; case "$S" in *[!0-9A-Za-z:\ -]*) echo "bad argument"; exit 0;; esac; [ -n "$S" ] || S="$(date -v-$([ "$(date +%u)" = 1 ] && echo 3 || echo 1)d +%F) 00:00"; git log --all --author="$(git config user.name)" --since="$S" --format='%h %ad %s' --date=short`

My local branches, newest first:
!`git branch --sort=-committerdate --format='%(refname:short) %(committerdate:relative)' | head -8`

Uncommitted work:
!`git status --short`

Tickets in flight:
!`grep -lE '^\*\*Status:\*\* (In Progress|In Review)' tickets/T-*.md || true`

Write my standup in three short bullet groups — **Yesterday**, **Today**, **Blockers** — max 3 bullets each, plain words, ticket ids where they exist. Today = in-flight branches and tickets. Blockers = only what the data shows (failing work, tickets waiting on review); otherwise "none". No preamble.
