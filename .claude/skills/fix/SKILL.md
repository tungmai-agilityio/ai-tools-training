---
name: fix
description: Fix a Clinic Booking bug issue — find the root cause, prove it with a failing test, smallest fix via developer, one commit, /review. Use for "fix issue N" or a triaged bug. Features use /implement.
---
Same flow as `/implement` (including the `in-progress` label, and the `blocked` label while a Needs decision waits on the user), with these differences:

1. **Understand.** Read the issue (`gh issue view N`) and `docs/business-rules.md`. If the expected behaviour is unclear, needs design, or touches an OPEN QUESTION, run `/plan` and stop at its gate.
2. **Branch** `fix/<N>-<slug>`, then run the **developer** subagent with the issue text.
3. **Code, config or data?** If the cause is config (`.env`) or data (`data/seed.json`, `data/clinic.db`), say so and report the fix instead of bending the code. Change data or `.env.example` only when the issue asks. A config-only fix has no red-to-green test: let the user decide.
4. **Prove it.** Run the new test against the old code yourself: stash only `app/` under a named stash, then `git stash apply` and `drop` that entry. Never a bare `git stash pop`, because the stash is shared across worktrees. Then run full `pytest`. Red before, green after, or it isn't done.
5. **Commit** `fix: <what> (#N)`. **Go-ahead →** fill the issue's Root cause and Fix sections. Review and report as in `/implement`, including the cause at `path:line`.
