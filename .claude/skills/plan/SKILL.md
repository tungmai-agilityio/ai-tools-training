---
name: plan
description: Plan a Clinic Booking ticket before any code is written — analyse it, stop on open questions, design the change, and fill the ticket's approach, acceptance criteria and test cases (writing a spec, rule change or ADR when the change needs one). Use when the user says "plan T-0NN", "spec this", "how should we build T-0NN", "what should we test", "the client decided X", or before /implement or /fix on an unplanned ticket.
---
This skill writes no app or test code.

1. Read `tickets/T-0NN.md`. If it is too thin to work from, run `/ticket` on it first.
2. Run the **business-analyst** subagent on it.
3. **Stop gate:** if it returns questions that the ticket, the reporter or `docs/business-rules.md` does not answer, or any OPEN QUESTION, show them to the user and stop. Never pick an answer yourself.
4. **Rule change.** If the user gives an approved answer (a named person and role), update `docs/business-rules.md` in its style: one testable sentence ending `(T-0NN, approved by <role>)`. Replace the line or OPEN QUESTION instead of adding a contradicting one.
5. Run the **solution-architect** subagent with the ticket and the analysis. If the feature adds an endpoint, changes the data model or spans backend and frontend, also have it write `docs/specs/T-0NN-<slug>.md` from `docs/templates/spec.md`.
6. **Test cases.** At least one happy and one error case per AC (409/422/403/404). Go through the edge-case checklist in `docs/templates/test-plan.md` and mark items N/A with a reason. Name each new test after the behaviour and say which must fail first.
7. **Write it into the ticket** (keep the reporter's text): Analysis, Approach (`path:line`), Given/When/Then ACs, Test plan, Out of scope. For a bug (`ticket-bug.md`): Approach → §6 Root cause, ACs → §5, test cases and out of scope → §8.
8. **Lasting decision?** If the design picks something future devs will question (storage, dependency, time handling, auth), add `docs/adr/NNNN-<slug>.md` from `docs/templates/adr.md`.
9. Next step: `/fix` (bug) or `/implement` (feature, chore), and which agents it will use.
