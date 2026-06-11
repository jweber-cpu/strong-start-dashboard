# Build Plan: FY27 Summer Strong Start — Weekly Pace Dashboard

**Status:** Not Started
**Created:** 2026-06-10
**Updated:** 2026-06-10

## Overview
A two-piece local tool: (1) a **snapshot script** that pulls the FY27 Summer Strong Start portfolio's
projects and tasks from the Asana API into `snapshot.json`, and (2) a **static HTML dashboard** that
loads that JSON and renders weekly pace, school comparison, region rollups, and trend. Read-only,
no server, manual refresh in v1.

## Key Decisions
| Decision | Choice | Rationale |
|---|---|---|
| Build vs adopt | Build (lightweight) | Due-week cohort metric not expressible in Asana native reporting (see landscape.md) |
| Language (script) | **Python** (stdlib + `requests`) | Simple Asana pulls, easy date math with `zoneinfo`; user is Windows — works fine. (Node acceptable if preferred.) |
| Dashboard | Single `index.html`, vanilla JS + a small chart lib (e.g. Chart.js via CDN or vendored) | No build step, matches "local prototype" |
| Data flow | API → `snapshot.json` → HTML | Decouples slow API pull from fast render; snapshot is testable fixture |
| Auth | Personal access token in `.env` (gitignored) | Lowest friction; no hosting |
| Timezone | America/New_York for date comparison | Avoids off-by-one between `due_on` (date) and `completed_at` (UTC) |
| School list | Live from portfolio `1214543972018645`, exclude names containing "Test" | Stays correct as schools change |

## Architecture
```
Asana API ──(portfolio → projects → tasks, paginated)──► snapshot.py ──► snapshot.json
                                                                              │
                                          metrics.py (pure functions) ◄───────┤
                                          - week bucketing (ISO, NY tz)       │
                                          - due-week % / on-time % / backlog  │
                                          - region rollup (uses region_map)   │
                                                                              ▼
                                                     index.html + app.js ──► charts/tables
                                                     (loads snapshot.json + computed metrics
                                                      OR computes in-browser from snapshot)
config: region_map.json (from OQ-2), .env (token)
```
- **Components:** `snapshot.py` (extract), `metrics.py` (transform — pure, unit-tested), `index.html`/`app.js` (present), `region_map.json` + `.env` (config).
- **Data flow:** extract → snapshot.json → transform (in Python at snapshot time *or* in JS at load time; default: compute in Python, write `metrics.json`, so the page is dumb and fast).
- **No DB, no API endpoints, no Asana writes.**

## Implementation Roadmap

### Phase 1: Snapshot pull (extract)
**Goal:** reliably pull all in-scope tasks into `snapshot.json`.
1. Write tests: portfolio→project filter excludes "Test"; pagination assembles all pages; required fields present per task. (tests first)
2. Implement `snapshot.py`: read token from `.env`; GET portfolio items; for each project GET tasks with `opt_fields`; paginate; write `snapshot.json` with metadata (pulled_at, portfolio_gid).
3. Run against the real workspace; verify count ≈ 24 projects × ~210 tasks.
### Success Criteria
```bash
# Snapshot produced with the right shape
python -c "import json;d=json.load(open('snapshot.json'));print(len(d['schools']))"
# Expected: 24 (no Test projects)
```
```bash
# Unit tests pass
python -m pytest tests/test_snapshot.py -q
# Expected: all green
```

### Phase 2: Metrics engine (transform)
**Goal:** correct, tested weekly metrics.
1. Write property-based tests for INV-1…INV-4 (Hypothesis): % in [0,100]/"—", on-time ≤ completed ≤ cohort, one due-week per task, region totals reconcile. (tests first)
2. Implement `metrics.py`: ISO-week bucketing in America/New_York; per (school, week) cohort/completed/on-time/backlog; region rollup weighted by task count; emit `metrics.json`.
3. Edge cases: empty cohort → "—"; no `due_on` → undated bucket; `completed` without `completed_at` → on-time unknown.
### Success Criteria
```bash
python -m pytest tests/test_metrics.py -q
# Expected: all green, including property tests
```
```bash
# Region rollup reconciles to school totals (INV-4)
python -m pytest tests/test_metrics.py -k reconcile -q
# Expected: pass
```

### Phase 3: Dashboard (present)
**Goal:** leadership-usable view.
1. Write a lightweight DOM test / smoke test that the page loads metrics.json and renders the school table. (tests first)
2. Build `index.html` + `app.js`: week picker; sortable school table + bar chart (due-week % and on-time %); region toggle with expand-to-schools; trend line per school/region; Stock/School + Workstream filters; "—" for empty cohorts.
3. Visual polish: KTAF-appropriate, plain, fast. Fonts: Whitney/Calibri/Verdana fallback.
### Success Criteria
```bash
# Page and assets exist and reference the data file
ls index.html app.js metrics.json
# Expected: all present
```
```markdown
| Criterion | Verification | Expected |
|---|---|---|
| Loads without errors | open index.html, check console | no errors; table populated |
| Sort works | click completion-% header | schools reorder, ties stable |
| Region reconciles | toggle region view | region totals = sum of its schools |
```

### Phase 4: Approvals pipeline & manager effectiveness (MVP — OQ-1 resolved)
**Goal:** show review-state counts per school and manager approval timeliness.
1. Write tests: manager_group derivation (Newark→region:band, else→region) for all 24 schools (INV-6); on-time-approval = `completed_at` ≤ `due_on` (INV-7); region/band totals reconcile. (tests first)
2. Extend `metrics.py`: per-school counts by `Review Stage` (+ approved=completed, blank); per manager_group approved count, on-time-approval rate, avg days early/late.
3. Dashboard: pipeline view (state counts per school) + manager-effectiveness view (Newark split ES/MS/HS; Camden/Miami/Paterson single group), timeliness vs due date.
### Success Criteria
```bash
python -m pytest tests/test_approvals.py -q
# Expected: all green (manager grouping + on-time-approval + reconciliation)
```
```bash
# All 24 schools resolve to exactly one manager_group
python -c "import json;m=json.load(open('region_map.json'))['schools'];print(len({(s['region'] if s['region']!='Newark' else 'Newark:'+s['grade_band']) for s in m.values()}))"
# Expected: 6  (Newark:ES, Newark:MS, Newark:HS, Camden, Miami, Paterson)
```
**Deferred (OQ-5):** time-in-stage / rejection-loop counts (need task activity log).

## Technical Details
- Asana endpoints: `GET /portfolios/{gid}/items`, `GET /projects/{gid}/tasks?opt_fields=...&limit=100` with `offset` pagination.
- `opt_fields`: `name,due_on,completed,completed_at,resource_subtype,custom_fields.name,custom_fields.display_value`.
- Rate limits: batch politely; snapshot is occasional, not live.

## Security Considerations
- Token in `.env`, gitignored; never logged. Read-only calls only.
- Treat `snapshot.json`/`metrics.json` as internal; scan first real pull for any student names before sharing (org policy).

## Risks & Mitigations
| Risk | Mitigation |
|---|---|
| `Review Stage` blank on many tasks → pipeline view sparse early | Expected during build-out; "approved" still derives from `completed`, so manager-effectiveness works regardless of `Review Stage` population |
| Time-in-stage needs activity log (OQ-5) | v1 shows current-state counts + approval timeliness only; activity-log pull is a fast-follow |
| Region map wrong | Externalized to `region_map.json`; user-confirmed (OQ-2); reconciliation test catches mis-sums |
| Off-by-one week from tz | Fixed America/New_York comparison; unit tests on boundary dates |
| Portfolio membership drift | School list pulled live each snapshot |

## Human Checkpoints
- After Phase 1: confirm the 24 schools pulled match expectations (and Test projects excluded).
- After Phase 2: spot-check a couple of (school, week) numbers against Asana manually.
- After Phase 3: leadership UX review before relying on it.

## Open Items
- [x] OQ-1 approval workflow — RESOLVED (approved = completed; manager by grade band/region)
- [x] OQ-2 region map → `region_map.json` (now includes grade_band)
- [ ] OQ-3 confirm timezone (default America/New_York)
- [ ] OQ-4 refresh cadence
- [ ] OQ-5 time-in-stage via activity log (default deferred)
- [ ] Decide Python vs Node for snapshot script (default Python)

## Completion Checklist
- [ ] Phases 1–3 success criteria pass
- [ ] Region rollup reconciles
- [ ] No Test projects included; school list from portfolio
- [ ] Token not committed; snapshot reviewed for PII

## Next Step
Run `/test-plan` (done — see test-plan.md). Then begin Phase 1 by writing its tests first.
