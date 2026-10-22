# T-0NN: <Outcome in the user's words>

**Status:** Open  **Type:** Feature  **Priority:** <Low|Medium|High>  **Reporter:** <Name (role)>  **Estimate:** <XS|S|M|L|TBD>

## 1. Description
<2–3 sentences: what changes for whom, and why now.>

## 2. Business rules
<The lines of `docs/business-rules.md` that apply, quoted, and any approved change as `(T-0NN, approved by <role>)`. "None" if none.>

## 3. Constraints
- <hard limits: no new dependency, frontend only, must keep existing API, performance, ...>

## 4. Acceptance criteria
- AC-1 Given <state>, when <action>, then <observable result>.
- AC-2 ...
- AC-N `pytest` passes with no existing test weakened.

## 5. Test cases
| ID | AC | Type | Given | When | Then |
|---|---|---|---|---|---|
| TC-1 | AC-1 | happy | <state> | <action> | <result> |
| TC-2 | AC-1 | error | | | 409 `<detail>` |

Type: happy, error, edge. At least one happy and one error case per AC. Edge cases from the checklist in
`docs/templates/test-plan.md` §3 that apply (others: N/A with a reason).

## 6. Out of scope
- <what we will not do in this ticket>

## 7. Open questions
<Non-blocking only; the ticket is not written while a blocking question is open.>
1. <question> — <who answers>

## 8. Implementation plan
<Filled by `/plan` after the user approves it: affected modules, dependencies, risks, steps, testing strategy.>

## Deploy note
<Optional. Only if deploying this needs a manual step (a `/db-migration` script to run, a new env var, a data reset). `/release` copies it verbatim into the release notes.>

## 9. Definition of Done
- [ ] AC-1 to AC-N pass; every test case has a test or a manual step.
- [ ] Docs updated (`README.md`, `CLAUDE.md`, `docs/business-rules.md`) if behaviour or rules changed.
- [ ] Branch `feat/T-0NN`, one commit `feat: <what> (T-0NN)`, PR into `develop`. Status → Done in that commit.
