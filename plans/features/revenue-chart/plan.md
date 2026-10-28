# Plan: Revenue chart and screen layout (proposed T-032, T-033)

**Author:** Claude (draft, for Tung to edit)  **Status:** Draft, not approved  **Decisions:** ADR-0001, ADR-0004, DDR-0003
**Design:** [UI design Artifact](https://claude.ai/artifact/VaAYYy7WoVCPzw2wEwS6jp), board 4 "Admin: Revenue report", board 6 "As built"
**Related:** `plans/features/revenue-report/spec.md` (T-015, API), `plans/archive/T-015.md`, `plans/archive/T-016.md` (current screen)

No code is written until Tung approves this plan. Sections marked **Open** wait for Tung.

## 1. What the design shows vs what is built

Captured from the running app with Playwright on 2026-10-28 (fake data, 12 to 16 Oct, admin session). Screenshots: light and dark, 1280 and 375, in the session scratchpad; they move into the Artifact's "As built" board when the chart ships.

| Area | Design (board 4) | Built today | Gap |
|---|---|---|---|
| Revenue by day | Stacked bar chart, consultation + penalty, total label on each bar, legend, y-axis `$0..$600`, "weekends left out" note | A "By day" table (one row per day with money) | **Chart missing.** Main gap. |
| By-doctor | Table in a 380px card beside the chart | Full-width table below the stats | Layout only |
| Summary cards | Order Total, Consultations ("Completed visits"), Penalties ("No-shows and late cancels"), each with a caption | Order Consultation, Penalty, Total; no captions | Order and captions |
| Money format | `$2,610.00` (thousands separator) | `$2250.00` (no separator, `money()` in `app.js`) | Formatting |
| Date range | From, To and the button in the page header, right-aligned, button "Show report" | Separate card with From, To and "Run report" below the header | Layout and wording |
| Page note | "Gross, in clinic time (America/New_York). Each visit counts on the day it was scheduled." under the title | "Days in America/New_York" under the title; the gross and scheduled-day note is a paragraph under the form, with the range and run time | Wording |
| Phone | Not drawn | Stats wrap 2+1; tables become cards (works) | Chart needs a phone layout |
| Dark theme | Not drawn | Works | Chart needs dark colours |

Design Artifact problems to fix at the same time (the design is a draft, so these are errors in it, not in the app):
- Doctor names `Dr. Maria Santos`, `Dr. Elena Park` are not in the seed. The seed has Carter, Emily Brooks and Sarah Mitchell.
- The penalty colour `#f0a35e` on a white surface has a contrast ratio of 2.02:1 (the `dataviz` validator warns below 3:1). See section 3.
- The nav lists "Holidays and time off", which the app has no screen for. That is not part of this plan (see section 8).

## 2. What is already planned or ticketed

Nothing. Searched `plans/`, `docs/` and the open sprint:
- **T-016** (done) said "no charts". T-015 and T-016 are archived and read-only.
- **DDR-0003** (Accepted) says "The Revenue screen shows totals, a stacked bar chart by day and a by-doctor table". So the chart is a decided design, but no ticket carries it.
- **T-022** (closed, merged) built the login UI and did not touch the Revenue results. Its ACs do not mention a chart.
- The Artifact's board 6 lists "Revenue chart and by-doctor table" under "Still differs (later tickets)", but no such ticket exists. The highest ticket is T-031. T-024 to T-027 are Ready but unrelated (CI and screenshots) and not in a sprint.

So: propose new tickets (section 7). The next free ID is T-032.

## 3. Chart approach

**Recommendation: hand-written inline SVG, built by one pure function in `app/static/app.js`. No library.**

Why it fits the constraints:
- **CSP (ADR-0001, `script-src 'self'`).** The policy restricts scripts only. Inline `<svg>` markup inserted with the same `innerHTML` pattern the screen already uses is allowed. Our own `app.js` draws it, so no new script origin.
- **No build step and no new dependency (`CLAUDE.md`).** A vendored chart library (Chart.js is about 200 KB, minified, and draws on `<canvas>`) would add a vendored file to approve and keep patched, and a canvas is not readable by a screen reader or testable from the DOM. One stacked bar chart is about 60 lines of SVG.
- **Escaping.** The only API strings in the chart are dates and cents, both formatted by existing helpers (`fmtKey`, `money`) and passed through `esc()`. Doctor names are not in the chart.
- **Testable.** `revenueChart(by_day)` takes data and returns a string, like `renderRevenue`, so `tests/test_frontend.py` can run it under `node` (existing `_run_js` pattern) and Playwright can assert on `<rect>` count and labels.

Rejected: Chart.js or similar (above), a `<canvas>` (no accessibility, no DOM test), CSS-only bars (cannot place axis labels cleanly and the stacked gap rule is awkward). Revisit a library only if the app adopts React and Vite (ADR-0001's signal).

**Form (dataviz skill).** Two parts of one total (consultation, penalty) per day: a stacked bar is right. Day totals are shown as direct labels. The by-doctor table stays a table (exact money, three columns).

**Colour.** Validated with `validate_palette.js`:
- Consultation uses `--brand` (teal, already themed for light and dark). Penalty needs a new pair of tokens `--chart-penalty`: light `#b45309` (passes lightness, 3:1 contrast, colour-blind separation 11.2 and normal-vision 22.1), dark `#f0a35e` (passes contrast and separation; dark mode was validated against surface `#1a1a19`).
- The design's `#f0a35e` on white fails the 3:1 contrast check, so the light value is darkened. Update board 4 to match.
- Brand teal `#0f766e` is flagged "reads gray" by the validator's chroma floor. It is the product brand colour and the validator's own note says secondary encoding makes this acceptable, which we have: a legend, 2px gaps between segments and a total label on every bar.
- Text (axis labels, totals) uses ink tokens, never the series colour. Segments are separated by a 2px surface gap. Bars have rounded top corners and a flat baseline.

**Many days.** `by_day` only lists days with money, up to about 260 weekdays in a 366-day range. Rule proposed: bar width is fixed at 28px with a minimum gap, the chart sits in a horizontally scrolling box (`overflow-x:auto`, as in the design), and per-bar total labels are dropped above 14 bars (the tooltip and the table still give every number). See Open question 3.

## 4. Data and API needs

None. `GET /reports/revenue` already returns `by_day` with `date`, `consultation_cents`, `penalty_cents`, `total_cents` (see `plans/features/revenue-report/spec.md` and `docs/references/api.md`). Zero-money days are already omitted, which matches the design note. No backend, model or business-rule change, so no `db-migration` and no `DomainError` involvement. Money stays integer cents; the chart scales cents to pixels and never formats a float as money.

One thing to guard in the script: axis maximum is computed from cents with integer maths and rounded up to a "nice" step ($100, $200, $500, $1,000, ...), so labels are never fractional.

## 5. Accessibility

- The SVG has `role="img"` and an `aria-label` summarising the range and totals (the design does this). Because a summary label cannot carry 30 values, the existing **By day table stays** below the chart inside a `<details>` ("Show as table"), open by default on phones and closed on desktop (Open question 2). So the same data is available to a screen reader and by keyboard.
- Legend is real text with a colour swatch (`aria-hidden`), so colour is never the only signal; the order of segments is fixed (consultation below, penalty above).
- Contrast: axis and label text at the existing `--ink-muted` (4.5:1 or better), segment colours at 3:1 or better against the surface in both themes.
- Hover or focus tooltip per bar (dataviz rule): bars are not focusable, so the tooltip is a convenience; every value is in the table. Hit area wider than the bar. No animation, so no reduced-motion handling.
- Reflow: at 375px the chart scrolls horizontally inside its card; the page itself must not scroll sideways (existing `test_no_sideways_scroll_on_a_phone` covers the Revenue screen).

## 6. Tests and screenshots

- `tests/test_frontend.py` (node): `revenueChart` returns one `<g>` per day, bar heights proportional to cents, total label `$1,234.00`-style via `money`, empty `by_day` returns no chart (the existing "No revenue in this range" empty state shows instead), a doctor name with `<script>` never reaches the SVG, axis max is a nice step for 0, 1 cent and 99,999 cents.
- `tests/test_ui_browser.py` (Python Playwright, ADR-0004): admin runs the report with seeded fake data, expects the chart `role=img` with the right label, one bar group per day, the table behind "Show as table", no CSP violation. Phone and dark variants via the existing `snap()` fixture (desktop 1280x800, phone 375x812; masks for password inputs are unaffected here). Take the dark screenshot with the theme set through the sidebar control, not a cookie.
- Screenshots are evidence, not pixel comparison (ADR-0004). Both sizes in light and dark go to the PR Evidence section, and the same PNGs replace the Revenue part of board 6 "As built".
- `tests/test_reports.py` is unchanged because the API does not change.
- Ticket test-case Artifact: add TCs for the chart (happy, empty, single day, many days, phone, dark).

## 7. UI Artifact updates

Edit the design Artifact only after Tung picks the options below, on branch of the canvas files (Revenue.dc.html, AsBuilt.dc.html), publishing to the same URL.
1. Board 4: fix the doctor names to the seed, change the penalty colour to the validated value, add the "Show as table" disclosure, and show the many-days case.
2. New board "4b Revenue, phone 375 and dark" (the design has neither).
3. If Tung wants to compare options, add a board with 2 or 3 clickable variants (a `data-props` switch or buttons, `is_interactive: true`) of the open choices: chart with and without per-bar labels, table open or closed by default, header form layout.
4. Board 6: after the build, replace the "Still differs" Revenue line with as-built screenshots.

## 8. Tickets breakdown (proposed, not created)

Neither is in a sprint. S-002 is closed to new scope without team agreement (`CLAUDE.md`), so these wait for `/sprint-prepare` or Tung's decision to add them.

| ID | Title | Type, est. | Needs | Files |
|---|---|---|---|---|
| T-032 | Show daily revenue as a stacked bar chart | Feature, S | nothing (API ready) | `app/static/app.js` (`revenueChart`, `renderRevenue`), `app/static/index.html` (chart CSS, tokens), tests above |
| T-033 | Match the Revenue screen to the design (layout, captions, `$2,610.00`) | Chore, XS | T-032 (same render function; do after to avoid conflicts) | `app/static/app.js`, `app/static/index.html`, tests that assert `$1650.00`-style strings |

T-033 is split off because the thousands separator is in the shared `money()` helper used by every screen, so it can change other screens' text and tests. If Tung prefers one ticket, T-033 folds into T-032 (estimate S to M).

**Not in this plan:** a "Holidays and time off" screen (the design lists it, the app has no UI for closures and no ticket for it; propose separately if wanted), changing the report rules (T-015 §11 questions stay open), per-doctor charts, CSV export, comparison to the previous period.

Workflow once approved: `/create-ticket` for each, `/sprint-prepare` to place them, `/push-tickets`, `/implement-ticket` (test-first, then screenshots), `/pr`. One approval of this file covers both tickets, as for the authentication and browser E2E plans.

## 9. Open questions (one at a time with Tung)

1. ~~**Chart approach:**~~ **Decided (Tung, 2026-10-28): hand-written inline SVG.**
2. ~~**By-day table:**~~ **Decided (Tung, 2026-10-28): keep it behind "Show as table".**
3. ~~**Long ranges (more than about 14 days):**~~ **Decided (Tung, 2026-10-28): scroll sideways and drop per-bar labels.**
4. ~~**Scope and timing:**~~ **Decided (Tung, 2026-10-28): add the tickets into S-002.** Sprint file and ticket `Sprint:` fields are edited only after plan approval, via `/sprint-prepare`; the Sprint ends 2026-11-13, so S-002 capacity needs a check then. Section 8's "outside S-002" wording is superseded.
5. ~~**Money format:**~~ **Decided (Tung, 2026-10-28): change the shared `money()` helper.** T-033 updates every test string that asserts the old format.
6. **Design fixes:** update board 4 with the validated penalty colour, seed doctor names and a phone and dark board (recommended).
