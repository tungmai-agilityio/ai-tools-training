---
name: Bug
about: Something that breaks a business rule or behaves wrongly
title: "<Symptom as the reporter sees it>"
labels: bug
---

**Severity:** <S1 down|S2 wrong data/money|S3 workaround exists|S4 cosmetic>  **Priority:** <Low|Medium|High>  **Reporter:** <Name (role)>

## 1. Summary
<One sentence: what is wrong, where, for whom.>

## 2. Environment
- Build / commit: <`git rev-parse --short HEAD`>
- Where: <UI screen | API endpoint | both>
- Config: <relevant `.env` values, never secrets>
- Clock: <clinic local date/time the bug happens at, if time matters>

## 3. Steps to reproduce
1. <exact step, with real (fake) ids and times>
2. ...

## 4. Actual behaviour
- <what happens; paste the response body / screenshot>

## 5. Expected behaviour
<The line of `docs/business-rules.md` that says so, then the acceptance criteria:>
- AC-1 Given <state>, when <action>, then <correct result>.

## 6. Analysis
- **Asks:** <one sentence>
- **Ambiguous:** <one sentence>
- **Root cause:** <`path:line` and why; "unknown" until proven>
- **Bug type:** <code | config | data>

## 7. Clarifying questions
1. <question> — <who answers>

## 8. Fix and test
- Code bug: failing test `tests/test_<area>.py::test_<behaviour>` (fails before, passes after).
- Config or data bug: no red-to-green test. Give the exact setting or record to change, and how to verify it (for example `GET /health`).
- Fix: <one line>

## Deploy note
<Optional. Only if deploying this needs a manual step (a `/db-migration` script to run, a new env var, a data reset). `/release` copies it verbatim into the release notes.>

## 9. Definition of Done
- [ ] Code bug: failing test written first, now green, and `pytest` green. Config or data bug: change applied and verified on the server.
- [ ] Code bug: branch `fix/<N>-<slug>`, one commit `fix: <what> (#N)`, PR into `develop` with `Closes #N`.
