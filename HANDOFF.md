# FY27 Strong Start Dashboard — Session Handoff

## What's built

- **Live URL**: https://jweber-cpu.github.io/strong-start-dashboard/
- **Repo**: jweber-cpu/strong-start-dashboard (public, GitHub Pages on main branch)
- **Daily schedule**: 7am ET via Claude Code scheduled task `strong-start-dashboard-daily`
- **Workflow script**: saved in Claude's project directory (session-specific path — see below)

## Architecture

A Claude Code Workflow (`Workflow` tool) fetches Asana data and pushes `index.html` to GitHub Pages.

**Phase 1 — Fetch Data:**
- One agent gets today's date via bash
- 24 agents run in parallel, one per school — each executes a Python script via bash that:
  - Loads ASANA_TOKEN from `C:\Users\Jweber\Desktop\Claudio\Code Sessions\strong-start-dashboard\.env`
  - Calls Asana API with pagination until no next_page
  - Filters to Stock List tasks (field GID `1214472577362529`, value GID `1214472577362530`)
  - Returns: totalStockList, expectedTasks, completedExpected, overdueTasks

**Phase 2 — Build & Publish:**
- HTML is built deterministically in the workflow JS (no LLM involved)
- One agent pushes index.html to GitHub via `gh api` with base64-encoded content

## Known issue — ROOT CAUSE NOT YET RESOLVED

**Problem**: Only 1–6 schools show real task counts; the rest show 0.

**What we know**:
- `schoolsProcessed: 24` is always returned — agents aren't failing outright
- The schools that show data vary run to run (not consistent by cohort)
- Adding retry logic for HTTP 429s didn't help
- ASANA_TOKEN is confirmed present in the .env file

**Likely root cause**: The 24 parallel agents are each spinning up bash + Python. Some agents appear to be returning the schema-valid default (all zeros) rather than actually executing the script — possibly due to bash unavailability in some agent contexts, or the agent hallucinating zeros when the script output is ambiguous.

**Recommended fix for next session**:
Replace the 24-parallel-agent approach with a **single agent** that runs one Python script fetching all 24 schools sequentially. This eliminates parallelism risk and gives one clear execution context. The script already exists conceptually — just loop over all 24 project GIDs in one Python process.

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

## Calculations

- **Total Stock List tasks**: all tasks where Stock List field = Stock List value, deduplicated by GID across all pages
- **Expected Tasks**: Stock List tasks with due_on <= today
- **Expected %**: Expected ÷ Total (round to nearest %)
- **Actual %**: Completed expected ÷ Total (round to nearest %)
- **Overdue Tasks**: Expected AND incomplete
- **On Track**: zero overdue tasks

## HTML design

- Font: Calibri
- Navy header (#001E62) with red K-mark (#EE3C37)
- Cohort pills: Newark ES=#EE3C37, Newark MS=#F9A21A, Newark HS=#4CAF50, Camden K-12=#57C0E9, Miami K-12=#001E62, Paterson K-8=#9B59B6
- Card left border: green (#22a55b) = on track, red (#EE3C37) = off track
- Summary bar: total schools, on track count, off track count, checklist window

## Workflow script location

The workflow script is saved at a session-specific path inside Claude's project cache. To find it, search for `strong-start-dashboard-wf_*.js` in:
`C:\Users\Jweber\.claude\projects\C--Users-Jweber-Desktop-Claudio-Code-Sessions\*\workflows\scripts\`

## Next session starting point

1. Open this repo in Claude Code
2. Read this file
3. Rewrite the data-fetch phase: single agent, single Python script, loops over all 24 schools sequentially, writes results to a temp JSON file, then the workflow reads that file to build HTML
4. Test with one school first before running all 24
5. Once confirmed working, the existing GitHub push logic and 7am schedule are fine as-is
