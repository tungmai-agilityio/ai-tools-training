---
name: qa-report
description: Run the regression and browser tests for a PR, branch or develop in a throwaway worktree, read its CI, map results to the ticket test cases, and draft a QA-report Artifact. Use for "QA this PR", "run regression on develop" or "QA report for T-019 to T-023". Read-only on the app.
---
QA never edits app code or tests, and never pushes, merges or comments on a PR or issue unless the user asks. Defects stay drafts in the report.

1. **Target.** A PR number, branch or `develop`, and the tickets it covers (`plans/tickets/T-NNN.md`). Ask once if unclear.
2. **Isolate.** `git fetch origin`, then `git worktree add -b qa/<target> <tmp>/wt origin/<branch>` (use `gh pr checkout` data for a PR head). Never name it `claude/*`.
3. **Environment.** In a venv, `make install` and `playwright install chromium`. The suite already freezes the clock and uses an in-memory DB with fake data. If the command guard blocks the install, stop and tell the user.
4. **Regression.** `pytest -q --junitxml=<out>/junit.xml -rs`, then run `tests/test_ui_browser.py` three more times to spot flakes. Screenshots land in `test-artifacts/screenshots/`. A skipped browser test is a finding, not a pass.
5. **CI.** `gh run list --workflow ci.yml`, `gh pr checks <N>`, and `gh run view <id> --log-failed` for failures. Note whether a CI run exists for the target's head commit, run time, and any earlier failed run.
6. **Map.** From the worktree root: `python3 .claude/skills/qa-report/map_cases.py <out>/junit.xml T-019=tests/test_login.py,tests/test_auth.py T-020=...` (one `ticket=files` per ticket). A test belongs to case `TC-n` through the `# TC-n` comment on its `def` line. Cases come from the ticket's `| TC-n |` rows; the output flags cases with no test and tests with no case.
7. **Report.** Publish a draft Artifact for the user to edit: verdict (pass, pass with notes, fail) and recommendation first; run facts (commit, versions, counts); findings with severity; a case table filterable by ticket, type and result; failures with log excerpts and screenshots; flaky tests; coverage gaps (spec edge cases with no case, CI not running browser tests). Mark it Claude-assisted.
8. **Sync results.** Read the feature's test-cases Artifact first (from the ticket's Working Artifacts link), then republish it with its Last run data updated: result per case, date, commit and the report link. Merge into the live version and keep every human edit. Results are evidence only; the ticket Markdown stays the source.
9. **Clean up.** Check `git status` and `git log origin/<branch>..qa/<target>` are empty, then `git worktree remove` the worktree and `git branch -d qa/<target>`. Mention it in the report.
