"""Phase 4 tests — approvals & manager effectiveness. Tests-first.

Covers INV-6 (manager grouping) and INV-7 (approved == completed; on-time
approval iff completed_at <= due_on), plus pipeline state counts.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import approvals  # noqa: E402


def _task(due_on, completed=False, completed_at=None, review_stage=None, subtype="approval"):
    return {"due_on": due_on, "completed": completed, "completed_at": completed_at,
            "review_stage": review_stage, "resource_subtype": subtype}


def _school(gid, name, region, band, tasks):
    import snapshot
    return {"gid": gid, "name": name, "region": region, "grade_band": band,
            "manager_group": snapshot.manager_group(region, band), "tasks": tasks}


# ---- INV-7: approved == completed, on-time logic ----------------------------

def test_days_delta_new_york():
    # completed 07-18, due 07-20 => 2 days early (positive)
    assert approvals.days_delta("2026-07-18T12:00:00Z", "2026-07-20") == 2
    # completed 07-25, due 07-20 => 5 days late (negative)
    assert approvals.days_delta("2026-07-25T12:00:00Z", "2026-07-20") == -5
    assert approvals.days_delta(None, "2026-07-20") is None


def test_manager_metrics_counts_reconcile():
    snap = {"schools": [_school("1", "TEAM", "Newark", "MS", [
        _task("2026-07-20", True, "2026-07-18T12:00:00Z"),  # on-time (early)
        _task("2026-07-20", True, "2026-07-25T12:00:00Z"),  # late
        _task("2026-07-20", True, None),                     # approved, time unknown
        _task("2026-07-20", False, None, "Ready for Review"),  # awaiting manager
        _task("2026-07-20", False, None, "Draft"),             # with submitter
    ])]}
    a = approvals.build_approvals(snap)
    mg = a["managers"]["Newark:MS"]
    assert mg["approved"] == 3                       # INV-7: approved == completed
    assert mg["on_time"] == 1
    assert mg["late"] == 1
    assert mg["unknown"] == 1
    assert mg["on_time"] + mg["late"] + mg["unknown"] == mg["approved"]
    assert mg["on_time_pct"] == round(1 / 3 * 100, 1)


def test_non_approval_tasks_are_excluded():
    snap = {"schools": [_school("1", "TEAM", "Newark", "MS", [
        _task("2026-07-20", True, "2026-07-18T12:00:00Z"),                       # approval -> counts
        _task("2026-07-20", True, "2026-07-18T12:00:00Z", subtype="default_task"),  # excluded
        _task("2026-07-20", False, None, "Draft", subtype="milestone"),             # excluded
    ])]}
    a = approvals.build_approvals(snap)
    assert a["managers"]["Newark:MS"]["approved"] == 1          # only the approval task
    assert sum(a["school_review"]["1"]["counts"].values()) == 1  # only approval tasks bucketed


def test_pipeline_state_counts_sum_to_total():
    snap = {"schools": [_school("1", "TEAM", "Newark", "MS", [
        _task("2026-07-20", True, "2026-07-18T12:00:00Z"),     # Approved
        _task("2026-07-20", False, None, "Ready for Review"),
        _task("2026-07-20", False, None, "Draft"),
        _task("2026-07-20", False, None, None),                 # Not set
    ])]}
    a = approvals.build_approvals(snap)
    c = a["school_review"]["1"]["counts"]
    assert c["Approved"] == 1
    assert c["Ready for Review"] == 1
    assert c["Draft"] == 1
    assert c["Not set"] == 1
    assert sum(c.values()) == 4


# ---- INV-6: manager grouping over all 24 real schools -----------------------

def test_manager_groups_from_real_config():
    import json
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rm = json.load(open(os.path.join(here, "region_map.json"), encoding="utf-8"))
    snap = {"schools": [
        {"gid": gid, "name": s["name"], "region": s["region"], "grade_band": s["grade_band"],
         "manager_group": __import__("snapshot").manager_group(s["region"], s["grade_band"]),
         "tasks": []}
        for gid, s in rm["schools"].items()
    ]}
    a = approvals.build_approvals(snap)
    assert set(a["managers"].keys()) == {
        "Newark:ES", "Newark:MS", "Newark:HS", "Camden", "Miami", "Paterson"}


def test_real_sample_if_present():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(here, "snapshot.json")
    if not os.path.exists(path):
        return
    import json
    a = approvals.build_approvals(json.load(open(path, encoding="utf-8")))
    for mg, v in a["managers"].items():
        assert v["on_time"] + v["late"] + v["unknown"] == v["approved"]
        assert v["approved"] >= 0
