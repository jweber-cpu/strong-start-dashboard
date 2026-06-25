# FY27 Strong Start Dashboard — Session Handoff

## What's built

- **Live URL**: https://jweber-cpu.github.io/strong-start-dashboard/
- **Repo**: jweber-cpu/strong-start-dashboard (public, GitHub Pages on main branch)
- **Daily schedule**: 7am ET via Claude Code scheduled task `strong-start-dashboard-daily`
- **Workflow script**: `C:\Users\Jweber\.claude\projects\C--Users-Jweber-Desktop-Claudio-Code-Sessions\759dd4b4-e296-4f6e-a343-28557f014195\workflows\scripts\strong-start-dashboard-wf_97bab375-a80.js`

## Dashboard design

The published dashboard is the **card-based view**:
- Navy header (#001E62) with red K-mark (#EE3C37) and italic tagline
- Summary bar: Total Schools / On Track / Off Track / Checklist Window (Jun 5 – Aug 14)
- School cards grouped by cohort pill (colored by region)
- Each card: school name, total tasks, On/Off track status, Expected Tasks, Expected %, Actual %, Overdue Tasks
- On track = green border/pill (zero overdue); Off track = red border/pill
- Font: Calibri

**Do not use** the weekly-pace dashboard (week picker, bar charts, sortable table) — that is `index.html` / `dashboard.html` in the local repo and is for a different purpose.

## Architecture

A Claude Code Workflow (`Workflow` tool) fetches Asana data and pushes `index.html` to GitHub Pages via the `gh` CLI.

**Phase 1 — Fetch Data (2 agents):**
1. Agent runs `fetch_all_schools.py TODAY school_data.json` via bash, returns `{today, success}`
2. Agent reads `school_data.json` and returns its raw contents as plain text (no schema — avoids truncation)
3. Workflow JS does `JSON.parse(rawJson)` to get school data

**Phase 2 — Build & Publish (1 agent):**
- HTML is built deterministically in the workflow JS (no LLM involved)
- Agent pushes index.html to GitHub via `gh api` with base64-encoded content

## Why this architecture

The previous approach spawned 24 parallel agents (one per school), each running a Python script via bash. Only 1–6 schools returned real data; the rest returned zeros. Root cause: agents in parallel bash contexts silently return schema-valid defaults when execution is unreliable.

The fix: `fetch_all_schools.py` fetches all 24 schools sequentially in one Python process and writes `school_data.json`. A single agent runs it. A second agent reads the file as raw text — not via schema — to avoid the agent truncating a large structured response.

## fetch_all_schools.py

Located at: `C:\Users\Jweber\Desktop\Claudio\Code Sessions\strong-start-dashboard\fetch_all_schools.py`

- Loops all 24 school GIDs sequentially
- Paginates Asana API with retry (handles HTTPError + ConnectionResetError)
- Filters to Stock List field (GID `1214472577362529`, value GID `1214472577362530`)
- Writes results to the output path passed as argv[2]
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
- ASANA_TOKEN: loaded from `.env` in the repo directory

## Calculations

- **Total Stock List tasks**: all tasks where Stock List field = Stock List value
- **Expected Tasks**: Stock List tasks with due_on <= today
- **Expected %**: Expected ÷ Total (round to nearest %)
- **Actual %**: Completed expected ÷ Total (round to nearest %)
- **Overdue Tasks**: Expected AND incomplete
- **On Track**: zero overdue tasks

## Scheduled task

- Task ID: `strong-start-dashboard-daily`
- Schedule: 7am ET daily (cron `0 7 * * *`)
- Runs on local machine — requires Claude Code to be running at 7am
- Points at the workflow script path listed above
- Last ran: 2026-06-24; next run: 2026-06-25 7am ET

## Manual run

To trigger a manual refresh, tell Claude Code:
> Run the strong-start-dashboard workflow

Or use the Workflow tool directly with the script path above.

## Repo notes

- `.nojekyll` is present — prevents Jekyll from stripping inlined JS
- `refresh.yml` GitHub Actions workflow has been removed — Claude scheduled task is the automation
- `fetch_all_schools.py` and `school_data.json` are gitignored (local only)
- `template.html` and `dashboard.html` are the weekly-pace dashboard (local use only, not published to Pages)

## Next session starting point

1. Open this repo in Claude Code
2. Read this file
3. Pipeline is working end-to-end — no known issues
4. If cards show zeros, test locally first: `python fetch_all_schools.py 2026-06-25 school_data.json` and verify output has real task counts
