---
name: merge
description: Finish a Clinic Booking MR — rebase on develop, resolve conflicts, re-test, merge into develop, delete the branch and set the ticket to Done. Use when the user says "merge T-0NN", "merge the MR", "resolve the conflict", "rebase on develop", or "close the ticket".
---
Never open, read, or grep `.instructor/`. Reference: `docs/references/git-conventions.md`. Pushing and merging change shared state, so **ask before each push or merge**.

1. **Gate.** The branch has an approved review (`/review` verdict approve, or an approval on the GitLab MR: `glab mr view <branch>`). The ticket status is `In Review`. `git status` is clean.
2. **Sync.** `git fetch origin`, then `git rebase origin/develop`.
3. **Conflicts.** For each file, read both sides and the tickets behind them (`git log origin/develop -- <file>`).
   - Keep both behaviours when both are intended. Never drop the other side's test to make it merge.
   - Docs and tickets: merge the text by hand. Business rules: keep both lines, and ask the user if they contradict each other.
   - If the right answer is unclear, stop and show the user the conflict with both intents.
   - `git add` the file, then `git rebase --continue`.
4. **Re-test.** Run full `pytest` after the rebase, even if there were no conflicts. Red means stop.
5. **Push** (after a go-ahead): `git push --force-with-lease`.
6. **Merge** (after a go-ahead): `glab mr merge <branch> --remove-source-branch`. Without glab or a GitLab MR: `git switch develop && git merge --no-ff <branch> -m "Merge branch '<branch>' into 'develop'"`, push `develop`, and delete the branch.
7. **Close.** On `develop`, set the ticket status to `Done` and commit `chore: mark T-0NN done` (or include it in the MR before merging). Report the merge commit and any follow-up tickets.
