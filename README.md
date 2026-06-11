# FY27 Summer Strong Start — Weekly Pace Dashboard

Local dashboard showing **week-by-week** completion pace for the FY27 Summer Strong Start
checklist across 24 schools / 4 regions, sourced from Asana. Replaces Asana's single
"total % complete" with a schedule-relative, comparable, time-series view.

See `spec.md`, `build-plan.md`, `test-plan.md`, `landscape.md` for the design.

## What's here
- `snapshot.py` — pulls the FY27 Summer Strong Start portfolio from Asana (read-only) → `snapshot.json`
- `metrics.py` — computes weekly due-cohort completion %, on-time %, backlog, region rollups → `metrics.json` + `metrics.js`
- `index.html` + `app.js` — the dashboard (no dependencies; opens straight from a browser)
- `region_map.json` — authoritative school → region + grade_band (manager) map
- `tests/` — pytest suite (run before trusting changes)
- `build_sample_snapshot.py` — dev-only: assembles a 6-school sample from saved pulls (throwaway)

## Run it for real (full 24 schools)
```powershell
pip install -r requirements.txt
copy .env.example .env          # then paste your Asana token into .env
python snapshot.py              # pulls all 24 schools  -> snapshot.json
python metrics.py               # computes metrics      -> metrics.json + metrics.js
```
Get a token at https://app.asana.com/0/my-apps (Personal access tokens). It stays in
`.env`, which is gitignored — never commit it.

## Open the dashboard
Just open `index.html` in a browser (it reads `metrics.js`, so no server needed).
Or serve it: `python -m http.server 8765` then visit http://localhost:8765/.

## Refreshing
Re-run `python snapshot.py && python metrics.py` whenever you want current numbers
(e.g., before a leadership meeting), then reload the page.

## Tests
```powershell
python -m pytest tests/ -q
```

## Status / notes
- The committed `snapshot.json`/`metrics.json` (if present) are a **DEV SAMPLE**: 6 schools
  (one per manager group), first 100 tasks each. Run `snapshot.py` with a token for the full set.
- **Manager effectiveness** (approval timing vs due date) and the **approvals pipeline** view
  are Phase 4 (`approvals.py`) — not yet built. "Approved" = task completed; `completed_at` is
  the approval timestamp.
- Time-in-stage / rejection-loop counts need the Asana activity log — deferred (OQ-5).
