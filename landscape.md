# Landscape: FY27 Summer Strong Start — Weekly Pace Dashboard

> Generated from `/landscape` on 2026-06-10
> Interview context: Yes (see spec.md)

## Problem Statement
Central office leadership needs to see, **week by week**, how each of 24 schools across 4 regions
is pacing against the FY27 Summer Strong Start checklist (~210 tasks per school) in Asana.
Asana's native reporting only shows **total completion %** of the whole project, which hides
whether a school is keeping up with what was *due this week* or falling behind. We also want a
view of where items sit in the **approval/review** process, and the ability to roll results up
**by region**.

## Search Criteria
- **Core problem:** weekly, schedule-relative completion tracking across many identical Asana projects, with cross-school comparison and regional rollups.
- **Target stack:** local prototype — read from the Asana REST API, render a single dashboard. No hosting in v1.
- **Key requirements:** due-week completion %; on-time rate (completed_at vs due_on); per-school + per-region; pull school list from the FY27 Summer Strong Start portfolio; exclude test projects.

## Candidates

### Asana Dashboards / Reporting (native)
- **What it does:** Built-in charts on a project or portfolio.
- **Coverage:** Low–Medium — good for total completion and simple groupings, but cannot express "of tasks *due* in week X, what % are now complete" or "completed on/before due date" across 24 projects in one comparable view.
- **Health:** High (vendor-maintained). **Fit:** High (no build).
- **Gaps:** The exact weekly, schedule-relative metric the user is missing. This is *why* the request exists.

### Asana Portfolios + Universal Reporting
- **What it does:** Roll up multiple projects; chart by custom field.
- **Coverage:** Medium — can group by `Workstream`/`Applicable Region` and show progress, but still no due-week-cohort or on-time logic; region rollup blocked by lack of a school→region field.
- **Health:** High. **Fit:** High. **Gaps:** Same weekly-cohort gap; no school-level region attribute.

### Google Looker Studio + Asana connector (or Sheets export)
- **What it does:** BI dashboards over Asana data via connector or a Sheets sync.
- **Coverage:** Medium–High — can compute custom weekly metrics if data is shaped first.
- **Health:** Medium (third-party connectors vary). **Fit:** Medium — introduces another tool/auth; region map still must be supplied externally; weekly-cohort math is awkward in pure BI.
- **Gaps:** Still need a transform layer to bucket by due-week and compute on-time rate; ongoing connector cost/licensing.

### Custom lightweight dashboard (Asana API → JSON snapshot → static HTML)
- **What it does:** A small script pulls the portfolio's projects + tasks (`due_on`, `completed_at`, `Review Stage`, `List Type`, `Workstream`) into a JSON snapshot; a single HTML page renders weekly pace, comparison, and region rollups.
- **Coverage:** High — we control the exact metric definitions (due-week %, on-time rate, backlog).
- **Health:** High (no third-party dependency beyond Asana API). **Fit:** High (matches "prototype, local").
- **Gaps:** We build and maintain it; v1 is snapshot-based (manual refresh), not live-streaming.

## Comparison Matrix

| Option | Coverage | Health | Fit | Notes |
|---|---|---|---|---|
| Asana native dashboards | Low–Med | High | High | Can't do due-week/on-time cohort metric |
| Asana portfolio reporting | Med | High | High | No school→region; no weekly cohort |
| Looker Studio / Sheets | Med–High | Med | Med | Extra tool + transform layer + cost |
| **Custom API → JSON → HTML** | **High** | **High** | **High** | Exact metrics; matches local-prototype intent |

## Recommendation

**Build from Scratch (lightweight) — with a fast-follow check of Asana native reporting.**

The defining requirement — *"of the tasks due in week X, how many did each school complete, and were they on time"* — is a **due-week cohort metric** that Asana's native dashboards and portfolio reporting fundamentally don't express, and that BI connectors can only do after a custom transform. Since the requested target is a **local prototype** anyway, the lowest-friction path is a small pull-and-render tool: one script to snapshot the portfolio's tasks from the Asana API, one static HTML dashboard to compute and display the metrics. This keeps full control over metric definitions, needs no hosting or new vendor, and is cheap to throw away or evolve.

Before investing further, we should spend ~30 minutes confirming Asana's native **portfolio reporting** truly can't approximate the weekly view — if leadership would accept "completed this week" throughput (which Asana *can* chart) instead of strict due-week cohorts, a no-build option may suffice.

## Open Questions
- [ ] Would leadership accept Asana-native "completed per week" charts (throughput) in lieu of strict due-week cohort %? If yes, no build needed.
- [ ] Asana API access: personal access token vs. a service account for the snapshot pull.

## Next Step
Run `/feature-spec` to write the specification (done — see spec.md).
