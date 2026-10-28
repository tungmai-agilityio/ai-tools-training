---
name: Chore
about: Tooling, config, tech debt or a timeboxed spike, with no behaviour change
title: "<Task>"
labels: chore
---

**Type:** <Chore|Tech debt|Spike>  **Priority:** <Low|Medium|High>  **Reporter:** <Name (role)>  **Estimate:** <XS|S|M>

## Why
<What hurts today, or what question the spike answers.>

## What
- <concrete change 1>
- <concrete change 2>

## Deploy note
<Optional. Only if deploying this needs a manual step (a `/db-migration` script to run, a new env var, a data reset). `/release` copies it verbatim into the release notes.>

## Done when
- [ ] <checkable result>  (spike: a written answer + recommendation in this issue, timebox <N h>)
- [ ] No behaviour change; `pytest` green.
- [ ] Branch `chore/<N>-<slug>`, commit `chore: <what> (#N)`, PR into `develop` with `Closes #N`.
