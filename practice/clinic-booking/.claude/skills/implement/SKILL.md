---
name: implement
description: Implement a planned Clinic Booking feature or chore ticket end to end — branch, test-first code via backend-dev/frontend-dev, one commit, review and QA via /review. Use when the user says "implement T-0NN", "build T-0NN", "do the ticket", or "start coding T-0NN". For bugs use /fix.
---
Never open, read, or grep `.instructor/`. References: `docs/references/code-conventions.md`, `git-conventions.md`, `testing-conventions.md`.

1. **Ready check.** The ticket has Approach, acceptance criteria and a test plan, and no unanswered open questions. If not, run `/plan` and stop at its gate.
2. **Branch.** `git switch develop && git pull`, then `git switch -c feat/T-0NN` (`chore/<slug>` for a chore). Set the ticket's status to `In Progress`.
3. **Build.** Give the agent the ticket path and the ACs it owns:
   - API, rules, persistence, tests → **backend-dev**.
   - `app/static/index.html` → **frontend-dev**.
   - Both: backend-dev first, then frontend-dev against the finished API. Never run both on the same files at once.
4. **Verify.** Run `pytest` yourself. Do not trust an agent's summary line. Each new test must be one that failed before the change.
5. **Commit.** Update the docs if behaviour or rules changed, then squash everything into one commit: `feat: <what> (T-0NN)`, or `chore: <what> (T-0NN)` for a chore ticket. The status stays `In Progress`; `/pr` moves it. Do not push.
6. **Review.** Run `/review`. It covers code review, security and QA. If the verdict is **changes needed**, send each finding back to the agent that wrote the code (step 3), amend the commit, and run `/review` again. Ask the user before acting on a finding that changes scope.
7. Report: ACs and their evidence, the pytest line, review verdict, out-of-scope notes (offer `/ticket` for each). Next step: `/pr`.
