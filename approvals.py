"""FY27 Summer Strong Start — approvals & manager effectiveness (Phase 4).

Workflow (confirmed): a school teammate sets Review Stage = "Ready for Review"
(reassigning to their manager); the manager either sends it back to "Draft" or
approves it, and **approving = completing the task**. So approved == completed
and `completed_at` is the approval timestamp.

Manager effectiveness = approval timing vs. due date, grouped by manager_group
(Newark -> region:grade_band; else -> region). Pure functions; unit-tested.
"""
from __future__ import annotations

from datetime import date

import metrics  # reuse NY-aware date helpers (no circular import at module load)


def days_delta(completed_at: str | None, due_on: str | None):
    """Days between due date and approval date (NY). Positive = early, negative = late."""
    if not completed_at or not due_on:
        return None
    return (date.fromisoformat(due_on) - metrics.ny_date(completed_at)).days


def _review_state(task: dict) -> str:
    """Bucket a task into a pipeline state (approved overrides review_stage)."""
    if task.get("completed"):
        return "Approved"
    rs = task.get("review_stage")
    if rs in ("Draft", "Ready for Review"):
        return rs
    return "Not set"


def build_approvals(snapshot: dict) -> dict:
    """Manager-effectiveness rollups + per-school pipeline state counts."""
    managers: dict[str, dict] = {}
    school_review: dict[str, dict] = {}

    for s in snapshot["schools"]:
        mg = s.get("manager_group")
        m = managers.setdefault(mg, {
            "schools": [], "approved": 0, "on_time": 0, "late": 0, "unknown": 0,
            "_delta_sum": 0, "_delta_n": 0,
        })
        if s["name"] not in m["schools"]:
            m["schools"].append(s["name"])

        counts = {"Approved": 0, "Ready for Review": 0, "Draft": 0, "Not set": 0}
        for t in s["tasks"]:
            counts[_review_state(t)] += 1
            if t.get("completed"):
                m["approved"] += 1
                ot = metrics.is_on_time(t.get("completed_at"), t.get("due_on"))
                if ot is True:
                    m["on_time"] += 1
                elif ot is False:
                    m["late"] += 1
                else:
                    m["unknown"] += 1
                d = days_delta(t.get("completed_at"), t.get("due_on"))
                if d is not None:
                    m["_delta_sum"] += d
                    m["_delta_n"] += 1
        school_review[s["gid"]] = {
            "name": s["name"], "manager_group": mg, "counts": counts,
        }

    # finalize manager stats
    for m in managers.values():
        known = m["on_time"] + m["late"]
        m["on_time_pct"] = round(m["on_time"] / m["approved"] * 100, 1) if m["approved"] else None
        m["avg_days_delta"] = round(m["_delta_sum"] / m["_delta_n"], 1) if m["_delta_n"] else None
        del m["_delta_sum"], m["_delta_n"]

    return {"managers": managers, "school_review": school_review}
