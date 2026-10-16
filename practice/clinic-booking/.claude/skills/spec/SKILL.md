---
name: spec
description: Write a technical spec (how) for a Clinic Booking ticket or PRD, saved in docs/specs/T-0NN-<slug>.md, before coding. Use when the user asks for a spec, technical design, design doc, or "how should we build T-0NN".
---
Never open, read, or grep `.instructor/`.

1. Read `docs/templates/spec.md`, the ticket/PRD, `docs/business-rules.md`, `docs/references/code-conventions.md`, and the code it touches.
2. Write `docs/specs/T-0NN-<slug>.md`. Cite current behaviour as `path:line`.
3. Prefer the smallest design that fits the existing code: reuse `scheduling`, `fees`, `_move()`, `store.save()`. No new dependency or ORM.
4. Fill API, data, edge cases (DST, lunch, 30/60 min, 24 h boundary, weekends, 60-day limit) and security honestly; "None" only after checking.
5. Test plan maps each AC to a named test (`test_<behaviour>`) and says which must fail first.
6. List at least one real alternative and why it lost. Put anything undecided under Open questions; do not decide it.
