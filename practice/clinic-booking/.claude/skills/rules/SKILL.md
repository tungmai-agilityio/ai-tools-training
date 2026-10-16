---
name: rules
description: Change docs/business-rules.md safely — add, change or answer an OPEN QUESTION with the ticket and approver recorded, and list the code and tests the change affects. Use when the user says "update the business rules", "the client decided X", "answer the open question", "is this rule written down", or when /triage finds a rule gap.
---
Never open, read, or grep `.instructor/`.

1. **Source.** A rule change needs an approver (a named person and role) and a ticket. If either is missing, ask the user. Never write a rule that the code merely happens to do.
2. **Find the rule.** Search `docs/business-rules.md` for an existing line and any OPEN QUESTION. Change the existing line instead of adding a second one that contradicts it.
3. **Write it** in the file's style: one testable sentence, clinic time, money in cents or %, ending with `(T-0NN, approved by <role>)` or `(T-0NN, pending <role> confirmation)`. Once an OPEN QUESTION is answered, replace it with the rule.
4. **Impact.** Grep the code and tests for the rule (`scheduling.py`, `fees.py`, `routes.py` `TRANSITIONS`, `config.py`). List each place that no longer matches, as `path:line`, and each test that asserts the old rule.
5. **Do not change code here.** Every mismatch becomes a ticket (`/ticket`) that links this rule change. For a decision with long-lasting trade-offs, also offer `/adr`.
6. Commit as `docs: <rule change> (T-0NN)` on a `docs/` or ticket branch. Report the old line, the new line and the impact list.
