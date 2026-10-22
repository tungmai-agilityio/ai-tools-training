---
name: review
description: Review a Clinic Booking branch or PR against REVIEW.md via code-reviewer and give a merge verdict. Use for "review this branch" or "is issue N ready to merge". Read-only.
---
This skill never edits files.

1. **Scope.** Default to `git diff develop...HEAD` plus any uncommitted changes, or the branch or range named. Read the issue it implements (`gh issue view N`).
2. **Review.** Run the **code-reviewer** subagent on the range and issue. It works through REVIEW.md and the security guidance, and checks every AC and test case.
3. **Issue link.** The branch and commit carry the issue number (`<type>/<N>-<slug>`, `(#N)`).
4. **Verdict.** **approve**, **approve with nits**, or **changes needed**, followed by the pytest line and the AC/test-case table (pass, fail, or manual).
5. Post nothing to GitHub unless asked.
