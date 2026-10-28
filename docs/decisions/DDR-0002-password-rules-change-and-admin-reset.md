# DDR-0002: Passwords are 12+ characters; users change their own, admins reset with a one-time temporary password

> Claude-assisted draft for maintainer edit. Decisions confirmed by the maintainers on 2026-10-27.

**Status:** Accepted  **Date:** 2026-10-27  **Deciders:** Maintainers  **Ticket:** T-020, T-022, T-023

## Context
Accounts are created by admins, and there is no email service. Staff share workstations, so rules that are too strict get written on sticky notes. Admins should not know anyone's real password.

## Decision
A password has at least 12 characters and no other composition rules. Signed-in users change their own password by entering the current one, the new one and a confirmation; the new one must differ from the current one, and their other sessions end. An admin resets a user's password from the Users screen: a dialog shows a generated temporary password once, with a Copy button. The user must set a new password at next sign-in and can do nothing else until then. The first administrator, seeded from deployment settings, goes through the same forced change at first sign-in. There is no email reset link.

## Options considered
| Option | Pros | Cons |
|---|---|---|
| **12+ characters, no other rules; self change + admin reset** (chosen) | Easy to remember as a passphrase; no mail service; admins never learn the final password. | The temporary password is visible to the admin and whoever they pass it to. |
| 8+ with upper, lower and digit | Familiar. | Shorter, predictable patterns. |
| 12+ and a common-password list | Blocks the worst choices. | A list to maintain. |
| Admin reset only | Smallest. | Users cannot fix their own password. |
| Email reset link | Self-service reset. | Needs a mail service and an email field; much bigger. |

## Consequences
- Good: simple rules, no new infrastructure, no shared knowledge of final passwords.
- Bad / ceiling: no self-service recovery for a forgotten password; an admin must reset it. Revisit when email is available or accounts exceed a handful.
- Follow-up: T-023 (change, reset, forced change), T-022 (change form, reset dialog, forced-change screen); rules recorded in `docs/business-rules.md`.
