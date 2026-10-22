---
name: review
description: Review a Clinic Booking branch or PR before merge — correctness, conventions, and security via code-reviewer, plus automated git hygiene checks. Use when the user says "review this branch", "review the PR", "is T-0NN ready to merge", or "check my changes". Read-only.
---
This skill never edits files.

1. **Scope.** Default to `git diff develop...HEAD` plus any uncommitted changes, or the branch or range named. Read the ticket it implements.
2. **Review.** Run the **code-reviewer** subagent on the range and ticket. It audits correctness, domain rules, security basics (REVIEW.md §4), tests, and acceptance criteria.
3. **Git hygiene** (`docs/references/git-conventions.md`):
   - Branch named `feat/T-0NN`, `fix/T-0NN`, or `chore/<slug>`.
   - Exactly one commit following `<type>: <what> (T-0NN)` format, rebased on `develop`.
   - No untracked secrets or databases: verify `git ls-files | grep -E '\.env$|\.db$'` outputs nothing.
   - Ticket status set to `In Progress` (or `In Review` once PR is opened).
4. **Verdict.** **approve**, **approve with nits**, or **changes needed**, followed by the pytest line and an AC table (pass, fail, or manual).
5. Post nothing to GitHub unless asked.
