# Plans

Markdown here is the source of truth for planned work. GitHub Issues are the execution layer.
Workflow, field ownership and examples: `docs/references/ticket-sync.md`.

| Folder | Holds |
|---|---|
| `tickets/T-NNN.md` | One file per GitHub issue. IDs continue from T-018 (T-001 to T-017 live in the read-only `plans/archive/`). |
| `sprints/S-NNN.md` | Sprint goal, dates, scope, capacity, risks and a generated ticket table. |
| `features/<slug>/` | `intent.md`, `spec.md`, `plan.md` for a new feature. Optional; bugs and chores skip it. |
| `archive/T-NNN.md` | Read-only history, T-001 to T-017. Don't edit or add files. |

Decision records are in `docs/decisions/` (ADR and DDR).
