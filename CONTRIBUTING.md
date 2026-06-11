# Contributing

Small project, simple rules.

## Before you commit
Run the tests — they're fast and catch the easy-to-break things (week bucketing,
on-time math, region reconciliation, manager grouping):
```powershell
python -m pytest tests/ -q
```
All tests should pass before you commit.

## Layout
- `snapshot.py` — extract (read-only Asana pull). Keep it read-only — never write to Asana.
- `metrics.py` — transform (pure functions over a snapshot dict). Add metric logic here.
- `approvals.py` — manager effectiveness + review pipeline.
- `index.html` / `app.js` — present. No external/CDN dependencies; keep it offline-friendly.
- `region_map.json` — the authoritative school → region / grade_band map (manager grouping).
- `tests/` — mirror each module; add a test with any new metric or edge case.

## Don't commit
- `.env` (your Asana token) — gitignored.
- `snapshot.json`, `metrics.json`, `metrics.js` (pulled data) — gitignored; generated locally.

## Conventions
- Tests-first for new metrics: add the assertion (and a property test if it's an invariant)
  before the implementation.
- Map new tests back to a spec reference (`spec.md`) so coverage stays traceable.
- If you bound coverage (e.g., skip a project type), say so in `log`/README rather than
  silently dropping it.

## Changing the school list or regions
Edit `region_map.json` only. The school set is otherwise pulled live from the FY27 Summer
Strong Start portfolio; "Test" projects are excluded automatically.
