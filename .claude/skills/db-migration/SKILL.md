---
name: db-migration
description: Change the stored Appointment shape without breaking existing rows in data/clinic.db — pick the lightest safe path and prove old rows still load. Use when a ticket adds, renames or retypes an Appointment field or Status, or old appointments fail to load.
---
**Why it matters.** Rows are `Appointment.model_dump_json()` blobs in `appointments(id, data)`. `Store.__init__` validates every row at startup, so **a row that no longer validates crashes the app at boot**. Doctors and patients are seed-only.

1. **Classify:**

   | Change | Old rows | Path |
   |---|---|---|
   | New field with an honest default, removed field, new `Status` (check `TRANSITIONS`) | load | **A** |
   | New required field, rename, type or unit change, `Status` removed or renamed | **crash** | **B**, or **C** if B can't express it |
   | Need to query or index by a field | — | Not a migration: stop, run the **planner**, write an ADR. |

2. **Apply the lightest path:**
   - **A. Default** that is true for old rows. If no honest default exists, it's an OPEN QUESTION: ask.
   - **B. Before-validator** on `Appointment` that rewrites the old shape. Add a `ponytail:` comment saying when it can go.
   - **C. One-off script** `scripts/migrate_<N>_<slug>.py` with stdlib `sqlite3`. It validates each row, writes in one transaction, is idempotent and prints the count of changed rows. It must not import `app.store`, which would crash on the very rows being fixed.

3. **Test red first** in `tests/test_migration_<slug>.py`: write an old-shape row to a `tmp_path` DB and assert it loads (for C, assert a second run changes 0 rows). A change that touches money or datetimes also tests that values stay integer cents and UTC-aware. Then run full `pytest`.
4. **Try it on a backup:** copy `data/clinic.db` first and restore it if anything breaks. Never commit `data/*.db`.
5. **Hand off:** record the path and why in the issue. For C, add a `## Deploy note` (back up, run the script before starting) for `/release`. Then `/implement` or `/fix`.
