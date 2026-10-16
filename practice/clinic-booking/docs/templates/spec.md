# Spec: <Feature name> (<T-0NN>)

**Author:** <name>  **Status:** <Draft|In review|Approved>  **PRD:** <link>  **Last updated:** <YYYY-MM-DD>

> A Spec says **how**. It must be reviewable before any code is written.

## 1. Context
<One paragraph: the problem from the PRD/ticket and the current behaviour, with `path:line` refs.>

## 2. Proposed design
<The change in prose, then per file:>
- **`app/<file>.py`:** <functions added/changed, signatures>
- **`app/static/index.html`:** <UI change, if any>

## 3. API changes
| Method | Path | Request | Response | Errors |
|---|---|---|---|---|
| POST | `/appointments/{id}/...` | `{...}` | `200 Appointment` | `404`, `409 DomainError`, `422` |

## 4. Data model / persistence
<Model fields added/changed, SQLite impact, backward compatibility of stored JSON.>

## 5. Business rules applied
<Quote the lines of `docs/business-rules.md` this implements. Money in cents, times in UTC, `_move()` for status.>

## 6. Alternatives considered
| Option | Pros | Cons | Why not |
|---|---|---|---|

## 7. Edge cases
- <DST, lunch break, 30/60 min, exactly 24 h, weekend, 60-day limit, concurrent booking, ...>

## 8. Security and privacy
<Auth (`require_admin`?), input validation, data exposed. "None" is an answer only if you checked.>

## 9. Test plan
| Test | File | Covers |
|---|---|---|
| `test_<behaviour>` | `tests/test_<area>.py` | AC-1 |

## 10. Rollout
<Migration of existing `data/clinic.db`, config added to `.env.example`, docs to update.>

## 11. Open questions
1. <question> — <owner>
