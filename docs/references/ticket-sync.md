# Markdown-first tickets

Markdown under `plans/` is the source of truth for requirements, scope, acceptance criteria and plans.
GitHub Issues are the execution layer: status, discussion, PRs. Two skills connect them, both backed by
`scripts/tickets.py` (stdlib only).

```
plans/tickets/T-018.md     one file per issue (IDs continue after the archived T-001..T-017)
plans/sprints/S-001.md     sprint plan + generated ticket table
plans/features/<slug>/     intent.md, spec.md, plan.md (optional, new features)
docs/decisions/            ADR-NNNN-*.md, DDR-NNNN-*.md
```

## Ticket format
```markdown
# Revenue report endpoint

**Sprint:** S-001  **Feature:** revenue-report  **Type:** Feature  **Priority:** Medium  **Estimate:** S  **Push:** Ready
**Severity:** S3 workaround exists  **Areas:** api  **Decisions:** ADR-0001

## Summary / Acceptance criteria / Test cases   (becomes the issue body)

## Tracking
<!-- tracking (written by push-tickets / sync-tickets, do not edit) -->
- **Issue:** [#34](https://github.com/OWNER/REPO/issues/34)
- **State:** open
- **Synced:** 2026-10-27T04:00:00Z
```
Required: `Type` (Bug|Feature|Chore), `Priority` (Low|Medium|High), `Push` (Draft|Ready). A Bug also needs
`Severity` (S1-S4). Optional: `Sprint`, `Feature`, `Estimate` (XS|S|M|L|TBD), `Areas`, `Decisions`.
Unknown fields or bad values fail `check`. The file name is the ID.

## Mapping to GitHub
| Markdown | Issue |
|---|---|
| ID + `# title` | title `T-018: <title>` |
| everything between the title and `## Tracking` | body, plus hidden marker `<!-- ticket-id: T-018 -->` and links to `Decisions` |
| Type | label `bug` / `enhancement` / `chore` |
| Priority, Severity, Areas | labels `priority: x`, `severity: Sx`, `area: x` (must already exist; never auto-created) |
| Sprint's `**Milestone:**` | milestone, if it exists (never auto-created) |

## Field ownership
| Owner | Fields |
|---|---|
| You (Markdown) | all of `plans/features/`, sprint text, ticket title, header fields and body |
| `push-tickets`, once | Tracking `Issue` (number + URL), after GitHub confirms |
| `sync-tickets` | Tracking `State`, `Reason`, `Synced` (time of the last change), the generated table in each sprint file |
GitHub title, label or body edits are reported as drift and never copied into Markdown.

## Gates
`Push: Ready` is a human decision. A ticket with `Feature:` is blocked until
`plans/features/<slug>/spec.md` has `**Status:** Approved` and its `plan.md` is not Draft. A ticket with
`Sprint:` needs its sprint file.

## Safety and idempotency
- Every command is a **dry run** until `--apply`. `push --apply` is the only GitHub write (creates issues, never edits, closes or reopens). Ask the user first.
- Dedupe: Tracking `Issue` set -> skip. Otherwise the repo is searched for the `ticket-id` marker; one hit is **adopted** (recovers a crash between create and write-back), two hits or one issue number in two files is an error and nothing is written.
- Per-ticket processing: an API error is logged, the run continues, exit code 1. Markdown changes only after GitHub confirms. Re-running is safe and a no-op when nothing changed.
- `sync` handles closed, reopened, `missing` (deleted or transferred) and `mismatch` (issue lacks this ticket's marker) without changing the ticket.
- No `GH_TOKEN`: fetch issues with the GitHub MCP, pass `--issues-json FILE`, and for creation use `show T-018` + MCP `issue_write` + `record T-018 --issue N --url URL`.

## Usage
```bash
python3 scripts/tickets.py check --sprint S-001
python3 scripts/tickets.py push --sprint S-001            # preview
python3 scripts/tickets.py push --sprint S-001 --apply    # after approval
python3 scripts/tickets.py sync --sprint S-001 --apply    # refresh Markdown
python3 scripts/tickets.py push T-018 T-019               # selected tickets
```
In Claude Code: `/push-tickets sprint S-001`, `/sync-tickets sprint S-001`. `/release --sprint S-001` adds a
sprint summary (done vs carried over) from a read-only sync.
