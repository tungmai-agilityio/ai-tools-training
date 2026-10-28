---
name: release-notes
description: Write the client-facing release note for a shipped Clinic Booking release as a private Artifact page, in plain English. Use for "client release note for v0.1.0" or after /release.
disable-model-invocation: true
---
Usage: `/release-notes vX.Y.Z S-NNN`. Source: `docs/releases/vX.Y.Z.md`, the sprint file `plans/sprints/S-NNN.md`, and the Done tickets in it (their description and acceptance criteria give the user-visible wording). Read-only on the repo.

1. Write for the clinic's staff and managers, not developers. Sections, each only if it has content: **What's new**, **Improvements**, **Fixes**, **Before you upgrade** (what the client or their administrator must do, described as an action), **Known limits**.
2. Every line traces to a Done ticket. Never invent a feature, a date or a promise; carry-over appears only as "coming next" when the sprint file says so.
3. Leave out ticket IDs, issue and PR numbers, file paths, env var names and values, secrets, and internal names (skills, hooks, ADRs). Fake data only in any example.
4. Publish with the Artifact tool as a private page (load its design skill first); give the page the version and release date. Never share or post it.
5. Report the page link and what the user should check before sending it to the client.
