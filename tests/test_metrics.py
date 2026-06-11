"""Phase 2 tests — metrics engine. Written before metrics.py (tests-first).

Property tests cover INV-1..INV-4; unit tests cover week bucketing, the
timezone-sensitive on-time comparison, and empty/undated edge cases.
"""
import os
import sys
from datetime import date

from hypothesis import given, strategies as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import metrics  # noqa: E402


# ---- pure date helpers ------------------------------------------------------

def test_iso_week_label():
    assert metrics.iso_week("2026-07-31") == "2026-W31"
    assert metrics.iso_week("2026-06-05") == "2026-W23"


def test_iso_week_boundary_sun_mon():
    # 2026-07-26 is a Sunday (W30), 2026-07-27 Monday (W31)
    assert metrics.iso_week("2026-07-26") == "2026-W30"
    assert metrics.iso_week("2026-07-27") == "2026-W31"


def test_on_time_uses_new_york_date_not_utc():
    # completed_at 02:00 UTC on the 21st = 22:00 EDT on the 20th -> NY date 07-20
    # due_on 07-20 => on-time in NY, but would be LATE if compared in UTC.
    assert metrics.is_on_time("2026-07-21T02:00:00.000Z", "2026-07-20") is True
    # completed two days after due is late regardless of tz
    assert metrics.is_on_time("2026-07-22T20:00:00.000Z", "2026-07-20") is False


def test_on_time_unknown_when_no_completed_at():
    assert metrics.is_on_time(None, "2026-07-20") is None


# ---- cohort math (INV-1, INV-2) ---------------------------------------------

def _task(due_on, completed=False, completed_at=None):
    return {"due_on": due_on, "completed": completed, "completed_at": completed_at}


def test_empty_cohort_returns_none_not_zero():
    stats = metrics.week_stats([])
    assert stats["cohort"] == 0
    assert stats["completion_pct"] is None  # INV-1: "—", not 0%


def test_basic_completion_and_on_time():
    tasks = [
        _task("2026-07-20", True, "2026-07-18T12:00:00Z"),  # on-time
        _task("2026-07-20", True, "2026-07-25T12:00:00Z"),  # late
        _task("2026-07-20", False),                          # incomplete
    ]
    s = metrics.week_stats(tasks)
    assert s["cohort"] == 3
    assert s["completed"] == 2
    assert s["completion_pct"] == round(2 / 3 * 100, 1)
    assert s["on_time"] == 1
    assert s["on_time_pct"] == round(1 / 3 * 100, 1)


@given(
    cohort=st.integers(min_value=0, max_value=200),
    completed=st.integers(min_value=0, max_value=200),
    on_time=st.integers(min_value=0, max_value=200),
)
def test_property_counts_bounded(cohort, completed, on_time):
    # INV-2: on_time <= completed <= cohort must always hold after clamping
    completed = min(completed, cohort)
    on_time = min(on_time, completed)
    tasks = []
    for i in range(cohort):
        if i < on_time:
            tasks.append(_task("2026-07-20", True, "2026-07-19T12:00:00Z"))
        elif i < completed:
            tasks.append(_task("2026-07-20", True, "2026-07-25T12:00:00Z"))
        else:
            tasks.append(_task("2026-07-20", False))
    s = metrics.week_stats(tasks)
    assert 0 <= s["on_time"] <= s["completed"] <= s["cohort"]
    if s["cohort"]:
        assert 0.0 <= s["completion_pct"] <= 100.0
    else:
        assert s["completion_pct"] is None


# ---- bucketing & undated (INV-3) --------------------------------------------

def test_undated_tasks_excluded_from_weeks():
    tasks = [_task("2026-07-20", True, "2026-07-19T12:00:00Z"),
             _task(None, True, "2026-07-19T12:00:00Z")]
    weeks, undated = metrics.bucket_by_week(tasks)
    assert "2026-W30" in weeks and len(weeks["2026-W30"]) == 1
    assert undated == 1


# ---- region rollup reconciles (INV-4) ---------------------------------------

def test_region_rollup_reconciles_to_schools():
    snapshot = {
        "schools": [
            {"gid": "1", "name": "A", "region": "Newark", "grade_band": "MS",
             "manager_group": "Newark:MS",
             "tasks": [_task("2026-07-20", True, "2026-07-19T12:00:00Z"),
                       _task("2026-07-20", False)]},
            {"gid": "2", "name": "B", "region": "Newark", "grade_band": "ES",
             "manager_group": "Newark:ES",
             "tasks": [_task("2026-07-20", True, "2026-07-25T12:00:00Z")]},
        ]
    }
    m = metrics.build_metrics(snapshot)
    wk = "2026-W30"
    school_cohort = sum(s["weekly"][wk]["cohort"] for s in m["schools"])
    region_cohort = m["regions"]["Newark"]["weekly"][wk]["cohort"]
    assert region_cohort == school_cohort == 3  # INV-4
    assert m["regions"]["Newark"]["weekly"][wk]["completed"] == 2


def test_manager_pace_reconciles_to_schools():
    snapshot = {
        "schools": [
            {"gid": "1", "name": "A", "region": "Newark", "grade_band": "MS",
             "manager_group": "Newark:MS",
             "tasks": [_task("2026-07-20", True, "2026-07-19T12:00:00Z"), _task("2026-07-20", False)]},
            {"gid": "2", "name": "B", "region": "Newark", "grade_band": "ES",
             "manager_group": "Newark:ES",
             "tasks": [_task("2026-07-20", True, "2026-07-25T12:00:00Z")]},
        ]
    }
    m = metrics.build_metrics(snapshot)
    wk = "2026-W30"
    assert set(m["manager_pace"].keys()) == {"Newark:MS", "Newark:ES"}
    assert m["manager_pace"]["Newark:MS"]["weekly"][wk]["cohort"] == 2
    assert m["manager_pace"]["Newark:ES"]["weekly"][wk]["cohort"] == 1
    total = sum(mp["weekly"][wk]["cohort"] for mp in m["manager_pace"].values())
    assert total == sum(s["weekly"][wk]["cohort"] for s in m["schools"])


def test_build_metrics_on_real_sample_if_present():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(here, "snapshot.json")
    if not os.path.exists(path):
        return
    import json
    snap = json.load(open(path, encoding="utf-8"))
    m = metrics.build_metrics(snap)
    # every school % is in range or None; on_time<=completed<=cohort every week
    for s in m["schools"]:
        for wk, st_ in s["weekly"].items():
            assert 0 <= st_["on_time"] <= st_["completed"] <= st_["cohort"]
            assert st_["completion_pct"] is None or 0.0 <= st_["completion_pct"] <= 100.0
