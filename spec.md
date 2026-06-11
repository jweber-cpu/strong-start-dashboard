# Spec: FY27 Summer Strong Start — Weekly Pace Dashboard

> Generated from `/feature-spec` on 2026-06-10. Grounded in live inspection of the Asana workspace.

## Overview
A local dashboard that shows, **week by week**, how each of 24 schools (across 4 regions) is pacing
against the FY27 Summer Strong Start checklist in Asana. For any given week it answers: *of the
tasks that were due that week, how many has each school completed, and how does that compare to
other schools and to the region?* It replaces the single "total % complete" number Asana shows
today with a schedule-relative, comparable, time-series view.

## Target User
**Central office leadership** (network-level). Primary user is the requester (Jeffrey Weber) and
peers who need a cross-network read. Not built for school-level self-service in v1 (school leaders
already see their own Asana project).

## Problem Statement
Asana reports only **total completion %** of the ~210-task project per school. With ~24 nearly
identical projects, leadership can't tell *week by week* whether a school is keeping pace with what
was scheduled, whether it's catching up or slipping, or how regions compare. The pain is the
inability to act early — by the time total % looks low, the school is already far behind.

## User Stories

**US-1 — Weekly pace per school**
Leadership sees, for a selected week, each school's due-week completion % and on-time rate.
<details>
<summary>Detail</summary>

- **Source:** interview + Asana inspection.
- **Steps:** open dashboard → pick a week → see a sortable table/bar chart of all 24 schools.
- **Acceptance (Given-When-Then):**
  - Given tasks with `due_on` in the selected ISO week, When the dashboard loads, Then each school shows `completed_in_cohort / total_in_cohort` as a % .
  - Given a completed task, When `completed_at` ≤ `due_on`, Then it counts toward **on-time**; when `completed_at` > `due_on`, it counts complete-but-late.
</details>

**US-2 — Compare schools**
Leadership ranks/sorts schools for a week to spot leaders and laggards.
<details>
<summary>Detail</summary>

- **Acceptance:** Given a selected week, When sorting by due-week completion %, Then schools order correctly and ties are stable; When a school has zero tasks due that week, Then it shows "—" (not 0%) so it isn't mistaken for failing.
</details>

**US-3 — Region rollup**
Leadership toggles to a region-by-region view (Newark / Camden / Miami / Paterson).
<details>
<summary>Detail</summary>

- **Acceptance:** Given the school→region map, When region view is selected, Then each region shows aggregate due-week completion % weighted by task count (not a simple average of school %s), and can expand to its schools.
- **Blocked by:** OQ-2 (region map).
</details>

**US-4 — Trend over time**
Leadership sees a school's (or region's) weekly completion across the summer to see catching-up vs. slipping.
<details>
<summary>Detail</summary>

- **Acceptance:** Given multiple weeks of data, When viewing trend, Then a line/area shows due-week completion % per week and cumulative backlog (overdue-and-incomplete) per week.
</details>

**US-5 — Approvals pipeline & manager effectiveness** *(OQ-1 RESOLVED)*
Leadership sees where items sit in review per school, and how timely **managers** are at approving.
<details>
<summary>Detail</summary>

- **Confirmed workflow:** A school-based teammate submits by setting `Review Stage` = **Ready for Review**, which reassigns the task to their **manager**. The manager reviews; if not approved it goes back to the submitter as **Draft**; the loop repeats until the manager approves, at which point **the task is completed**. Therefore **"approved" == `completed`**, and **`completed_at` is the approval timestamp.**
- **Pipeline view (per school):** counts of items by current state — Draft, Ready for Review (awaiting manager), Approved (completed), and blank/not-started.
- **Manager-effectiveness view:** for approved items, measure **`completed_at` (approval date) vs `due_on`** → on-time-approval rate and avg days early/late, **grouped by manager**. Manager grouping = Newark → by **grade band** (ES/MS/HS each = a distinct manager); Camden, Miami, Paterson → by **region** (single manager today). Grade band is carried for all so the view can split if managers are added.
- **Acceptance (Given-When-Then):**
  - Given an approved (completed) item with `completed_at`, When ≤ `due_on`, Then it counts as an on-time approval for that item's manager group; When > `due_on`, late (record days late).
  - Given the manager view for Newark, When grouped, Then ES/MS/HS appear as separate managers; for Camden/Miami/Paterson the region is one manager group.
  - Given items still in Ready for Review, When the pipeline view loads, Then they show as "awaiting manager" with days-waiting since entering that stage *(days-waiting requires stage-entry timestamps — see OQ-5)*.
- **Coverage:** scoped to **approval-type tasks only** (`resource_subtype == "approval"`, ~13 per school) — the items that actually go through submit → review → approve. Regular tasks and milestones are excluded from the approvals view; they're covered by the weekly-pace metrics. (Corrected 2026-06-11 per user.)
</details>

## Invariants & Edge Cases
**Invariants (drive property-based tests):**
- INV-1: due-week completion % = completed-in-cohort ÷ tasks-due-in-week, always in [0, 100] or "—" when denominator = 0.
- INV-2: on-time count ≤ completed count ≤ cohort total, for every school/week.
- INV-3: a task belongs to exactly one due-week (the ISO week of its `due_on`); tasks with no `due_on` are excluded from cohort metrics and counted separately as "undated".
- INV-4: region rollup totals reconcile — sum of region cohort counts = sum of in-scope school cohort counts.
- INV-5: test/demo projects are never included; school set = current portfolio membership.
- INV-6: every in-scope school maps to exactly one (region, grade_band); manager_group derives deterministically (Newark → region:band; else → region).
- INV-7: an approved item's approval timestamp = its `completed_at`; on-time-approval iff `completed_at` date ≤ `due_on`.

**Edge cases:**
- School with **0 tasks due** in a week → display "—", excluded from averages.
- Task with **no `due_on`** → excluded from due-week metrics, surfaced in an "undated tasks" count.
- Task **completed before it was due** → on-time.
- Task completed with **no `completed_at`** but `completed=true` → count complete; on-time = unknown (flag).
- **Timezone:** `due_on` is a date (no time); `completed_at` is a UTC timestamp. Compare on calendar date in a fixed timezone (America/New_York) to avoid off-by-one.
- Duplicate-named schools (e.g., Legacy ES vs Legacy MS, Paterson Prep ES vs MS) must stay distinct by project GID.
- Portfolio changes (school added/removed) between snapshots.

## Detailed Requirements
- Pull **all projects in portfolio `1214543972018645` (FY27 Summer Strong Start)**; ignore any project name containing "Test".
- Per task, capture: `gid`, `name`, `due_on`, `completed`, `completed_at`, `resource_subtype`, and custom fields `Workstream`, `Applicable Region`, `Review Stage`, `List Type`, `Driver`.
- Bucket tasks into ISO weeks (Mon–Sun) by `due_on` in America/New_York.
- Metrics per (school, week): cohort size, completed count, completion %, on-time count, on-time %, plus cumulative overdue-incomplete (backlog).
- Attach `region`, `grade_band`, and derived `manager_group` to each school from `region_map.json`.
- Approval/manager metrics: per (manager_group): approved-item count, on-time-approval rate (`completed_at` ≤ `due_on`), avg days early/late; per school: current counts by `Review Stage` (Draft / Ready for Review / approved=completed / blank).
- Optional filters: by `Workstream`, by `List Type` (Stock vs School), by `Driver`, by region/grade band.
- Visible date range configurable (default: min→max `due_on` in the data).

## Scope (MVP vs Future)
**In (MVP):** US-1, US-2, US-3, US-4, **US-5 (approvals pipeline + manager-effectiveness)**; portfolio-driven school list; test-project exclusion; due-week % + on-time %; region **and grade-band/manager** rollups; Stock/School and Workstream filters; single local HTML reading a JSON snapshot; manual refresh via a pull script.
**Out (v1):** time-in-stage / rejection-loop counts that need the activity log (OQ-5, default deferred); live/auto-refresh + hosting; auth beyond a personal token; per-school login; FY26 or DSO Playbook projects; writing back to Asana.

## Technical Context
- **Data source:** Asana REST API. Portfolio → projects → tasks with `opt_fields` for the fields above. Pagination required (~210 tasks × 24 ≈ 5,000 tasks).
- **Stack (proposed, see build plan):** a small Node or Python script for the snapshot pull (`snapshot.json`), and a single static `index.html` (vanilla JS + a charting lib) that loads the JSON. No server in v1.
- **Auth:** Asana personal access token, kept in a local `.env` / not committed.
- **Reference:** see landscape.md — custom build chosen because the due-week cohort metric isn't expressible in Asana native reporting.
- **Field GIDs (FY27, confirmed):** portfolio `1214543972018645`; `Review Stage` `1214466859502165` (Draft `…502166`, Ready for Review `…502167`); `List Type` `1214472577362529` (Stock `…362530`, School `…362531`); `Applicable Region` `1214466879907115`; `Workstream` `1214555120153662`; `Driver` `1214466801734390`.

## Test Strategy
- **Unit:** week-bucketing, % math, on-time comparison, "—" for empty cohorts (property-based on INV-1–4).
- **Integration:** snapshot parser against a saved real Asana JSON fixture; portfolio→task pipeline with pagination; test-project exclusion.
- **Manual/visual:** dashboard renders, sort works, region toggle reconciles to school totals.
- **Baseline:** project has no prior test suite (new repo) — baseline = lint + the new unit/integration suites must pass.

## Security Considerations
- **Risk level: Medium.** Pulls real operational data and requires an Asana token.
- Token must never be committed; load from env. Snapshot JSON may contain task names/owners — treat as internal, don't publish.
- No student/family PII expected in these tasks (operational checklist items), but **scan the first real snapshot** for any names before sharing; per org policy, exclude identifiable student info.
- Local-only prototype reduces exposure; if later hosted, revisit auth + access control.

## Explicit Boundaries (what the build should NOT touch)
- Must not modify or complete any Asana tasks (read-only API usage).
- Must not include the FY26 projects, DSO Playbook, or any "Test" project.
- Must not invent a school→region map or an approval workflow — both come from the user (OQ-1, OQ-2).

## Open Questions
- [x] **OQ-1 (approvals): RESOLVED 2026-06-10.** Submit (Ready for Review) → reassign to manager → reject back to Draft, loop → manager approves = task **completed**; `completed_at` = approval timestamp. Manager grouping by grade band (Newark) / region (else). Covers all in-scope tasks. Approvals view promoted from deferred into MVP scope.
- [ ] **OQ-5 (new):** "Days waiting in Ready for Review" and "rejection count / loops" require **stage-entry timestamps**, which the task fields don't carry directly — they live in the task **story/activity log**. Decide for v1: (a) skip time-in-stage and show current-state counts + approval timeliness only, or (b) pull each task's stories to reconstruct stage transitions (heavier API cost). Default: (a) for v1.
- [x] **OQ-2 (region map): RESOLVED 2026-06-10.** Authoritative map confirmed by user, stored in `region_map.json` (keyed by project GID). See below.
- [ ] **OQ-3:** Confirm America/New_York as the comparison timezone for all regions (incl. Miami, which is also Eastern — likely fine).
- [ ] **OQ-4:** Refresh cadence for the snapshot in practice (daily? on-demand before leadership meetings?).

### Region map — CONFIRMED (OQ-2), source of truth = `region_map.json`
- **Newark (12):** TEAM, Rise, SPARK, Seek, Life, THRIVE, Lab, BOLD, NCA, Purpose, Justice, KURA
- **Camden (5):** LSP, LSM, Sumner, KHS, Hatch
- **Miami (5):** KIPP Miami Tech, Legacy ES, Legacy MS, KCA, KRA
- **Paterson (2):** Paterson Prep ES, Paterson Prep MS

## Success Definition
Leadership can open the dashboard, pick a week, and within seconds see every school's due-week
completion % and on-time rate, sort to find who's behind, and toggle to a region rollup that
reconciles to the school numbers — using live portfolio membership and excluding test projects.

## Next Step
Run `/plan` to design architecture and phases (done — see build-plan.md), then `/test-plan`.
