# Testing conventions

## Rules
- `pytest` must be green before any commit or MR.
- Every bug fix ships a test that **fails before the fix and passes after it**. Run it on the old code to prove it.
- Never weaken, skip or delete an existing test to get green. If a test is wrong, say so in the MR.
- Name tests after the behaviour, not the function: `test_insured_gets_20_percent_off`, not `test_fees_2`.
- One behaviour per test. Arrange, act, assert, with a blank line between.

## Fixtures and helpers
- `DB_PATH` is `:memory:` in tests (set in `tests/conftest.py`).
- The `client` fixture gives a `TestClient` with a reset store.
- `tests/helpers.book(...)` creates an appointment through the API. Use it instead of hand-built JSON.
- Time is frozen at **Tue 2026-10-13 10:00 New York time**. Move it with `now["value"] = ...`.

## Where tests go
| Area | File |
|---|---|
| Booking, lifecycle, reschedule | `tests/test_booking.py` |
| Fees, rounding | `tests/test_fees.py` |
| Slots, hours, timezones | `tests/test_scheduling.py` |
| SQLite persistence | `tests/test_persistence.py` |
| HTML served, frontend wiring | `tests/test_frontend.py` |
| Browser smoke (optional, Playwright) | `tests/test_ui_browser.py` |

## Edge cases to always consider
DST switch days, the 12:00–13:00 lunch break, 30 vs 60 minute slots, exactly-24h cancellation, weekends,
the 60-day booking limit, back-to-back appointments, insured vs uninsured, odd cents when rounding.

## Commands
```bash
pytest                                   # full suite
pytest tests/test_fees.py::test_name     # one test
pytest -x -q                             # stop at first failure
```
