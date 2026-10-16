---
name: plan
description: Plan a Clinic Booking ticket before any code is written — analyse it, surface open questions, design the change and fill the ticket's Approach, Acceptance criteria and Test plan. Use when the user says "plan T-0NN", "how should we do T-0NN", "break this ticket down", or before /implement or /fix on an unplanned ticket.
---
Never open, read, or grep `.instructor/`. This skill writes no code.

1. Read `tickets/T-0NN.md`. If it is too thin to work from, run `/ticket` on it first.
2. Run the **ticket-analyst** subagent on it.
3. **Stop gate:** if it returns questions the ticket, the reporter or `docs/business-rules.md` does not answer, or any OPEN QUESTION, show them to the user and stop. Never pick an answer yourself.
4. Run the **solution-architect** subagent with the ticket and the analysis. For a feature that adds an endpoint, changes the data model or spans backend and frontend, have it write a spec with `/spec` instead.
5. Write the result into the ticket (keep the reporter's text): Analysis, Approach (`path:line`), Given/When/Then acceptance criteria, Test plan (failing tests named after the behaviour), Out of scope. Use the section names in `docs/templates/ticket-feature.md` or `ticket-bug.md`.
6. Say which skill comes next: `/fix` (bug), or `/implement` (feature, chore), and which agents it will use (backend-dev, frontend-dev, or both).

If a subagent type is not registered (Claude Code was not opened in `practice/clinic-booking/`), spawn a general-purpose agent whose prompt starts with "Read `.claude/agents/<name>.md` and follow it exactly".
