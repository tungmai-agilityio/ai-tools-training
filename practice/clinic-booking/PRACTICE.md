# How to practice with this repo

You play one role. Claude plays the other people. Use one chat thread per role
(`BA-sim`, `QA-sim`, `Reviewer-sim`, `Lead-sim`, `Client-sim`).

## Using the web app

Start the server, open http://127.0.0.1:8000/, and run `python scripts/seed_demo.py`.
Reproduce bugs from the UI where you can, and from `/docs` where you cannot. A good
QA habit is to try the same case both ways and note when they differ.

## Persona prompt (paste, then fill in the brackets)

```
You are [role/persona] on a clinic booking project. Stay in character.
You know these hidden facts: [facts]. Only reveal one if I ask the right question.
Be realistic: busy, sometimes vague, sometimes wrong. Do not help me more than a real person would.
When I say DEBRIEF, step out of character and grade me against: [skill bar].
List what I missed first.
```

## Ticket map

| Ticket | Best role to play | Skill it trains |
|---|---|---|
| T-001 | QA, then Dev | Reproduce a vague bug, write a failing test |
| T-002 | QA | Spot the missing condition in a ticket |
| T-003 | Dev | Money rules and rounding |
| T-004 | Dev | Time and timezone bugs |
| T-005 | BA | Business rule is unclear: ask the right questions |
| T-006 | Reviewer or Lead | Security basics |
| T-007 | Dev | Config problem vs code problem |
| T-008 | Dev | Data problem vs code problem |
| T-009 | BA | Turn a one-line feature request into a spec |

## Suggested order (matches Week 1, Days 1 to 3)

- Day 1: T-001, T-002, T-007, T-008 (understand and reproduce)
- Day 2: T-003, T-004 (fix, test, PR, self-review with Claude)
- Day 3: T-005, T-006, T-009 (BA/review drills), then the conflict drill and one full end-to-end ticket

Grade yourself with `.instructor/ANSWER_KEY.md` only after you finish a drill.

## Done checklist

- [ ] Wrote a repro in a ticket
- [ ] Fixed a bug on a branch with a test that failed first
- [ ] Opened a PR a stranger could review
- [ ] Left at least 3 actionable review comments
- [ ] Merged a PR and resolved one conflict
- [ ] Caught at least one wrong thing in AI output by running it
