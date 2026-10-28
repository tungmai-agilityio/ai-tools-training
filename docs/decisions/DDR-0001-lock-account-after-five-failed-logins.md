# DDR-0001: Lock a username for 15 minutes after 5 failed logins

> Claude-assisted draft for maintainer edit. Decisions confirmed by the maintainers on 2026-10-27.

**Status:** Accepted  **Date:** 2026-10-27  **Deciders:** Maintainers  **Ticket:** T-019, T-020

## Context
Staff sign in with a username and password on shared clinic computers. Without a limit, passwords can be guessed. A permanent lock could leave the only admin locked out. The sign-in screen must not reveal whether a username exists.

## Decision
After 5 consecutive failed attempts a username is locked for 15 minutes, even if the right password is then entered. A successful login resets the count. A locked user sees "Too many failed attempts. Try again in 15 minutes or ask an administrator to unlock the account." Wrong username and wrong password show the same message ("Wrong username or password."). The screen shows no status codes. An admin can unlock an account early from the Users screen, and re-enabling or resetting a user also clears the lock.

## Options considered
| Option | Pros | Cons |
|---|---|---|
| **Lock 15 min after 5 failures** (chosen) | Slows guessing; recovers on its own; admin can unlock. | A person can lock out a colleague's username on purpose for 15 minutes. |
| No lockout, generic error only | Simplest. | Brute force stays open. |
| Lock until an admin unlocks | Strongest. | A locked admin has no recovery path. |

## Consequences
- Good: guessing is slowed, no one is locked out for good.
- Bad / ceiling: lockout is per username, not per address, so it does not stop one address trying many usernames. Revisit with rate limiting if the app is exposed beyond the clinic network.
- Follow-up: T-019 (counter, lock, reset), T-020 (admin unlock), T-022 (messages); rule recorded in `docs/business-rules.md`.
