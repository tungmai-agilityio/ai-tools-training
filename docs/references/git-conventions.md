# Git conventions

GitHub flow: day-to-day work goes to `develop`, releases go to `main` (see Releases). Everything reaches either through a pull request (PR). Work is tracked as GitHub issues; `#N` is the issue number.

## Branches
| Kind | Name | Example |
|---|---|---|
| Feature issue | `feat/<N>-<kebab-slug>` | `feat/23-revenue-export` |
| Bug issue | `fix/<N>-<kebab-slug>` | `fix/31-cancel-fee-rounding` |
| Chore, with or without an issue (tooling, config) | `chore/<N>-<kebab-slug>` or `chore/<kebab-slug>` | `chore/ignore-worktrees` |
| Docs only | `docs/<kebab-slug>` | `docs/conventions` |

- Branch from an up-to-date `develop`. One issue = one branch = one PR.
- Name branches only from the table above. Never use tool-generated names such as `claude/*`; if a tool pre-created one, rename it before the first push.
- Never commit straight to `develop`. Never force-push a branch someone else is reviewing.

## Commits
Conventional Commits, one line, imperative, lower case, no period, issue number in brackets at the end:

```
<type>: <what changed> (#N)
```

| Type | Use for |
|---|---|
| `feat` | new behaviour a user can see |
| `fix` | a bug fix (comes with a test that failed first) |
| `test` | tests only |
| `refactor` | no behaviour change |
| `docs` | docs, templates |
| `chore` | tooling, config, dependencies, housekeeping |

- No issue (a `chore/` or `docs/` branch): leave the suffix off, e.g. `chore: ignore .claude/worktrees/`.
- Jira key (optional): if the ticket has a `Jira` line in its Tracking section, you may add the key inside the brackets, e.g. `fix: charge 50% for cancels inside 24 hours (#31, CLB-12)`. Never required; leave it off when there is no Jira ticket.
- Good: `fix: charge 50% for cancels inside 24 hours (#31)`
- Bad: `Fixed bug`, `fix: #31`, `WIP`, `fix: stuff and also refactor fees`
- Aim for **one commit per issue**. Squash fixups before asking for review (`git commit --fixup <sha>` + `git rebase -i --autosquash develop`; agents: `GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash develop`).
- Add a body (blank line, then wrapped text) only when the *why* is not obvious from the issue.
- Older commits and files say `T-0NN`: those refer to the archived tickets in `plans/archive/`.

## Issues
- Templates: `.github/ISSUE_TEMPLATE/` (feature, bug, chore). Type labels: `enhancement`, `bug`, `chore`.
- An open issue is open work. Add the `in-progress` label when its branch starts, and `blocked` while it waits on a decision (remove it once answered).
- Don't add `todo`, `in-review` or `done` labels: open, a linked PR, and closed already say that.
- The PR body says `Closes #N`, so GitHub closes the issue when the PR merges. Never reopen a closed issue; open a new one with `Related: #N`.

## Pull requests
- Title = the commit subject. Description = `.github/pull_request_template.md` (repo root), filled in, with `Closes #N`. If the ticket has a Jira key, add a `Jira: CLB-12` line (see the comment in the template); otherwise leave it out.
- Before opening: `pytest` is green and the diff is only the issue.
- At least one approval. The author resolves every thread or answers it.
- Merge with a merge commit (`Merge pull request #M from <user>/fix/31-...`) and delete the source branch.

## Conflicts
- Rebase your branch on `develop` (`git fetch && git rebase origin/develop`), resolve, re-run `pytest`, then push with `--force-with-lease`.
- When both sides changed behaviour, keep both and ask the other author. Never drop someone's test to make it merge.

## Releases
- `main` holds released code only. It moves through one PR from `develop` (`release: vX.Y.Z`), merged **without** deleting `develop`.
- Release notes live in `docs/releases/vX.Y.Z.md`, merged into `develop` first on a `docs/release-vX.Y.Z` branch.
- After the merge, tag `main` with an annotated `vX.Y.Z` tag. First release is `v0.1.0`; `feat` bumps minor, otherwise patch. Steps: `/release`.

## Remote
`origin` (GitHub) is the only remote: branches, issues, PRs, review and releases.

## Never commit
`.env`, `data/*.db`, `.venv/`, `__pycache__/`, real tokens, real patient data.
