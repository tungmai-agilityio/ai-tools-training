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
| [ADR-0002](ADR-0002-signed-session-cookie-with-session-version.md) | Authenticate with a signed, stateless session cookie and a per-user session version | Proposed |
| [ADR-0003](ADR-0003-two-roles-deny-by-default-and-retire-admin-token.md) | Two roles, deny by default, and retire the shared admin token | Proposed |
| [DDR-0001](DDR-0001-lock-account-after-five-failed-logins.md) | Lock a username for 15 minutes after 5 failed logins | Proposed |
| [DDR-0002](DDR-0002-password-rules-change-and-admin-reset.md) | Passwords are 12+ characters; users change their own, admins reset with a one-time temporary password | Proposed |
| [DDR-0003](DDR-0003-signed-in-experience-by-role.md) | Show the signed-in user and hide what their role cannot do | Proposed |
