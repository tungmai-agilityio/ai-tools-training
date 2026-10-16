---
name: ticket
description: Write or complete a Clinic Booking ticket in tickets/T-0NN.md (feature, bug, chore, spike) from a request, a bug report or an existing vague ticket. Use when the user says "write a ticket", "turn this into a ticket", or "fill in T-0NN".
---
Never open, read, or grep `.instructor/`.

1. Pick the template by type: `docs/templates/ticket-feature.md`, `ticket-bug.md`, or `ticket-chore.md` (chore, tech debt, spike).
2. New ticket: id = highest `tickets/T-*.md` + 1. Existing ticket: keep the reporter's original text at the top and add the template sections below it.
3. Read `docs/business-rules.md` and only the code the ticket touches. Fill `path:line` references from the real code.
4. Bugs: Steps, Actual and Bug type come from `/triage`. Given a raw bug report that has not been triaged, run `/triage` instead (unless `/triage` is what called this skill).
5. Acceptance criteria are Given/When/Then, and a test or a manual step can check each one. Bugs keep them under Expected behaviour.
6. Never invent an answer for something the reporter left open, or an OPEN QUESTION in the rules. Put it under Open/Clarifying questions with who should answer.
7. Status starts `Open`. Delete template hint text (`<...>`) and any section that truly does not apply.

Finish by listing the open questions to the user.
