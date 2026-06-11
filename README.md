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

## Teammate setup (clone from GitHub)
For a teammate setting this up on their own machine the first time. Requires
**Python 3.10+** and an **Asana account with access to the FY27 Summer Strong Start portfolio**.
```powershell
git clone https://github.com/jweber-cpu/strong-start-dashboard.git
cd strong-start-dashboard
pip install -r requirements.txt
copy .env.example .env          # then paste YOUR Asana token into .env (see below)
python snapshot.py              # pulls all 24 schools  -> snapshot.json
python metrics.py               # computes metrics      -> metrics.json + metrics.js
```
Then open `index.html`. After the first setup, just double-click **`refresh.bat`** to pull
fresh data (it runs both scripts for you).

> Note: running locally needs Python **and** a personal Asana token per person. That's fine
> for ops/technical teammates. Leaders who only need to *view* should instead be sent the
> generated `index.html` + `app.js` + `metrics.js` (opens in any browser, no install), or use
> the hosted version if/when it's stood up.

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
Double-click **`refresh.bat`** whenever you want current numbers — e.g., before a leadership
meeting. It pulls fresh Asana data, rebuilds the metrics, rebuilds the self-contained
`dashboard.html`, and opens it in your browser. (Manual equivalent:
`python snapshot.py && python metrics.py && python build_standalone.py`.)

## Tests
```powershell
python -m pytest tests/ -q
```

## Status / notes
- All four build phases are complete: snapshot pull, weekly metrics, dashboard, and the
  **manager-effectiveness + approvals-pipeline** views (`approvals.py`). "Approved" = task
  completed; `completed_at` is the approval timestamp.
- Data files (`snapshot.json`, `metrics.json`, `metrics.js`) are **gitignored** — each runner
  generates them locally from their own pull. Nothing data-bearing lives in the repo.
- **Not built (by design):** time-in-stage / rejection-loop counts (need the Asana activity
  log, OQ-5); hosted always-current version; FY26 / DSO Playbook projects.
