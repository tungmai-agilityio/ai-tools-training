---
name: sync-tickets
description: Refresh the Tracking section of Markdown tickets and the sprint ticket tables from their GitHub issues (state, closed/reopened). Use for "sync tickets", "sync sprint S-001" or "what is the status of the sprint".
---
Reference: `docs/references/ticket-sync.md`. The script is `python3 scripts/tickets.py`. It only reads GitHub and only writes `## Tracking` and the generated sprint table; requirements, scope, ACs and plans are never touched.

1. **Select** tickets: ids, `--sprint S-001` or `--all`.
2. **Preview (dry run):** `python3 scripts/tickets.py sync <selector>`. With no `GH_TOKEN`, fetch each mapped issue with the GitHub MCP `issue_read`/`list_issues` (state all), save as JSON and add `--issues-json FILE`.
3. **Read the table:** `unchanged`, `closed`, `reopened`, `update`, `unmapped` (run `/push-tickets`), `missing` (issue deleted or transferred; ask the user), `mismatch` (issue does not carry this ticket's marker; ask the user), `error`. Title or label drift is reported only; GitHub is never copied into requirements.
4. **Apply:** the dry run changes nothing. Run the same command with `--apply` to write the Markdown (local only, no GitHub write, no approval needed beyond the user asking for a sync).
5. **Report** a short sprint board: open and closed counts, tickets without an issue, drift and errors. Offer a commit `docs: sync sprint S-001 ticket status`.
