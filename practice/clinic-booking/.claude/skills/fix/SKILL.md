---
name: fix
description: Fix a Clinic Booking bug ticket — reproduce, prove the root cause with a failing test, smallest fix via bug-fixer, review, one commit. Use when the user says "fix T-0NN", "debug this ticket", "this is broken", or hands over a bug report. Not for features (/implement).
---
Never open, read, or grep `.instructor/`. References: `docs/references/testing-conventions.md`, `git-conventions.md`.

1. **Understand.** Read the ticket and `docs/business-rules.md`. If the expected behaviour is unclear or touches an OPEN QUESTION, run `/plan` and stop at its gate.
2. **Branch.** `git switch develop && git pull`, then `git switch -c fix/T-0NN`. Set the ticket's status to `In Progress`.
3. **Reproduce and fix.** Run the **bug-fixer** subagent with the ticket. It must show the new test failing before its fix.
4. **Code, config or data?** If the root cause is config (`.env`, `CLINIC_TIMEZONE`) or data (`data/seed.json`, `data/clinic.db`), say so. Fix data or `.env.example` only when the ticket asks for it. Otherwise report the fix to the user instead of bending the code. A pure config fix has no red-to-green test: tell the user and let them decide.
5. **Prove it.** Run the new test against the old code yourself (`git stash push -m fix-T-0NN -- app/`, run the test, then find that entry by its message in `git stash list` and `git stash apply` + `drop` it; never a bare `git stash pop`, because the stash is shared with other worktrees), then run full `pytest`. Red before and green after, or it is not done.
6. **Review.** Run the **code-reviewer** subagent, plus **security-auditor** if the bug is in auth, input or rendering. Send each finding that holds up back to bug-fixer.
7. **Commit.** One commit `fix: <what> (T-0NN)`. Fill the ticket's Root cause and Fix sections, and set the status to `In Review`. Do not push.
8. Report: cause (`path:line`), the fix, the test failing then passing, other bugs noticed (offer `/ticket`). Next step: `/mr`.

If a subagent type is not registered (Claude Code was not opened in `practice/clinic-booking/`), spawn a general-purpose agent whose prompt starts with "Read `.claude/agents/<name>.md` and follow it exactly".
