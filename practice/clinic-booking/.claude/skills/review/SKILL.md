---
name: review
description: Review a Clinic Booking branch or MR before merge — correctness and conventions (code-reviewer), security (security-auditor) and acceptance criteria (qa-tester) in parallel, merged into one verdict. Use when the user says "review this branch", "review the MR", "is T-0NN ready to merge", or "check my changes". Read-only.
---
Never open, read, or grep `.instructor/`. This skill never edits files.

1. **Scope.** Default to `git diff develop...HEAD` plus any uncommitted changes, or the branch or range the user names. Find the ticket from the branch name or commit subject.
2. Run these in parallel, each given the range and the ticket:
   - **code-reviewer**: always.
   - **security-auditor**: when the diff touches `routes.py` auth, `store.py` SQL, `index.html` rendering, `models.py`, config or `.env*`. Scope it to the diff.
   - **qa-tester**: when the ticket has acceptance criteria and `app/` changed.
3. **Merge.** Drop duplicates. Check every remaining finding against the code yourself and drop any you cannot back up. Rank them blocker → major → minor → nit, as `path:line — problem — failure case — fix`.
4. **Git hygiene** (`git-conventions.md`): branch name, one commit, commit format, rebased on `develop`, no `.env` or `*.db`, ticket status `In Review`.
5. **Verdict:** **approve**, **approve with nits**, or **changes needed**, followed by the pytest line and an AC table (pass, fail or manual).
6. Post nothing to GitLab unless the user asks.
