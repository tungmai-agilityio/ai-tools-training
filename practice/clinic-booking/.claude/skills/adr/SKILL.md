---
name: adr
description: Record a Clinic Booking architecture or technical decision as an ADR in docs/adr/ — context, decision, options, consequences. Use when the user says "write an ADR", "record this decision", "why did we choose X", or when a spec, ticket or /rules change makes a choice future devs will question (storage, dependencies, timezone handling, auth).
---
Never open, read, or grep `.instructor/`.

1. **Number.** Take the highest `docs/adr/NNNN-*.md` + 1, starting at `0001`. The filename is `docs/adr/NNNN-<kebab-slug>.md`.
2. **Gather.** Read the ticket, spec or MR that made the decision, and the code it shaped (`path:line`). Decisions already made in this repo can be written up after the fact with status `Accepted` and their original ticket. Examples: SQLite JSON rows with no ORM (T-012), integer cents, UTC storage with clinic-time logic, `DomainError` over `HTTPException`.
3. **Write** from `docs/templates/adr.md`. List at least two real options. Consequences must name the ceiling and the signal that should make us revisit it, matching any `ponytail:` comment in the code.
4. **Never rewrite an accepted ADR.** To change a decision, add a new ADR and set the old one's status to `Superseded by ADR-NNNN`.
5. Link the ADR from the ticket or spec. Commit as `docs: add ADR-NNNN <decision>`.
