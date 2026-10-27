---
name: sprint-prepare
description: Plan a sprint — review ticket readiness, priorities, estimates and dependencies, propose a goal and feasible scope, and on approval write plans/sprints/S-NNN.md and set Sprint on the tickets. Use for "prepare the next sprint" or "plan sprint S-002".
---
Format: `docs/references/ticket-sync.md`. Writes Markdown only; never touches GitHub. Replace `S-NNN` with the sprint ID.

1. **Backlog.** Read `plans/tickets/`: tickets with no `Sprint`, plus `plans/sprints/` for dates and past sprints (carried-over tickets, how much got done). Run `python3 scripts/tickets.py check --all` and drop invalid tickets from the proposal.
2. **Readiness.** A ticket is ready when it has ACs and test cases, an Estimate, and no blocking question. A plan is not needed: `/plan-work` runs per ticket after the sprint is approved (a ticket with `**Feature:**` still needs its approved spec before it can be pushed). List the unready ones with what is missing; do not schedule them.
3. **Propose.** Ask for the sprint dates and capacity if the user hasn't given them (one question at a time, recommended answer first). Then propose a goal and a scope: order by priority, respect dependencies (a ticket's `Related:` / plan), and stay within capacity using the Estimates. Show what is left out and why, and the risks.
4. **Approval gate.** Stop until the user approves or changes the scope. Never invent capacity or estimates.
5. **Write.** Create `plans/sprints/S-NNN.md` (next free number, checked against `origin/develop`; never overwrite a file) in the sprint format, with `**Status:** Planned`, and set `**Sprint:** S-NNN` on each approved ticket. Leave the `## Tickets` block between its markers empty; `/sync-tickets --sprint S-NNN` fills it.
6. Next: mark scoped tickets `**Push:** Ready` (the user decides), then `/push-tickets --sprint S-NNN`.
