# T-0NN: <Outcome in the user's words>

**Status:** Open  **Type:** Feature  **Priority:** <Low|Medium|High>  **Reporter:** <Name (role)>  **Estimate:** <XS|S|M|L|TBD>

## 1. Summary
<2–3 sentences: what changes for whom, and why now. Name any hard constraint (no new dependency, frontend only, ...).>

## 2. Analysis
- **Asks:** <one sentence>
- **Ambiguous:** <one sentence; details in §8>
- **First step:** <usually the failing test or the wireframe>

## 3. Approach
<Files and functions that change, as `path` → what. Keep existing interfaces where possible.>

## 4. Acceptance criteria
- AC-1 Given <state>, when <action>, then <observable result>.
- AC-2 ...
- AC-N `pytest` passes with no existing test weakened.

## 5. Out of scope
- <what we will not do in this ticket>

## 6. Business-rule impact
<"None", or the exact lines to add/change in `docs/business-rules.md`, and who approved them.>

## 7. Test plan
- Automated: <new test names and files; which must fail before the change>
- Manual: <UI or `/docs` steps>

## 8. Open questions
1. <question> — <who answers>

## 9. Definition of Done
- [ ] AC-1 to AC-N pass.
- [ ] Docs updated (`README.md`, `CLAUDE.md`, `docs/business-rules.md`) if behaviour or rules changed.
- [ ] Branch `feat/T-0NN`, one commit `feat: <what> (T-0NN)`, MR into `develop`. Status → In Review.
