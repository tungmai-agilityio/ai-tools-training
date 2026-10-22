---
name: db-migration
description: Change the stored Appointment shape in Clinic Booking without breaking existing rows in data/clinic.db — classify the change, pick the lightest safe path (default, before-validator, or one-off script), prove old rows still load with a test. Use when the user says "add a field to Appointment", "rename a field", "change a status", "migrate the db", "old appointments fail to load", or when a ticket touches app/models.py Appointment or app/store.py.
---
References: `docs/references/code-conventions.md`, `testing-conventions.md`, `tickets/T-012.md`.

**How storage works.** One table `appointments(id, data)`; `data` is `Appointment.model_dump_json()`. On startup `Store.__init__` runs `Appointment.model_validate_json` on every row, so **a row that no longer validates crashes the app at boot**. There are no SQL columns to alter. Doctors and patients live in `data/seed.json` and are not migrated.

1. **Classify** the change to `Appointment` (and `Status`):

   | Change | Old rows | Path |
   |---|---|---|
   | New field with a default | load | **A** — nothing else to do |
   | Field removed | load (pydantic ignores extras; the value stays in the blob until the next save) | **A** |
   | New `Status` value | load | **A** — also check `TRANSITIONS` in `routes.py` |
   | New required field, rename, type change, `Status` value removed or renamed, units change (e.g. dollars → cents) | **crash** | **B**, or **C** if B can't express it |
   | Need to query or index by a field in SQL | — | Not a migration. Stop and run the **planner** subagent, then write an ADR. No ORM, no new dependency. |

2. **Pick the lightest path that holds.**
   - **A. Default.** Give the field a default that is true for old appointments. If no default is honest (for example, the right value depends on the business rules), that's an OPEN QUESTION: ask, don't invent one.
   - **B. Before-validator.** Add a `@model_validator(mode="before")` on `Appointment` that rewrites the old shape (`if "old" in data: data["new"] = data.pop("old")`). Old rows load and are rewritten in the new shape on their next `store.save()`. Add a `ponytail:` comment naming the old shape and when it can go (after every DB has run C, or after the next release).
   - **C. One-off script** `scripts/migrate_T-0NN_<slug>.py`, using stdlib `sqlite3` and `DB_PATH`. Use it when old data must change all at once (a backfill computed from other fields, for example). The script reads each row, transforms the JSON, validates it with `Appointment.model_validate`, and writes it back in **one transaction**. It must be idempotent (running it twice does nothing the second time) and must print how many rows it changed. It does not import `app.store` (that would load the DB and crash on the very rows being fixed).
   - Money stays integer cents, rounded half up. Datetimes stay timezone-aware UTC. A migration that touches either gets a test for both.

3. **Test (red first).** In `tests/test_migration_<slug>.py`, write an old-shape JSON row into a `tmp_path` SQLite file, then build `Store(db_path=tmp_path / "clinic.db")` and assert the appointment loads with the expected new values. For C, run the script's function on that file instead, assert the result, and assert that a second run changes 0 rows. The test must fail before the model change. Then run full `pytest`. Don't edit existing tests to fit the new shape unless the ticket changes that behaviour.

4. **Try it on real data.** `cp data/clinic.db data/clinic.db.bak`, run the script (C) or start the app (A/B) against `data/clinic.db`, open `/` and check that the old appointments are listed. If something breaks, `mv data/clinic.db.bak data/clinic.db`. Never commit `data/*.db`.

5. **Hand off.** Fill in the ticket's approach with the path you chose (A/B/C) and why. For C, add a `## Deploy note` section to the ticket ("back up `data/clinic.db`, run `python scripts/migrate_T-0NN_<slug>.py` before starting the new version"); `/release` copies it into the release notes. Then continue with `/implement` or `/fix`.
