# DDR-0003: Show the signed-in user and hide what their role cannot do

> Claude-assisted draft for Tung's edit. Decisions confirmed by Tung on 2026-10-27.

**Status:** Accepted  **Date:** 2026-10-27  **Deciders:** Tung  **Ticket:** T-022

## Context
The UI is one page, `app/static/index.html`, with Book, Appointments, Today and Revenue screens. Staff and admins now see different things. The UI draft (Artifact "Clinic Login UI Draft") has five boards: sign-in, staff view, users, revenue, and change/reset password.

## Decision
Without a session the page shows only the sign-in form. After sign-in the sidebar shows the user's name with a role tag on the same row, the session's end time, and a Sign out button. Staff see Book, Appointments and Today. Admins also see Holidays and time off, Revenue and Users. Hidden items are not disabled, they are absent. No screen shows an HTTP status code. When the session ends, the page returns to sign-in. The Revenue screen shows totals, a stacked bar chart by day and a by-doctor table. A user who must change a temporary password sees only the change-password screen.

## Options considered
| Option | Pros | Cons |
|---|---|---|
| **Hide what the role cannot use** (chosen) | Uncluttered; staff are not tempted by controls that fail. | Admin features are less discoverable to staff by design. |
| Show everything, disable for staff | Staff see what exists. | Clutter and "why can't I?" questions. |
| Separate admin page | Clear split. | Second page and navigation; contradicts ADR-0001's single page. |

## Consequences
- Good: simple navigation per role; the server still enforces every rule.
- Bad / ceiling: hiding is cosmetic, so tests must also call admin routes as staff. Revisit if more roles appear.
- Follow-up: T-022 builds these screens; the UI Artifact is the design reference.
