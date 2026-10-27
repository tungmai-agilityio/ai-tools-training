---
name: plan-work
description: Plan a ready Clinic Booking ticket before coding — implementation plan and testing strategy via planner, approved by the user, written into the ticket. Use for "plan T-018", "how should we build T-018", or before /implement-ticket on an unplanned ticket.
---
This skill writes no app or test code. Ticket format: `docs/references/ticket-sync.md`.

1. Read `plans/tickets/T-NNN.md`. **Ready check:** it has ACs and test cases, and no blocking question is open. If not, go back to `/create-ticket` and stop.
2. Run the **planner** subagent with the ticket text. For a new endpoint, a data-model change or backend-plus-frontend work, have it write `plans/features/<slug>/spec.md` from `docs/templates/spec.md` and set the ticket's `**Feature:**`.
3. If the planner reports a gap or a missing decision in the ticket, show it to the user and stop. Requirement changes go back to `/create-ticket`.
4. **Approval gate:** show the plan to the user and stop until they approve it, or revise it with them. Approving the plan also approves writing it into the ticket.
5. Write it into the ticket's `## Plan` section (a bug: `## Analysis` and `## Fix and test`) and set `**Plan:** Approved`. Never change the requirement or acceptance-criteria text. If the issue already exists, the issue body is not edited; the Markdown stays the source of truth.
6. Record a decision future developers will question (storage, dependency, time handling, auth) as an ADR from `docs/templates/adr.md`, or a UX/behaviour choice as a DDR from `docs/templates/ddr.md`, in `docs/decisions/` (next free number), and list it as `**Decisions:** ADR-0001`.
7. Next: `/sprint-prepare` or `/push-tickets`, then `/implement-ticket`.
