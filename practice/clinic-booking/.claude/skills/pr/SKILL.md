---
name: pr
description: Open and finish a Clinic Booking GitHub pull request — check the review gate, rebase on develop and resolve conflicts, write the description from the template, push and open the PR, then merge after approval and set the ticket Done. Use when the user says "open a PR", "ready for review", "write the PR description", "rebase on develop", "resolve the conflict", or "merge T-0NN".
---
Never open, read, or grep `.instructor/`. Reference: `docs/references/git-conventions.md`. Pushing and merging change shared state, so **ask before each push and each merge**.

**Open**
1. **Gate.** `/review` has run on the current HEAD with the verdict **approve** or **approve with nits**. If not, or HEAD changed since, run it. **changes needed** means stop.
2. **Sync.** `git fetch origin && git rebase origin/develop`. For each conflict, read both sides and the tickets behind them. Keep both behaviours when both are intended, and never drop the other side's test. If business rules contradict each other, or the right answer is unclear, stop and show the user. Run full `pytest` after any rebase.
3. **Describe.** Fill `.github/pull_request_template.md`: title = commit subject, every AC mapped to a test or manual step, checklist ticked only for what `/review` verified.
4. **Go-ahead → open.** Set the ticket status to `In Review` and amend it into the one commit. `git push -u origin <branch>` (`--force-with-lease` after a rebase), then `gh pr create --base develop --title "<subject>" --body-file <file>`. Report the link.

**Finish** (once the PR is approved on GitHub)
5. Rebase again if `develop` moved (step 2). Set the ticket status to `Done` as the last change, amend, and `git push --force-with-lease`. Re-request approval if the push reset it.
6. **Go-ahead → merge:** `gh pr merge <branch> --merge --delete-branch`, or the Merge button. Never merge or commit into `develop` locally.
7. `git switch develop && git pull`, check the merge commit, and report it with any follow-up tickets.
