---
name: jira-tickets
description: Optionally mirror Ready Markdown tickets into Jira through the Atlassian MCP and sync Jira status back into Tracking. Use for "push T-018 to Jira" or "sync Jira status".
---
Reference: `docs/references/ticket-sync.md` (Jira section). Jira is an optional execution layer next to GitHub Issues; the Markdown stays the source of truth and `scripts/tickets.py` is not changed. **Creating a Jira issue is an external write: ask first.** Never edit, transition or delete an existing Jira issue.

**Setup (read-only, once per session).** `getAccessibleAtlassianResources` for the `cloudId`; `listJiraProjects` and `listJiraProjectIssueTypesMetadata` to confirm the project key and that `Task`, `Feature` and `Bug` exist. Ask which project if there is more than one. Never hard-code a project key; always use the key stored in Tracking.

**Push**
1. `python3 scripts/tickets.py check <selector>`; stop on a `FAIL`. Only `Push: Ready` tickets, unless the user names a Draft ticket explicitly.
2. **Dedupe.** Skip a ticket whose Tracking already has `**Jira:**`. Otherwise search with `searchJiraIssuesUsingJql`: `project = <KEY> AND description ~ "ticket-id: T-018"`. One hit: adopt it (record its key). Two hits: stop and ask.
3. **Preview (dry run).** Take `python3 scripts/tickets.py show T-018` and show per ticket: project, type (Feature -> Feature, Chore -> Task, Bug -> Bug), summary (`title`), labels (`show` labels with `: ` replaced by `-`, e.g. `priority-low`; Jira labels cannot contain spaces), and description (`body`, ending with `ticket-id: T-018`). Priority is not a field on this project's create screen, so it travels as the label only.
4. **Go-ahead gate.** Wait for approval of exactly those rows.
5. **Create** with `createJiraIssue` (`issueType`, `summary`, `description`, `additional_fields.labels`), read it back with `getJiraIssue`, then add the Tracking line.

**Tracking line** (next to `**Issue:**` when both trackers are used; written once by this skill):
```
- **Jira:** [CLB-2](https://<site>.atlassian.net/browse/CLB-2)
```
Only a `https://<site>.atlassian.net/browse/<KEY>-<n>` URL is ever written.

**Sync (read-only on Jira).** For each ticket with a `**Jira:**` line, `getJiraIssue` and map the status category: `new` -> open, `indeterminate` -> in progress, `done` -> closed. Update only `**State:**` and `**Synced:**`. Report drift in title or labels; never copy Jira text into the Markdown. If the key no longer resolves, report `missing` and ask. A renamed project changes the key, so re-read the URL from Jira and ask before rewriting the Tracking line.

**Report** created, adopted, skipped and failed per ticket. A failed ticket is safe to re-run because of the `ticket-id` marker.
