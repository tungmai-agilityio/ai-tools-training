---
name: implement
description: Implement a planned Clinic Booking feature or chore ticket end to end — branch, test-first code via backend-dev/frontend-dev, review, QA, one commit, status In Review. Use when the user says "implement T-0NN", "build T-0NN", "do the ticket", or "start coding T-0NN". For bugs use /fix.
---
Never open, read, or grep `.instructor/`. References: `docs/references/code-conventions.md`, `git-conventions.md`, `testing-conventions.md`.

1. **Ready check.** The ticket has Approach, acceptance criteria and a test plan, and no unanswered open questions. If not, run `/plan` and stop at its gate.
2. **Branch.** `git switch develop && git pull`, then `git switch -c feat/T-0NN` (`chore/<slug>` for a chore). Set the ticket's status to `In Progress`.
3. **Build.** Give the agent the ticket path and the ACs it owns:
   - API, rules, persistence, tests → **backend-dev**.
   - `app/static/index.html` → **frontend-dev**.
   - Both: backend-dev first, then frontend-dev against the finished API. Never run both on the same files at once.
4. **Verify.** Run `pytest` yourself. Do not trust an agent's summary line. Each new test must be one that failed before the change.
5. **Review.** Run the **code-reviewer** subagent. Also run **security-auditor** when the diff touches auth, SQL, HTML rendering, input models or config. Send each finding that holds up back to the agent that wrote the code, then re-run `pytest`. Ask the user before acting on a finding that changes scope.
6. **QA.** Run the **qa-tester** subagent against the ACs. A fail goes back to step 3. List "manual" items for the user.
7. **Commit.** Squash to one commit `feat: <what> (T-0NN)`. Update docs if behaviour or rules changed. Set the ticket's status to `In Review`. Do not push.
8. Report: ACs and their evidence, the pytest line, review verdict, out-of-scope notes (offer `/ticket` for each). Next step: `/mr`.

If a subagent type is not registered (Claude Code was not opened in `practice/clinic-booking/`), spawn a general-purpose agent whose prompt starts with "Read `.claude/agents/<name>.md` and follow it exactly".
