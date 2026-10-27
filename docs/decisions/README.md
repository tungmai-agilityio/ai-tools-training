# Decision records

One flat folder. Numbers are per type, four digits, never reused or renumbered.

| Type | File | Records | Template |
|---|---|---|---|
| ADR | `ADR-0001-<slug>.md` | Architecture: storage, dependency, time handling, auth | `docs/templates/adr.md` |
| DDR | `DDR-0001-<slug>.md` | Design: UX and product-behaviour choices | `docs/templates/ddr.md` |

A superseded record stays; set its `Status: Superseded by ...`. A ticket or spec links records with
`**Decisions:** ADR-0001, DDR-0002`; `tickets.py` checks that each file exists.

## Index
| Record | Decision | Status |
|---|---|---|
| [ADR-0001](ADR-0001-keep-single-page-frontend.md) | Keep the same-origin vanilla frontend; React (Vite) when we outgrow it | Accepted |
| [ADR-0004](ADR-0004-python-playwright-for-ui-tests-and-screenshots.md) | Python Playwright runs UI tests and captures screenshots, in CI on every PR | Accepted |
