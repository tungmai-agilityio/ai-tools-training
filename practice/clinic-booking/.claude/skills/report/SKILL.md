---
name: report
description: Write a Clinic Booking test report (QA result for a ticket, MR or release) or a weekly status report from the tickets and git history. Use when the user asks for a test report, QA report, status report, weekly update, or sprint summary.
---
Never open, read, or grep `.instructor/`.

**Test report** (`docs/templates/test-report.md` → `docs/reports/test-<T-0NN|release>-<YYYY-MM-DD>.md`):
1. Run `pytest` and paste the real summary line. Note the branch and `git rev-parse --short HEAD`.
2. One test case per acceptance criterion in the ticket, plus the edge cases in `docs/references/testing-conventions.md` that apply.
3. Mark a case Pass only if you ran it. Not run is Not run. Defects found get a bug ticket (`/ticket`), linked here.
4. The recommendation follows from the results, not from optimism.

**Status report** (`docs/templates/status-report.md` → `docs/reports/status-<YYYY-MM-DD>.md`):
1. Build it from the `**Status:**` line of every `tickets/T-*.md` and `git log develop --merges --since=<date>`.
2. Blocked items name who must decide. Overall colour is 🟡 or 🔴 if anything is blocked past its ETA.
