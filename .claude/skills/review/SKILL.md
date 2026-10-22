---
name: review
description: Review a Clinic Booking branch or PR against REVIEW.md via code-reviewer and give a merge verdict. Use for "review this branch" or "is T-0NN ready to merge". Read-only.
---
This skill never edits files.

1. **Scope.** Default to `git diff develop...HEAD` plus any uncommitted changes, or the branch or range named. Read the ticket it implements.
2. **Review.** Run the **code-reviewer** subagent on the range and ticket. It works through REVIEW.md and the security guidance, and checks every AC and test case.
3. **Ticket status** is `In Progress` (or `Done` once the PR is open).
4. **Verdict.** **approve**, **approve with nits**, or **changes needed**, followed by the pytest line and the AC/test-case table (pass, fail, or manual).
5. Post nothing to GitHub unless asked.
