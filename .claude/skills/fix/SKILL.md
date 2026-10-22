---
name: fix
description: Fix a Clinic Booking bug ticket — find the root cause, prove it with a failing test, smallest fix via developer, one commit, /review. Use for "fix T-0NN" or a triaged bug. Features use /implement.
---
Same flow as `/implement` (including its Needs-decision handling), with these differences:

1. **Understand.** Read the ticket and `docs/business-rules.md`. If the expected behaviour is unclear, needs design, or touches an OPEN QUESTION, run `/plan` and stop at its gate.
2. **Branch** `fix/T-0NN`, then run the **developer** subagent with the ticket.
3. **Code, config or data?** If the cause is config (`.env`) or data (`data/seed.json`, `data/clinic.db`), say so and report the fix instead of bending the code. Change data or `.env.example` only when the ticket asks. A config-only fix has no red-to-green test: let the user decide.
4. **Prove it.** Run the new test against the old code yourself: stash only `app/` under a named stash, then `git stash apply` and `drop` that entry. Never a bare `git stash pop`, because the stash is shared across worktrees. Then run full `pytest`. Red before, green after, or it isn't done.
5. **Commit** `fix: <what> (T-0NN)` after filling the ticket's Root cause and Fix sections. Review and report as in `/implement`, including the cause at `path:line`.
