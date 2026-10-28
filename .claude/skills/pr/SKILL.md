---
name: pr
description: Open, rebase and merge a Clinic Booking GitHub pull request into develop — review gate, conflicts, description from the template, closing its issue. Use for "open a PR", "rebase on develop" or "merge issue N".
---
Reference: `docs/references/git-conventions.md`. **Ask before each push and each merge.**

**Open**
1. **Gate.** `/review-pr` must have passed on the current HEAD (**approve** or **approve with nits**); otherwise run it. **changes needed** means stop.
2. **Sync.** Rebase on `origin/develop`. For a conflict, read both sides and their issues, keep both intended behaviours, and never drop the other side's test. If rules conflict or the answer is unclear, stop and ask. Run `pytest` after any rebase.
3. **Describe.** Fill `.github/pull_request_template.md`: title = commit subject, `Closes #N`, every AC and test case mapped to evidence, and tick only what `/review-pr` verified. For a UI change, Evidence embeds the changed screens at both sizes and links the CI `screenshots` artifact; upload the same PNGs to the feature's UI-design Artifact ("As built").
4. **Go-ahead → open.** Push (`--force-with-lease` after a rebase) and run `gh pr create --base develop`. Report the link.

**Finish** (after GitHub approval)
5. If `develop` moved and GitHub reports a conflict, rebase (step 2) and push with `--force-with-lease`, then re-request approval.
6. **Go-ahead → merge** with `gh pr merge --merge --delete-branch`. GitHub closes the issue through `Closes #N`. Never merge or commit into `develop` locally.
7. Pull `develop`, check the merge commit and that the issue closed, and report it with any follow-ups.
