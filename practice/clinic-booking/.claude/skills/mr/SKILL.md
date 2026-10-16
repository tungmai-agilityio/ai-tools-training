---
name: mr
description: Prepare a Clinic Booking branch for a GitLab merge request — check git conventions, run pytest, and write the MR title and description from the template. Use when the user says "open an MR", "write the MR description", "ready for review", or "prepare PR".
---
Never open, read, or grep `.instructor/`.

1. Check against `docs/references/git-conventions.md`:
   - branch is `feat/T-0NN`, `fix/T-0NN` or `chore/<slug>`, based on `develop`;
   - `git log develop..HEAD --oneline` is one commit named `<type>: <what> (T-0NN)`. If not, tell the user and suggest the squash; do not rewrite history without asking.
2. Run `pytest` and keep the summary line. If it fails, stop and report.
3. Read the ticket and `git diff develop...HEAD`. Flag anything outside the ticket's scope.
4. Fill `docs/templates/merge-request.md`: title = commit subject, every AC mapped to a test or manual step, checklist ticked only for what you verified.
5. Write it to the scratchpad or print it. Pushing, creating the MR, and moving the ticket to `In Review` need the user's go-ahead.
