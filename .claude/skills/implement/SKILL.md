---
name: implement
description: Implement a Clinic Booking feature or chore ticket from its approved plan — branch, test-first code via developer, one commit, /review. Use for "implement T-0NN" or "build T-0NN". Bugs use /fix.
---
1. **Ready check.** A feature needs its approved plan (§8 filled); a simple chore needs its What list. If not, run `/plan` and stop at its gate.
2. **Branch** from an up-to-date `develop`: `feat/T-0NN` or `chore/<slug>`. Set the ticket to `In Progress`.
3. **Build.** Run the **developer** subagent with the ticket and its plan.
4. **Needs decision?** If the developer pauses, ask the user, then continue the same developer (SendMessage) with the answer. A changed requirement goes back to `/ticket`; a changed design goes back to `/plan`.
5. **Verify.** Run `pytest` yourself; don't trust an agent's summary. Every new test must have failed before the change.
6. **Commit.** Update docs if behaviour or rules changed, then make one commit `<type>: <what> (T-0NN)`. Don't push.
7. **Review.** Run `/review`. On **changes needed**, send the findings to the developer, amend, and review again. Ask the user before acting on a finding that changes scope.
8. **Report:** ACs and test cases with evidence, the pytest line, the verdict, outstanding issues (offer `/ticket`). Next: `/pr`.
