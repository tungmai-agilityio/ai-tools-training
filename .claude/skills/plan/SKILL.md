---
name: plan
description: Plan a ready Clinic Booking issue before coding — implementation plan and testing strategy via planner, approved by the user, written into the issue. Use for "plan issue N" or "how should we build issue N", or before /implement on an unplanned issue.
---
This skill writes no app or test code.

1. Read the issue (`gh issue view N`). **Ready check:** it has ACs and test cases, and no blocking question is open. If not, go back to `/ticket` and stop.
2. Run the **planner** subagent with the issue text. For a new endpoint, a data-model change or backend-plus-frontend work, have it write `docs/specs/<N>-<slug>.md` from the spec template.
3. If the planner reports a gap or a missing decision in the issue, show it to the user and stop. Requirement changes go back to `/ticket`.
4. **Approval gate:** show the plan to the user and stop until they approve it, or revise it with them. Approving the plan also approves writing it to the issue.
5. Write it into the issue body's §8 Implementation plan (`gh issue edit N --body-file <file>`; for a bug: §6 Analysis and §8 Fix and test). A filled §8 means the plan is approved.
6. Add an ADR (`docs/templates/adr.md`) for a decision future developers will question (storage, dependency, time handling, auth).
7. Next: `/implement` (feature, chore) or `/fix` (bug).
