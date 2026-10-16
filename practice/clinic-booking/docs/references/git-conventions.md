# Git conventions

GitLab flow with one long-lived branch, `develop`. Everything reaches it through a merge request (MR).

## Branches
| Kind | Name | Example |
|---|---|---|
| Feature ticket | `feat/T-0NN` | `feat/T-012` |
| Bug ticket | `fix/T-0NN` | `fix/T-004` |
| No ticket (tooling, docs, config) | `chore/<kebab-slug>` | `chore/ignore-worktrees` |
| Docs only | `docs/<kebab-slug>` | `docs/conventions` |

- Branch from an up-to-date `develop`. One ticket = one branch = one MR.
- Never commit straight to `develop`. Never force-push a branch someone else is reviewing.

## Commits
Conventional Commits, one line, imperative, lower case, no period, ticket id in brackets at the end:

```
<type>: <what changed> (T-0NN)
```

| Type | Use for |
|---|---|
| `feat` | new behaviour a user can see |
| `fix` | a bug fix (comes with a test that failed first) |
| `test` | tests only |
| `refactor` | no behaviour change |
| `docs` | docs, tickets, templates |
| `chore` | tooling, config, dependencies, housekeeping |

- No ticket (a `chore/` or `docs/` branch): leave the suffix off, e.g. `chore: ignore .claude/worktrees/`.
- Good: `fix: charge 50% for cancels inside 24 hours (T-003)`
- Bad: `Fixed bug`, `fix: T-003`, `WIP`, `fix: stuff and also refactor fees`
- Aim for **one commit per ticket**. Squash fixups before asking for review (`git commit --fixup <sha>` + `git rebase -i --autosquash develop`; agents: `GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash develop`).
- Add a body (blank line, then wrapped text) only when the *why* is not obvious from the ticket.

## Merge requests
- Title = the commit subject. Description = `docs/templates/merge-request.md`, filled in.
- Before opening: `pytest` is green, the diff is only the ticket, the ticket's status is `In Review`.
- At least one approval. The author resolves every thread or answers it.
- Merge with a merge commit (`Merge branch 'fix/T-0NN' into 'develop'`), delete the source branch, set the ticket to `Done`.

## Conflicts
- Rebase your branch on `develop` (`git fetch && git rebase origin/develop`), resolve, re-run `pytest`, then push with `--force-with-lease`.
- When both sides changed behaviour, keep both and ask the other author. Never drop someone's test to make it merge.

## Never commit
`.env`, `data/*.db`, `.venv/`, `__pycache__/`, real tokens, real patient data, anything under `.instructor/`.
