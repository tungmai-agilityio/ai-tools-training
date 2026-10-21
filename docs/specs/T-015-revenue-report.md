# Spec: Revenue report (T-015)

**Author:** Tung Mai  **Status:** Draft  **PRD:** `tickets/T-015.md`  **Last updated:** 2026-10-21

> A Spec says **how**. It must be reviewable before any code is written.

## 1. Context
The clinic manager cannot see what the clinic earned. Each `Appointment` carries `fee_cents` and
`cancellation_fee_cents` (`app/models.py:38-39`), but the only place they show up is the paginated
`GET /appointments` (`app/routes.py:244`). This adds a read-only, admin-only report that sums money over a date
range, split into consultation and penalty revenue, per doctor and per day. The stored `Appointment` shape does not
change and no dependency is added.

## 2. Proposed design
The handler scans `store.appointments` in memory. Each appointment counts on the clinic-local date of its
scheduled start (`scheduling.to_local(a.start).date()`), and the range includes both ends.
`completed` adds `fee_cents` to consultation. `no_show` and `cancelled` add `cancellation_fee_cents` to penalty.
All other statuses are ignored. An appointment that adds 0 creates no `by_day` row. `by_doctor` lists every seeded
doctor, including those with 0. The grand totals are the sums over `by_doctor`. `total_cents` is computed from the
other two fields, so the parts always add up.

- **`app/models.py`:** add `RevenueTotals(consultation_cents=0, penalty_cents=0, computed total_cents)`,
  `DoctorRevenue(RevenueTotals) + doctor_id, doctor_name`, `DayRevenue(RevenueTotals) + date`,
  `RevenueReport(from_date, to_date, totals, by_doctor, by_day)`.
- **`app/routes.py`:** add a new "Reports" section after `delete_appointment`:
  `revenue_report(from_date: date = Query(alias="from"), to_date: date = Query(alias="to")) -> RevenueReport`,
  registered with `@router.get("/reports/revenue", dependencies=[Depends(require_admin)])` so the 403 comes
  before query validation. Reuses `require_admin` (`:69`), `scheduling.to_local` (`app/scheduling.py:15`), and the
  alias and 366-day-cap patterns from `:108` and `:181`.
- **`app/static/index.html`:** no change (a UI is a separate ticket).

## 3. API changes
| Method | Path | Request | Response | Errors |
|---|---|---|---|---|
| GET | `/reports/revenue?from=YYYY-MM-DD&to=YYYY-MM-DD` | header `X-Admin-Token` | `200 RevenueReport` | `403` bad or missing token; `422` missing or malformed date, `from` > `to`, range > 366 days |

Example `200`:
```json
{"from_date": "2026-10-14", "to_date": "2026-10-15",
 "totals": {"consultation_cents": 39997, "penalty_cents": 0, "total_cents": 39997},
 "by_doctor": [{"doctor_id": 1, "doctor_name": "Dr. James Carter", "consultation_cents": 27000, "penalty_cents": 0, "total_cents": 27000},
               {"doctor_id": 2, "doctor_name": "Dr. Emily Brooks", "consultation_cents": 12997, "penalty_cents": 0, "total_cents": 12997},
               {"doctor_id": 3, "doctor_name": "Dr. Sarah Mitchell", "consultation_cents": 0, "penalty_cents": 0, "total_cents": 0}],
 "by_day": [{"date": "2026-10-14", "consultation_cents": 12000, "penalty_cents": 0, "total_cents": 12000},
            {"date": "2026-10-15", "consultation_cents": 27997, "penalty_cents": 0, "total_cents": 27997}]}
```

## 4. Data model / persistence
These are response models only. `Appointment`, the SQLite tables and the stored JSON do not change. The endpoint
writes nothing.

## 5. Business rules applied
- "Fees (all amounts in cents …)": totals are sums of stored integer cents, so no rounding happens.
- Late-cancel (50%) and no-show (100%) amounts are reported as penalty, using `cancellation_fee_cents` as stored.
- "Insured patients get 20% off": the stored, discounted `fee_cents` is the amount counted.
- Admin only: the endpoint uses `require_admin`.
- New rules for a "Revenue report" section of `docs/business-rules.md` (dev defaults, pending clinic manager
  confirmation): consultation revenue is the fee of completed visits; penalty revenue is no-show and late-cancel
  fees; each visit counts on its scheduled start day in clinic time; amounts are gross, with no refunds; admin only.
- No status changes, so `_move()` is not involved.

## 6. Alternatives considered
| Option | Pros | Cons | Why not |
|---|---|---|---|
| `json_extract` SQL aggregate over `appointments` | Pushes the work into SQLite | Clinic-tz bucketing in SQL, a second read path besides `store.appointments` | The in-memory scan is the existing read pattern and is fast at clinic scale |
| Inline `require_admin(x_admin_token)` like the other admin routes | Matches the other admin routes | Callers without a token get 422 on bad dates | `Depends` is the same function and checks auth first |

## 7. Edge cases
- An evening visit whose UTC date is the next day (only possible in data not created through booking) counts on
  its clinic day (AC-5).
- A rescheduled visit counts on its new day with its new fee (AC-6).
- A free cancellation adds 0 and creates no day row.
- An empty range still lists every doctor with 0.
- A range of exactly 366 days inclusive is allowed; 367 days is rejected.
- `from == to` (a single day) is valid.
- Odd-cent fees (Dr. Brooks, 12997) add up exactly.
- DST, lunch, weekends and the 60-day limit do not apply (see the ticket's test plan).

## 8. Security and privacy
Admin only, fail closed: `require_admin` (`app/routes.py:69`) uses a constant-time comparison and refuses every
request when `ADMIN_TOKEN` is empty. The response contains only fake doctor names and aggregate cents, with no
patient data. Input is two typed `date` query parameters, and the 366-day cap bounds the range.

## 9. Test plan
See `tickets/T-015.md` §7. All tests live in `tests/test_reports.py`.

## 10. Rollout
No migration: an existing `data/clinic.db` is read as it is. No new config. Docs to update: the "Revenue report"
section in `docs/business-rules.md`; one line in `README.md`; this spec.

## 11. Open questions
1. Are no-show and late-cancel fees revenue, or only amounts owed until paid? Reported separately for now. — clinic manager
2. Is the scheduled day acceptable for accounting, including a late-cancel fee that arose on the cancellation day? — accounting
3. Deleting a completed appointment removes it from past totals. Accept this, or block deleting completed visits? — clinic manager
