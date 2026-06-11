# IT Brief — Host the Strong Start Weekly-Pace Dashboard

**Requestor:** Jeffrey Weber · **Date:** 2026-06-11
**Goal:** Give central-office and regional leaders a single private link that always shows
current FY27 Summer Strong Start progress — no Python, no tokens, nothing to install on their end.

## What it is
A small, already-built read-only dashboard. It pulls the FY27 Summer Strong Start portfolio
from **Asana**, computes weekly completion pace / on-time rates / region rollups / manager
approval timeliness, and renders a static HTML page. Code + tests are done and on GitHub
(private): `https://github.com/jweber-cpu/strong-start-dashboard`. It only **reads** Asana —
it never writes back.

## The ask (what we need IT to stand up)
A standard, low-footprint Azure pattern (fits our M365 environment):

1. **Static hosting** for the dashboard files (`index.html`, `app.js`, `metrics.js`)
   — e.g., **Azure Static Web Apps** or a Blob static website behind Front Door.
2. **A scheduled job** (twice daily is plenty) that runs the existing Python
   (`snapshot.py` → `metrics.py`) and publishes the refreshed `metrics.js` to the host
   — e.g., **Azure Function (timer trigger)**, Container App job, or Automation runbook.
3. **Access control:** gate the link behind **Entra ID (SSO)** so only an approved KTAF group
   can open it. Not a public link.
4. **A dedicated Asana service-account token** (not an individual's personal token), stored in
   **Azure Key Vault** and read by the scheduled job.

```
Entra SSO ──► Static site (index.html/app.js/metrics.js)
                         ▲ publishes metrics.js
   Scheduled job (2×/day) ── reads token ◄── Key Vault (Asana service token)
        │ runs snapshot.py + metrics.py
        ▼ pulls (read-only)
      Asana  (FY27 Summer Strong Start portfolio)
```

## Already done (to minimize IT effort)
- All logic is written and tested (23 passing tests): the Asana pull, metric computation,
  and the dashboard. No app development needed — just host + schedule + secure.
- Runtime: **Python 3.10+**, dependencies in `requirements.txt` (`requests`, `tzdata`).
- A full run pulls ~4,860 tasks across ~70 paginated calls in well under a minute.

## Security & data notes
- **Data classification: internal.** The published `metrics.js` is aggregate only (school names,
  regions, weekly counts/percentages) — no student/family data, no individual task text.
- **Sensitive view:** the dashboard includes **manager approval-effectiveness** (timing vs. due
  date), which reads as staff-performance data. Access should be limited to an approved
  leadership group, and **People Operations should weigh in** on who may view it.
- The Asana token grants read access to these projects — keep it in Key Vault, never in the
  static files or the browser.

## Decisions for IT
- Preferred host + scheduler combo (Static Web Apps + Function is our suggested default).
- Entra group that should have access.
- Who owns the Asana service account / token rotation.
- Refresh cadence (suggested: 2×/day, e.g., 6am & 1pm ET).

## Rough effort
A few hours of setup for someone familiar with Azure — this is a standard "static site +
timer job + Key Vault + SSO" pattern, not custom infrastructure. No ongoing app maintenance
beyond token rotation and occasional dependency updates.

**Contact:** Jeffrey Weber for the data/logic; repo README has run instructions.
