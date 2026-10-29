---
name: release
description: Cut a Clinic Booking release for one sprint — verify its tickets, write the notes, open the develop → main PR, tag and publish after the merge. Use for "release sprint S-002", "cut a release" or "tag v0.N.0".
disable-model-invocation: true
---
Usage: `/release S-NNN` (the sprint is required). Reference: `docs/references/git-conventions.md` (Releases). **Ask before each push, merge and tag.**

**Verify** on an up-to-date `develop`; stop at the first failure and report what blocks:
- The tree is clean. `develop`'s head has green CI (`gh run list --branch develop`; PRs to `main` run `tests` too) and `pytest` passes locally.
- Run `python3 scripts/tickets.py sync --sprint S-NNN` (dry run, read-only; add `--issues-json` without a `GH_TOKEN`). Every ticket in `plans/sprints/S-NNN.md` needs its issue closed, its PR merged into `develop`, and its acceptance criteria and test cases passing (`/qa-report` on `develop` gives the evidence). Any other ticket **blocks** the release unless the user names it as carry-over. A ticket with no issue cannot be checked this way: ask the user to name it as carry-over or to create its issue first (`/push-tickets`).
- First release (no tag on `origin/main`): there is no baseline, so `develop` → `main` ships everything on `develop`. List every merged PR in the notes, not only the sprint's.
- PRs merged since the last tag that belong to no sprint ticket are listed as **extra** in the notes and PR: `develop` → `main` ships them too.
- No OPEN QUESTION decided in `app/` since the last tag. `.env.example` must list every setting in `app/config.py`; a missing one blocks the release, and a new one needs a deploy note.

**Notes**
1. Last tag: `git describe --tags --abbrev=0 origin/main` (none → `v0.1.0`). Any `feat` bumps the minor version, otherwise the patch; no major bump before `v1.0.0`.
2. Write `docs/releases/vX.Y.Z.md` from the sprint's tickets and their issues (`gh issue view N`): **Features**, **Fixes**, **Deploy notes** (new env vars, seed or DB changes, each issue's `## Deploy note` verbatim), **Sprint S-NNN summary** (goal from the sprint file; Done vs Carried over as `T-NNN #N title (state)`), and **Extra**. One line per issue as `#N title`; skip docs and chores unless they affect deploy.
3. Commit it on `docs/release-vX.Y.Z` and run `/pr` into `develop` (no issue to close). Merge before step 4.

**Ship**
4. **Go-ahead →** open the PR: `gh pr create --head develop --base main --title "release: vX.Y.Z" --body-file <body>`. The body has: summary and sprint goal; **Verification evidence** (ticket → issue → PR → state table, test and CI results for the head SHA); the notes (Features, Fixes); **Deploy checklist** (the Deploy notes, as tick boxes); **Known issues and carry-over**. Squash-merge it (`gh pr merge --squash`, the only method allowed) and never delete `develop` on merge.
5. After the merge, **go-ahead →** push an annotated `vX.Y.Z` tag on `origin/main`, which triggers `.github/workflows/release.yml` to draft the release from `docs/releases/vX.Y.Z.md`. Review the draft, then publish it with `gh release edit vX.Y.Z --draft=false`.
6. Run `/release-notes vX.Y.Z S-NNN` for the client-facing page.
7. Report the version, PR link, tag, release and client page, plus the deploy notes; offer `/create-ticket` for any non-blocking problems.
