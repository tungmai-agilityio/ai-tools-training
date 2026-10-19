# Test plan: T-0NN <title>

**Author:** <name>  **Date:** <YYYY-MM-DD>  **Ticket:** `tickets/T-0NN.md`  **Status:** <Draft|Agreed>

## 1. Scope
- In scope: <ACs, endpoints, screens>
- Out of scope: <and why>

## 2. Test cases
| ID | AC | Type | Given | When | Then | Level | Test name / steps |
|---|---|---|---|---|---|---|---|
| TC-1 | AC-1 | happy | <state> | <action> | <result> | auto | `tests/test_<area>.py::test_<behaviour>` |
| TC-2 | AC-1 | error | | | 409 `<detail>` | auto | |
| TC-3 | AC-2 | edge | | | | manual | <UI steps> |

Type: happy, error, edge, regression. Level: auto (pytest), api (curl on `/docs`), manual (UI).

## 3. Edge cases checked
- [ ] DST switch day  - [ ] lunch 12:00–13:00  - [ ] 30 vs 60 min  - [ ] exactly 24 h before start
- [ ] weekend  - [ ] 60-day limit  - [ ] back-to-back  - [ ] insured vs uninsured / odd-cent rounding
- [ ] after restart (SQLite)  - [ ] UI and API give the same result
Mark each item N/A with a reason when it does not apply.

## 4. Test data
<fake doctors/patients from `data/seed.json`, frozen time, env values>

## 5. Exit criteria
All auto cases green, no open S1/S2 defect, manual cases run or explicitly waived by <who>.
