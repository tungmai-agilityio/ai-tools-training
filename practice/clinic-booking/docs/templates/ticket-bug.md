# T-0NN: <Symptom as the reporter sees it>

**Status:** Open  **Type:** Bug  **Severity:** <S1 down|S2 wrong data/money|S3 workaround exists|S4 cosmetic>  **Priority:** <Low|Medium|High>  **Reporter:** <Name (role)>

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
- <what should happen, with the line of `docs/business-rules.md` that says so>

## 6. Analysis
- **Asks:** <one sentence>
- **Ambiguous:** <one sentence>
- **Root cause:** <`path:line` and why; "unknown" until proven>
- **Bug type:** <code | config | data>

## 7. Clarifying questions
1. <question> — <who answers>

## 8. Fix and test
- Failing test: `tests/test_<area>.py::test_<behaviour>` (fails before, passes after).
- Fix: <one line>

## 9. Definition of Done
- [ ] Failing test written first, now green; `pytest` green.
- [ ] Branch `fix/T-0NN`, one commit `fix: <what> (T-0NN)`, MR into `develop`. Status → In Review.
