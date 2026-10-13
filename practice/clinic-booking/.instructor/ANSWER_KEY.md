# ANSWER KEY (spoilers)

Do not read this before you have attempted the ticket. Use it to grade a finished drill.

| Ticket | Layer | Where | What is wrong | Failing test to write |
|---|---|---|---|---|
| T-001 | Code | `routes.py` `list_appointments` | Slice starts at `offset - 1`, so page 2+ repeats the last row of the previous page and returns page_size+1 items. | Book 12, request `page=2&page_size=5`: expect ids `[6..10]`, no overlap with page 1. |
| T-002 | Code | `scheduling.py` `overlaps` | Only detects a new appointment that starts before an existing one. It misses a new appointment that starts inside an existing one (e.g. 60-min at 09:00, then a 30-min at 09:30). Ticket gives no times or durations; the "long visits" comment is the clue. | Book 09:00 for 60 min, then 09:30 for 30 min with another patient: expect 409. |
| T-003 | Code | `fees.py` `late_cancellation_fee` | `round()` rounds half to even, but the rule is half up. Dr. Brooks's fee 12997 uninsured gives 6498 instead of 6499. | `late_cancellation_fee(12997) == 6499`. |
| T-004 | Code | `routes.py` `todays_appointments` | Compares the clinic-local date of each appointment with the UTC date of now. US Eastern is behind UTC, so from 8 PM to midnight local (7 PM in winter) the UTC date is already tomorrow and the screen shows tomorrow's patients or nothing. | Book on the 13th at 3 PM local, then freeze now at 2026-10-14T01:00Z (9 PM on the 13th local): expect it in `/appointments/today`. |
| T-005 | Code + BA | `routes.py` `cancel` | Only blocks `cancelled`. `completed` and `no_show` can be cancelled and charged. Rule says only `scheduled` may be cancelled. The checked-in case is an open question in `docs/business-rules.md`: the BA must get a decision before coding it. | Complete an appointment, cancel it: expect 409. |
| T-006 | Code (security) | `routes.py` `require_admin` | Fails open: if `ADMIN_TOKEN` is empty (the default, and `.env.example` leaves it blank) the check is skipped. Fix: fail closed, and refuse to start or deny when no token is configured. | With `ADMIN_TOKEN=""`, `DELETE` with no header must be 403. |
| T-007 | Config | `config.py` + `.env.example` | `CLINIC_TIMEZONE` defaults silently to UTC and is missing from `.env.example`, so slots shift by 4 hours (5 in winter). Tests pass because `conftest.py` sets the variable. Not a frontend problem. | Test that startup fails (or uses the documented zone) when the variable is absent; add the variable to `.env.example`. |
| T-008 | Data | `data/seed.json` | Dr. Mitchell's `fee_cents` is 150 (looks like dollars). The calculation is correct. Fix the data (15000 or whatever the clinic confirms), and consider a validation guard. | Assert every seeded doctor has a plausible fee. |
| T-009 | BA / feature | n/a | No spec. Questions to ask: free reschedule or fee? How close to the start time? Same doctor only? Keep the original id? What if the new slot is taken? Who can do it? | Spec first, tests second. |

## Seeing the bugs in the UI

- T-001: Appointments tab, page 2 starts with the last row of page 1 (run `scripts/seed_demo.py` first).
- T-002: Book tab, slots stay offered next to a 60-min booking; book 09:00 for 60 min then 09:30.
- T-004: Today tab, only visible when the UTC date differs from the clinic date (after about 8 PM local). Easiest to reproduce with a frozen clock in a test.
- T-005: The UI only shows Cancel for `scheduled` appointments, so the bug is not reachable from the screen. Reproduce it with `/docs` or curl. Good lesson: a UI guard is not a server rule.
- T-006: Not reachable from the UI (there is no delete button). Use `/docs`.
- T-007: The frontend hardcodes America/New_York on purpose. Start the server without `CLINIC_TIMEZONE` and the slots show 4:00 AM to 12:30 PM. The frontend is not at fault.
- T-008: Book with Dr. Mitchell and the confirmation toast shows $1.50.

## Review-drill checklist (use on your own PRs too)

- Does the diff touch only what the ticket needs (scope creep)?
- Is there a test that fails without the change?
- Money: integer cents, rounding rule stated, no floats.
- Time: stored in UTC, compared in clinic time, no naive datetimes.
- Security: fails closed, no secrets in code, no default-open behaviour.
- Does the PR description stand alone?
