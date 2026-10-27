# Decision records

One flat folder. Numbers are per type, four digits, never reused or renumbered.

| Type | File | Records | Template |
|---|---|---|---|
| ADR | `ADR-0001-<slug>.md` | Architecture: storage, dependency, time handling, auth | `docs/templates/adr.md` |
| DDR | `DDR-0001-<slug>.md` | Design: UX and product-behaviour choices | `docs/templates/ddr.md` |

A superseded record stays; set its `Status: Superseded by ...`. A ticket or spec links records with
`**Decisions:** ADR-0001, DDR-0002`; `tickets.py` checks that each file exists.

## Index
None yet.
