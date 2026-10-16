---
name: test-plan
description: Write a QA test plan for a Clinic Booking ticket before coding — test cases per acceptance criterion, edge cases, automation level, exit criteria. Use when the user says "test plan for T-0NN", "what should we test", "write test cases", or after /plan and before /implement or /fix.
---
Never open, read, or grep `.instructor/`. This skill writes no app or test code.

1. Read the ticket, `docs/business-rules.md`, `docs/references/testing-conventions.md` and the existing tests in the area. A ticket without acceptance criteria goes to `/plan` first.
2. Fill in `docs/templates/test-plan.md` and save it as `docs/test-plans/T-0NN.md`.
   - At least one happy and one error case per AC. Error cases use the real status codes (`DomainError` 409 or 422, 403 for admin, 404).
   - Go through the edge-case checklist. Mark each item N/A with a reason, never just skip it.
   - Mark a case as already covered when an existing test covers it, citing `path::test_name`.
   - Name each new automated test after the behaviour, and say which ones must fail before the change.
3. Link the plan from the ticket's Test plan section (§8 Fix and test for a bug).
4. When the code is ready, the **qa-tester** subagent runs the plan, and `/report` turns the results into a test report.
