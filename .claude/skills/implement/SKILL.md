---
name: implement
description: Implement a planned Clinic Booking feature or chore ticket using test-driven development — branch, red-to-green code via developer, one commit, review via /review. Use when the user says "implement T-0NN", "build T-0NN", "do the ticket", "test-driven development", or "start coding T-0NN". For bugs use /fix.
---
References: `docs/references/code-conventions.md`, `git-conventions.md`, `testing-conventions.md`.

1. **Ready check.** The ticket has Approach, acceptance criteria and a test plan, and no unanswered open questions. If not, run `/plan` and stop at its gate.
2. **Branch.** `git switch develop && git pull`, then `git switch -c feat/T-0NN` (`chore/<slug>` for a chore). Set the ticket's status to `In Progress`.
3. **Build.** Run the **developer** subagent with the ticket path and the acceptance criteria it owns. It follows test-driven development (failing tests first in `tests/`, then implementation in `app/` and `app/static/index.html`).
4. **Verify.** Run `pytest` yourself. Do not trust an agent's summary line. Each new test must be one that failed before the change.
5. **Commit.** Update the docs if behaviour or rules changed, then squash everything into one commit: `feat: <what> (T-0NN)`, or `chore: <what> (T-0NN)` for a chore ticket. The status stays `In Progress`; `/pr` moves it. Do not push.
6. **Review.** Run `/review`. If the verdict is **changes needed**, send each finding back to the developer agent, amend the commit, and run `/review` again. Ask the user before acting on a finding that changes scope.
7. Report: ACs and their evidence, the pytest line, review verdict, out-of-scope notes (offer `/ticket` for each). Next step: `/pr`.
