---
name: plan
description: Plan a ready Clinic Booking ticket before coding — implementation plan and testing strategy via planner, approved by the user, written into the ticket. Use for "plan T-0NN" or "how should we build T-0NN", or before /implement on an unplanned ticket.
---
This skill writes no app or test code.

1. **Ready check.** The ticket has ACs and test cases, and no blocking question is open. If not, go back to `/ticket` and stop.
2. Run the **planner** subagent with the ticket. For a new endpoint, a data-model change or backend-plus-frontend work, have it write `docs/specs/T-0NN-<slug>.md` from the spec template.
3. If the planner reports a gap or a missing decision in the ticket, show it to the user and stop. Requirement changes go back to `/ticket`.
4. **Approval gate:** show the plan to the user and stop until they approve it, or revise it with them.
5. Once approved, write it into the ticket's §8 Implementation plan (for a bug: §6 Analysis and §8 Fix and test). A filled §8 means the plan is approved.
6. Add an ADR (`docs/templates/adr.md`) for a decision future developers will question (storage, dependency, time handling, auth).
7. Next: `/implement` (feature, chore) or `/fix` (bug).
