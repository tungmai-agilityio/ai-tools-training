---
name: release
description: Release management for Clinic Booking — run release checks (green develop, clean tree, no unmerged tickets), prepare release notes, open develop → main PR, and tag main after merge. Use when the user says "cut a release", "release management", "release checklist", "ship develop to main", "write release notes", or "tag v0.N.0".
---
Reference: `docs/references/git-conventions.md` (Releases). Pushing, merging and tagging change shared state, so **ask before each one**.

**Check** (stop and report on the first failure)

1. `git switch develop && git fetch origin && git pull`. The working tree is clean.
2. `pytest` is green on `develop`.
3. No ticket in `tickets/` is `In Progress` or `In Review` with its branch already merged (a half-moved status). List any `Done` ticket whose branch is not in `develop`.
4. No OPEN QUESTION in `docs/business-rules.md` is decided in code since the last release: for each OPEN QUESTION, grep `git diff <last-tag>..develop -- app/` for its topic.
5. `.env.example` lists every env var read in `app/` (`grep -rnE "getenv|environ" app/`). A new var means a deploy note.

**Notes**

6. Last tag: `git describe --tags --abbrev=0 origin/main` (none → first release is `v0.1.0`, range is all of `develop`).
7. Version: any `feat` → bump minor, only `fix`/`chore`/`docs` → bump patch. Before `v1.0.0`, never bump major.
8. Collect `git log <last-tag>..develop --merges --format=%s` and the matching ticket titles. Write `docs/releases/vX.Y.Z.md`: **Features**, **Fixes**, **Deploy notes** (new env vars, data changes to `data/seed.json`, anything that needs `data/clinic.db` reset). One line per ticket, `T-0NN title`. Copy each merged ticket's `## Deploy note` section verbatim into **Deploy notes** (e.g. a `/db-migration` script to run first). Skip `docs`/`chore` unless they change deploy.

**Ship**

9. Branch `docs/release-vX.Y.Z` from `develop`, commit the notes as `docs: release notes vX.Y.Z`, and run `/pr` for it into `develop` (no ticket: skip `/pr`'s ticket-status steps).
10. After it merges: **go-ahead →** `gh pr create --head develop --base main --title "release: vX.Y.Z" --body-file docs/releases/vX.Y.Z.md`. Never pass `--delete-branch` when merging: `develop` must stay.
11. After approval and merge: **go-ahead →** `git fetch && git tag -a vX.Y.Z origin/main -m "vX.Y.Z" && git push origin vX.Y.Z`. Then **go-ahead →** mirror to GitLab: `git push gitlab main vX.Y.Z`.
12. Report: version, PR link, tag, deploy notes. Any problem found in the checks that is not a blocker → offer `/ticket`.
