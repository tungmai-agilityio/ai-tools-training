---
name: prd
description: Draft a Product Requirements Document (what and why) for a Clinic Booking feature or epic, saved in docs/prd/. Use when the user asks for a PRD, product requirements, user stories, or "scope this feature".
---
Never open, read, or grep `.instructor/`.

1. Read `docs/templates/prd.md`, `docs/business-rules.md`, `README.md`, and the related tickets.
2. If the problem, users or success metric is unclear, ask up to 5 questions first. Do not guess metrics.
3. Write `docs/prd/<kebab-name>.md` from the template. No implementation detail: that belongs in the spec (`/spec`).
4. User stories: `As a <role>, I want <capability>, so that <benefit>`, each with Given/When/Then ACs.
5. New business rules are worded so they can be pasted into `docs/business-rules.md`; undecided ones are marked OPEN QUESTION.
6. End with the release plan split into ticket-sized pieces, and offer to create them with `/ticket`.
