# FY27 Strong Start Dashboard — Session Handoff

## What's built

- **Live URL**: https://jweber-cpu.github.io/strong-start-dashboard/
- **Repo**: jweber-cpu/strong-start-dashboard (public, GitHub Pages on main branch)
- **Daily schedule**: 7am ET via GitHub Actions — runs in the cloud, no local machine needed
- **Manual trigger**: Actions tab → Refresh Dashboard → Run workflow

## Dashboard design

The published dashboard is the **card-based view**:
- Navy header (#001E62) with red K-mark (#EE3C37) and italic tagline
- Summary bar: Total Schools / On Track / Off Track / Checklist Window (Jun 5 – Aug 14)
- School cards grouped by cohort pill (colored by region)
- Each card: school name, total tasks, On/Off track status, Expected Tasks, Expected %, Actual %, Overdue Tasks
- On track = green border/pill (zero overdue); Off track = red border/pill
- Font: Calibri

**Do not use** the weekly-pace dashboard (week picker, bar charts, sortable table) — that is `template.html` / `dashboard.html` in the local repo and is for a different purpose.

## Architecture

GitHub Actions runs the pipeline daily at 7am ET (cron `0 11 * * *` UTC):

1. **`fetch_all_schools.py`** — fetches all 24 schools sequentially from Asana, writes `school_data.json`
2. **`build_card_dashboard.py`** — reads `school_data.json`, builds card-based HTML, writes `index.html`
3. **Commit & push** — `index.html` committed to main branch, GitHub Pages deploys automatically

No Claude workflow or local machine required for daily refresh.

## Key files

| File | Purpose |
|------|---------|
| `fetch_all_schools.py` | Fetches Asana data for all 24 schools sequentially |
| `build_card_dashboard.py` | Builds card-based HTML from school_data.json |
| `.github/workflows/refresh.yml` | GitHub Actions workflow (daily 7am ET + manual trigger) |
| `ASANA_TOKEN` | GitHub repo secret — used by Actions to authenticate with Asana |

## Why sequential fetch (not parallel)

The previous approach spawned 24 parallel agents, one per school. Only 1–6 schools returned real data; the rest returned zeros. Root cause: parallel bash agent contexts silently returned schema-valid defaults.

`fetch_all_schools.py` fetches all 24 schools in one Python process, sequentially, with retry on connection errors. Reliable and confirmed working.

## fetch_all_schools.py

- Loops all 24 school GIDs sequentially
- Paginates Asana API with retry (handles HTTPError + ConnectionResetError)
- Filters to Stock List field (GID `1214472577362529`, value GID `1214472577362530`)
- Usage: `python fetch_all_schools.py YYYY-MM-DD output.json`

## Schools and project GIDs

| School | GID | Cohort |
|--------|-----|--------|
| KURA | 1214543972018542 | Newark ES |
| Life | 1214543972018529 | Newark ES |
| Seek | 1214543972018516 | Newark ES |
| SPARK | 1214543972018490 | Newark ES |
| THRIVE | 1214543972018503 | Newark ES |
| BOLD | 1214543972018581 | Newark MS |
| Justice | 1214543972018607 | Newark MS |
| Purpose | 1214543972018594 | Newark MS |
| Rise | 1214543972018568 | Newark MS |
| TEAM | 1214543972018555 | Newark MS |
| Lab | 1214543972018633 | Newark HS |
| NCA | 1214543972018620 | Newark HS |
| Hatch | 1214566137135712 | Camden K-12 |
| KHS | 1214566137135725 | Camden K-12 |
| LSM | 1214566202106004 | Camden K-12 |
| LSP | 1214566202106030 | Camden K-12 |
| Sumner | 1214566202106017 | Camden K-12 |
| KCA | 1214566137135751 | Miami K-12 |
| KIPP Miami Tech | 1214566137135790 | Miami K-12 |
| KRA | 1214566137135738 | Miami K-12 |
| Legacy ES | 1214566137135764 | Miami K-12 |
| Legacy MS | 1214566137135777 | Miami K-12 |
| Paterson Prep ES | 1214566137135813 | Paterson K-8 |
| Paterson Prep MS | 1214566137135826 | Paterson K-8 |

## Asana config

- Portfolio GID: `1214543972018645`
- Stock List field GID: `1214472577362529`
- Stock List enum value GID: `1214472577362530`
- Checklist window: June 5 – August 14, 2026
- ASANA_TOKEN: stored as a GitHub repo secret (Settings → Secrets → Actions)

## Calculations

- **Total Stock List tasks**: all tasks where Stock List field = Stock List value
- **Expected Tasks**: Stock List tasks with due_on <= today
- **Expected %**: Expected ÷ Total (round to nearest %)
- **Actual %**: Completed expected ÷ Total (round to nearest %)
- **Overdue Tasks**: Expected AND incomplete
- **On Track**: zero overdue tasks

## Claude scheduled task

A Claude scheduled task (`strong-start-dashboard-daily`) also exists but is now redundant — GitHub Actions is the primary automation. The Claude task can be left as a backup or deleted.

## Repo notes

- `.nojekyll` is present — prevents Jekyll from stripping JS
- `fetch_all_schools.py` is committed to the repo (force-added past gitignore)
- `school_data.json` is gitignored — generated at runtime, not stored in repo
- `template.html` and `dashboard.html` are the weekly-pace dashboard (local use only)

## Next session starting point

1. Open this repo in Claude Code
2. Read this file
3. Pipeline is working end-to-end — no known issues
4. To debug: run `python fetch_all_schools.py YYYY-MM-DD school_data.json` locally and check output has real task counts before investigating anything else
