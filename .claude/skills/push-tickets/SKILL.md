---
name: push-tickets
description: Create GitHub issues from Ready Markdown tickets in plans/tickets/ without duplicates, and record the issue number and URL back in the ticket. Use for "push tickets", "push sprint S-001" or "create issues for T-018".
---
Reference: `docs/references/ticket-sync.md`. The script is `python3 scripts/tickets.py`. **Creating issues is a GitHub write: ask first.** Never edit or reopen an existing issue.

1. **Select** tickets: ids (`T-018 T-019`), `--sprint S-001` or `--all`.
2. **Validate:** `python3 scripts/tickets.py check <selector>`. Fix the Markdown (never invent values) and stop on a `FAIL`.
3. **Preview (dry run):** `python3 scripts/tickets.py push <selector>`. With no `GH_TOKEN`, fetch the repo's issues with the GitHub MCP `list_issues` (state all), save them as JSON, and add `--issues-json FILE` (the author cannot be verified there: an issue that already carries a ticket marker is only adopted with `--adopt-author <login>`, and only after the user confirms that login). Show the table: `create`, `adopt`, `skip`, `blocked` (a gate failed), `error`.
4. **Go-ahead gate.** Show the preview and wait for the user's approval of exactly those rows. No approval, no GitHub write.
5. **Apply:**
   - With `GH_TOKEN`: `python3 scripts/tickets.py push <selector> --apply`.
   - Without it: for each `create` row run `python3 scripts/tickets.py show T-NNN`, create the issue with the MCP `issue_write` tool (title, body and labels exactly as shown), then `python3 scripts/tickets.py record T-NNN --issue N --url URL`. For `adopt` rows only run `record`.
6. **Report** created/adopted/failed per ticket and the next step. A failed ticket is safe to re-run: the hidden `ticket-id` marker makes the retry adopt a half-created issue instead of duplicating it. Commit the Markdown change as `docs: record issue numbers for S-001 tickets` (no issue number needed).
