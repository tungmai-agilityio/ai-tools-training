---
name: release
description: Cut a Clinic Booking release — checks, release notes, develop → main PR, and tag. Use for "cut a release" or "tag v0.N.0".
disable-model-invocation: true
---
Reference: `docs/references/git-conventions.md` (Releases). **Ask before each push, merge and tag.**

**Check** on an up-to-date `develop`, and stop at the first failure:
- The tree is clean and `pytest` is green.
- Every ticket merged into `develop` is `Done`, and no `Done` ticket's branch is missing from `develop`.
- No OPEN QUESTION has been decided in `app/` since the last tag.
- `.env.example` lists every env var read in `app/`; a new one needs a deploy note.

**Notes**
1. Last tag: `git describe --tags --abbrev=0 origin/main` (none → `v0.1.0`). Any `feat` bumps the minor version, otherwise the patch. No major bump before `v1.0.0`.
2. Write `docs/releases/vX.Y.Z.md` from the merges since the tag: **Features**, **Fixes**, **Deploy notes** (new env vars, seed or DB changes, and each ticket's `## Deploy note` copied verbatim), one line per ticket. Skip docs and chores unless they affect deploy.

**Ship**
3. Commit the notes on `docs/release-vX.Y.Z` and run `/pr` into `develop` (skip its ticket-status steps).
4. **Go-ahead →** `gh pr create --head develop --base main --title "release: vX.Y.Z" --body-file docs/releases/vX.Y.Z.md`. Never delete `develop` on merge.
5. After the merge, **go-ahead →** tag `vX.Y.Z` on `origin/main` and push the tag to `origin`. Then tell the user to mirror to GitLab themselves (`git push gitlab develop main --tags`); the hook blocks GitLab pushes from Claude.
6. Report the version, PR link, tag and deploy notes; offer `/ticket` for any non-blocking problems.
