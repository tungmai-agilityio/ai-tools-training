# Plan: Hooks as approval gates + CI/CD triage

**Author:** Claude (draft, for maintainer edit)  **Status:** Implemented (T-029 to T-031 closed). Gates for push, merge, tag, branch delete and data are planned in [approval-gates-rollback](../approval-gates-rollback/plan.md), which reverses the "leave pushes to the classifier" decision.
Approved in plan mode, 2026-10-28. Draft, Claude-assisted, human-edited. No tickets created yet.

## Context
Two Academy lessons (Hooks as approval gates; CI/CD integration and deployment) vs. what the repo already does. The maintainers' answers while grilling: leave pushes to the classifier; no GitHub-write hooks; only add explicit allow for safe project commands; CI scope is read-only triage plus the speed fix.

## 1. Lesson summary
**Hooks as approval gates**
- A PreToolUse hook returns allow / ask / deny as JSON (`hookSpecificOutput.permissionDecision` + reason). Ask reason goes to the human, deny reason to Claude (so it can relay the route to approval). Non-interactive runs turn ask into deny.
- Block messages must say why and how to get approval. Team hooks live in `.claude/settings.json`; non-negotiable ones in managed settings.
- Gate on records the agent cannot write. Measure time waiting at gates (leading) and gate violations reaching prod (lagging).

**CI/CD**
- Claude does judgment steps (triage failures, changelogs, lint fixes) in a sandbox with scoped tokens; start read-only, then write steps that only land as PRs under branch protection.
- Tier autonomy by environment (dev free, staging on approved merge, prod needs a named human via hook); rollback is the most-practiced path.
- Measure share of failures triaged without paging a human, then DORA.

## 2. Mapping to this project
| Gate | Today | Verdict |
|---|---|---|
| Issue creation | `/push-tickets` dry run until `--apply`, CLAUDE.md "ask first" | Prose + skill; keep (Maintainers: no GitHub hook) |
| Ready tickets | `Push: Ready` human field, `tickets.py check` | Already a deterministic gate |
| git push | Hook denies force/protected/`claude/*`; ask comes from classifier | Keep as is (the maintainers' choice) |
| PR labels / merge | Prose in project rules; branch protection + review | Keep prose; branch protection is the real gate |
| Pip / make | Hook denies bad `pip install`; `-r requirements*.txt` only passes via classifier, so it prompted today | **Add explicit allow** |

Current hook is deny-only (exit 2). The lesson's JSON form lets it also return allow with a reason, which removes classifier friction for commands we already trust. Deny reasons should also name the route ("edit requirements.txt only if the ticket says so; ask a maintainer").

Note: all 83 tests in `tests/test_push_hook.py` pass on both this branch and `develop`; the earlier "9 failing" report is not reproducible and is dropped (re-check in CI if it reappears).

## 3. Proposed hooks
| # | Trigger | Behavior | Tests |
|---|---|---|---|
| H1 | PreToolUse(Bash): exactly the project's requirements install (`-r requirements.txt` or `-r requirements-dev.txt`); `make` and `pytest` are already in `permissions.allow` | **allow** (JSON, reason "project requirements install") only when the whole command is that; chained or extra segments fall through to existing checks | parametrized cases in `test_push_hook.py`: exact forms allow; an install of any other package, or a chained `; rm` / `&& curl`, do not |
| H2 | Existing deny paths | Keep exit 2, extend stderr with the route to approval | existing deny cases still return 2; assert message contains route |

Out of scope by decision: ask-on-push, GitHub write gates. Revisit later (no ticket): ask on test/migration edits, protect `.claude/hooks` and settings, gate decision log.

## 4. CI/CD proposals
- **C1 Speed:** cold run was 11m33s vs 5 min target. Investigate in `.github/workflows/tests.yml`: Playwright cache hit path still runs `install-deps` and `pip` setup; split browser UI tests from unit tests (parallel jobs) or mark slow tests. Target < 5 min cold, measured from 3 runs.
- **C2 Triage job (read-only):** new workflow on `workflow_run` failure of `Tests`: claude-code-action with `contents: read`, `actions: read`, `pull-requests: write` limited to one comment; reads the log, classifies flaky vs real, comments summary. No code writes. Reuses existing `CLAUDE_CODE_OAUTH_TOKEN`.
- **Not now:** deploy via MCP, staging/production tiers, rollback rehearsal. Revisit after ADR-0005 (Render) is Accepted; tiers would be dev free, Render test on approved merge to `develop`, no production.
- Existing and kept: review-round limits, `ready-for-merge` label, never auto-merge.

## 5. Ticket breakdown (drafts for `/create-ticket`, all Push: Draft until a maintainer says Ready)
1. **Chore:** H1 explicit allow for the requirements install + H2 route-to-approval messages (S). Files: `.claude/hooks/block-forbidden-command.py`, `tests/test_push_hook.py`.
2. **Chore:** cut CI cold run below 5 min (S/M). File: `.github/workflows/tests.yml`, maybe test markers.
3. **Chore:** read-only CI failure triage workflow (S). New `.github/workflows/ci-triage.yml`.
4. **Docs (optional):** short note in `docs/references/` describing which gates are hooks vs prose (XS).

Order: 1 and 2 independent; 3 after 2 (stable CI first).

## 6. Decisions (formerly open questions)
1. 9 failing push-hook tests: not reproducible, dropped.
2. Allow path: hook allow for the requirements install only; settings already covers make and pytest.
3. Triage job: PR comment only (no labels, no re-runs).
4. Extra gates: dropped, listed under "Revisit later" above.

No open questions remain. Next step: `/create-ticket` for tickets 1 to 3 when a maintainer says go.

## Verification (after approval, per ticket)
- `make test` incl. `tests/test_push_hook.py`; manual: pipe sample JSON into the hook and check stdout/exit code.
- CI: three runs, record cold/warm time; trigger triage on a deliberately failing branch.
