<!-- Title: <type>: <what changed> (#N)   — same as the commit subject -->

## What
<1–3 sentences: what this PR changes.>

Closes #N

## Why
<The problem, in one or two sentences. Link the issue section rather than repeating it.>

## How
- <key change, `path` — why this way>
- <deliberate simplifications (`ponytail:` comments) and their ceiling>

## Acceptance criteria
- [ ] AC-1 <copied from the issue> — verified by `test_<name>` / manual step
- [ ] AC-2 ...

## How to test
```bash
pytest
```
Manual: <steps in the UI or `/docs`, with the expected result>

## Evidence
<Test output before (failing) and after (passing); screenshots for UI changes.>

## Checklist
- [ ] Branch `feat|fix|chore|docs/...` from `develop`, one commit, rebased on latest `develop`
- [ ] A test that failed before the change now passes; `pytest` green
- [ ] No existing test weakened or deleted
- [ ] Follows `docs/references/code-conventions.md` (cents, UTC, `clock.now_utc()`, `DomainError`, `_move()`, `store.save()`)
- [ ] Only this issue's scope; other findings noted as new issues
- [ ] No secrets, `.env`, `data/*.db` or real data
- [ ] Docs / business rules updated if behaviour changed

## Notes for the reviewer
<Where to look first, what you are unsure about, follow-up issues.>
