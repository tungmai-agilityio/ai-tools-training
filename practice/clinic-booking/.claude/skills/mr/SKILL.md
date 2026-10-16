---
name: mr
description: Write the GitLab merge request title and description for a reviewed Clinic Booking branch, from the template, and open the MR on go-ahead. Use when the user says "open an MR", "write the MR description", "ready for review", or "prepare PR".
---
Never open, read, or grep `.instructor/`.

1. **Gate.** `/review` has run on the current HEAD with the verdict **approve** or **approve with nits**. If it has not run, or HEAD has changed since, run it now. If the verdict is **changes needed**, stop. `/review` owns the git, scope and pytest checks, so do not repeat them here.
2. Read the ticket and `git diff develop...HEAD`.
3. Fill `docs/templates/merge-request.md`: title = commit subject, every AC mapped to a test or manual step, checklist ticked only for what `/review` verified, with its pytest line as evidence.
4. Write it to the scratchpad or print it.
5. After the user's go-ahead: set the ticket status to `In Review` and amend it into the one commit. Then `git push -u origin <branch>` and `glab mr create --target-branch develop --title "<commit subject>" --description "$(cat <file>)"`. Report the MR link.
