# Test Plan: FY27 Summer Strong Start — Weekly Pace Dashboard

> Generated from `/test-plan` on 2026-06-10.

## Pipeline Position
`/interview → /feature-spec → /plan → /test-plan → build → /milestone-check`

This plan says *how to prove the dashboard is correct*. The build plan says what to build.

## Inputs
- spec.md (invariants INV-1…INV-5, acceptance criteria, edge cases, Medium security)
- build-plan.md (Phases 1–3, components `snapshot.py` / `metrics.py` / `index.html`)
- New repo — **no prior test suite**, so the baseline is the suites defined here plus lint.

## Baseline (always run)
```bash
python -m pytest -q          # all unit + integration + property tests
python -m pyflakes .         # or ruff — no lint errors
```
Add: a saved **real Asana JSON fixture** (`tests/fixtures/snapshot_real.json`, captured once, PII-scrubbed) so transform tests run without hitting the API.

## Properties & Invariants (property-based — Hypothesis)
| ID | Property | From |
|---|---|---|
| P-1 | due-week completion % ∈ [0,100], or "—" when cohort size = 0 | INV-1 |
| P-2 | on-time count ≤ completed count ≤ cohort total (∀ school, week) | INV-2 |
| P-3 | every dated task maps to exactly one ISO due-week; undated excluded | INV-3 |
| P-4 | Σ region cohort counts = Σ in-scope school cohort counts (reconciliation) | INV-4 |
| P-5 | no project whose name contains "Test" ever appears in results | INV-5 |
| P-6 | every school resolves to exactly one (region, grade_band) and one manager_group | INV-6 |
| P-7 | on-time-approval iff `completed_at` date ≤ `due_on`; late count + on-time count = approved count | INV-7 |

## Tests by Phase

### Phase 1 — Snapshot (extract) — write first
- `test_snapshot.py`
  - Integration: portfolio items → projects, filter drops "Test" names (P-5).
  - Pagination: multi-page task responses are fully assembled (mock 2+ pages).
  - Shape: each task has `due_on` key (nullable), `completed`, `completed_at`, custom fields present.
  - Maps to: spec Detailed Requirements; INV-5.

### Phase 2 — Metrics (transform) — write first
- `test_metrics.py`
  - Property: P-1, P-2, P-3, P-4 (Hypothesis generators for synthetic tasks).
  - Unit: ISO-week bucketing across **week boundaries** (Sun 23:59 vs Mon 00:00) in America/New_York.
  - Unit: on-time logic — `completed_at` date ≤ `due_on` ⇒ on-time; > ⇒ late; `completed` w/o `completed_at` ⇒ on-time unknown.
  - Unit: empty cohort ⇒ "—" (not 0%); undated task ⇒ undated bucket, excluded from %.
  - Unit: region rollup weighted by task count (not mean of %s).
  - `-k reconcile` selects P-4.
  - Maps to: US-1, US-2, US-3, US-4; INV-1…INV-4; spec edge cases.

### Phase 4 — Approvals & manager effectiveness — write first
- `test_approvals.py`
  - Property: P-6 (manager_group derivation for all 24 schools — Newark→region:band, else→region; expect 6 groups), P-7 (on-time-approval logic, counts reconcile).
  - Unit: approved == completed; `completed_at` missing on a completed item ⇒ approval-time unknown (flagged, excluded from timeliness avg).
  - Unit: Newark splits ES/MS/HS as 3 managers; Camden/Miami/Paterson each one group.
  - Unit: per-school `Review Stage` counts (Draft / Ready for Review / approved / blank) sum to school task total.
  - Maps to: US-5; INV-6, INV-7.

### Phase 3 — Dashboard (present) — write first
- `test_dashboard_smoke` (DOM/headless or manual checklist)
  - Page loads `metrics.json` and renders the 24-school table.
  - Sort by completion % reorders; ties stable.
  - Region toggle totals equal sum of member schools (visual reconcile of P-4).
  - "—" shown for schools with no tasks due in the selected week.
  - Maps to: US-1, US-2, US-3.

## Edge Cases to Cover
- Week with zero due tasks for a school → "—".
- Task with null `due_on` → undated count, not in %.
- Completed-before-due → on-time.
- `completed=true`, `completed_at=null` → complete, on-time unknown (flagged).
- Duplicate-stem schools kept distinct by GID (Legacy ES/MS; Paterson Prep ES/MS).
- Portfolio gains/loses a school between two snapshots.
- DST / Eastern boundary date correctness.

## Security Testing (Medium risk)
- Token never appears in committed files or logs (grep test on repo + sample log).
- API layer issues **no** write/PUT/POST-complete calls (assert read-only client).
- Fixture is PII-scrubbed; add a check that flags any task name containing patterns that look like student names before sharing a snapshot (manual gate).

## Verification Commands (for `/milestone-check`)
```bash
# Phase 1
python -m pytest tests/test_snapshot.py -q          # all green
python -c "import json;print(len(json.load(open('snapshot.json'))['schools']))"   # 24
# Phase 2
python -m pytest tests/test_metrics.py -q           # all green (incl. property tests)
python -m pytest tests/test_metrics.py -k reconcile -q   # P-4 passes
# Phase 4
python -m pytest tests/test_approvals.py -q          # all green (manager grouping + on-time-approval)
# Phase 3
ls index.html app.js metrics.json                   # present
# + manual: load page, sort, region toggle, "—" behavior, manager-effectiveness view
```

## Open Items / Infra
- [ ] Install: `pip install pytest hypothesis requests` (+ `ruff` or `pyflakes`).
- [ ] Capture + PII-scrub `tests/fixtures/snapshot_real.json` (one real pull).
- [ ] OQ-1/OQ-2 resolved before testing Phase 4 (approvals) and region reconciliation against real labels.

## Notes
- Highest-leverage tests are the property tests (P-1…P-4) and the week-boundary unit tests — that's where the metric is easy to get subtly wrong.
- Map every test back to a spec reference; don't write coverage-padding tests.

## Next Step
Begin Phase 1 by writing `tests/test_snapshot.py`, then implement `snapshot.py` until green.
Run `/milestone-check 1` after Phase 1.
