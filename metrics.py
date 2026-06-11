"""FY27 Summer Strong Start — metrics engine (Phase 2, transform).

Pure functions over a snapshot dict (from snapshot.py). Computes per-school,
per-week pace (due-week completion % + on-time rate), running backlog, and
rolls up to regions. Manager/approval metrics live in approvals.py (Phase 4).

All date logic compares in America/New_York: due_on is a calendar date;
completed_at is a UTC timestamp converted to its NY calendar date so an
approval finished late-evening Eastern isn't counted a day late.
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")


# ---- date helpers -----------------------------------------------------------

def _parse_date(due_on: str) -> date:
    return date.fromisoformat(due_on)


def iso_week(due_on: str) -> str:
    """ISO week label 'YYYY-Www' for a YYYY-MM-DD date string."""
    y, w, _ = _parse_date(due_on).isocalendar()
    return f"{y}-W{w:02d}"


def ny_date(completed_at: str) -> date:
    """Calendar date (America/New_York) of a UTC ISO8601 timestamp."""
    ts = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
    return ts.astimezone(NY).date()


def is_on_time(completed_at: str | None, due_on: str | None):
    """True/False if completed on/before due; None if unknowable."""
    if not completed_at or not due_on:
        return None
    return ny_date(completed_at) <= _parse_date(due_on)


# ---- bucketing & cohort stats -----------------------------------------------

def bucket_by_week(tasks: list[dict]):
    """Group tasks by their due_on ISO week; return (weeks, undated_count)."""
    weeks: dict[str, list[dict]] = {}
    undated = 0
    for t in tasks:
        if not t.get("due_on"):
            undated += 1
            continue
        weeks.setdefault(iso_week(t["due_on"]), []).append(t)
    return weeks, undated


def week_stats(tasks: list[dict]) -> dict:
    """Cohort stats for one (school, week): the tasks DUE that week."""
    cohort = len(tasks)
    completed = sum(1 for t in tasks if t.get("completed"))
    on_time = sum(1 for t in tasks
                  if t.get("completed") and is_on_time(t.get("completed_at"), t.get("due_on")) is True)
    return {
        "cohort": cohort,
        "completed": completed,
        "completion_pct": round(completed / cohort * 100, 1) if cohort else None,  # INV-1
        "on_time": on_time,
        "on_time_pct": round(on_time / cohort * 100, 1) if cohort else None,
    }


def _merge_stats(a: dict, b: dict) -> dict:
    """Sum two cohort stat dicts (for rollups), recomputing percentages."""
    cohort = a["cohort"] + b["cohort"]
    completed = a["completed"] + b["completed"]
    on_time = a["on_time"] + b["on_time"]
    return {
        "cohort": cohort,
        "completed": completed,
        "completion_pct": round(completed / cohort * 100, 1) if cohort else None,
        "on_time": on_time,
        "on_time_pct": round(on_time / cohort * 100, 1) if cohort else None,
    }


def _backlog_by_week(tasks: list[dict], weeks: list[str]) -> dict[str, int]:
    """Cumulative overdue-and-still-incomplete count as of each week's end."""
    out = {}
    for wk in weeks:
        out[wk] = sum(
            1 for t in tasks
            if t.get("due_on") and iso_week(t["due_on"]) <= wk and not t.get("completed")
        )
    return out


# ---- top-level build --------------------------------------------------------

def build_metrics(snapshot: dict) -> dict:
    """Compute per-school + per-region weekly metrics from a snapshot dict."""
    all_weeks: set[str] = set()
    for s in snapshot["schools"]:
        w, _ = bucket_by_week(s["tasks"])
        all_weeks.update(w)
    weeks = sorted(all_weeks)

    schools_out = []
    region_weekly: dict[str, dict[str, dict]] = {}
    manager_weekly: dict[str, dict[str, dict]] = {}
    empty = lambda: {"cohort": 0, "completed": 0, "completion_pct": None, "on_time": 0, "on_time_pct": None}

    for s in snapshot["schools"]:
        wk_tasks, undated = bucket_by_week(s["tasks"])
        weekly = {wk: week_stats(wk_tasks.get(wk, [])) for wk in weeks}
        backlog = _backlog_by_week(s["tasks"], weeks)
        for wk in weeks:
            weekly[wk]["backlog"] = backlog[wk]
        schools_out.append({
            "gid": s["gid"], "name": s["name"], "region": s["region"],
            "grade_band": s.get("grade_band"), "manager_group": s.get("manager_group"),
            "undated": undated, "weekly": weekly,
        })
        rw = region_weekly.setdefault(s["region"], {wk: empty() for wk in weeks})
        mw = manager_weekly.setdefault(s.get("manager_group"), {wk: empty() for wk in weeks})
        for wk in weeks:
            base = {k: weekly[wk][k] for k in ("cohort", "completed", "completion_pct", "on_time", "on_time_pct")}
            rw[wk] = _merge_stats(rw[wk], base)
            mw[wk] = _merge_stats(mw[wk], base)

    regions_out = {r: {"weekly": wk} for r, wk in region_weekly.items()}
    manager_pace_out = {mg: {"weekly": wk} for mg, wk in manager_weekly.items()}

    import approvals  # function-level import avoids module-load circular dependency
    appr = approvals.build_approvals(snapshot)

    return {
        "meta": {**snapshot.get("meta", {}), "weeks": weeks},
        "weeks": weeks,
        "schools": schools_out,
        "regions": regions_out,
        "manager_pace": manager_pace_out,
        "managers": appr["managers"],
        "school_review": appr["school_review"],
    }


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    snap = json.load(open(os.path.join(here, "snapshot.json"), encoding="utf-8"))
    m = build_metrics(snap)
    out = os.path.join(here, "metrics.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2)
    # Also emit metrics.js so the dashboard opens from file:// without a server.
    js = os.path.join(here, "metrics.js")
    with open(js, "w", encoding="utf-8") as f:
        f.write("window.METRICS = ")
        json.dump(m, f)
        f.write(";\n")
    print(f"Wrote {out} and {js}: {len(m['schools'])} schools, {len(m['weeks'])} weeks "
          f"({m['weeks'][0]}..{m['weeks'][-1]})")


if __name__ == "__main__":
    main()
