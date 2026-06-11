"""Phase 1 tests — snapshot extraction. Written before snapshot.py (tests-first).

These exercise the PURE functions and the pagination assembler with a fake
session, so no network or token is needed to run them.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import snapshot  # noqa: E402


# ---- INV-5: test/demo projects never included -------------------------------

def test_is_test_project_flags_test_names():
    assert snapshot.is_test_project("Newark Test FY27 Summer Strong Start")
    assert snapshot.is_test_project("Katie Paterson Test FY27 Summer Strong Start")
    assert not snapshot.is_test_project("TEAM FY27 Summer Strong Start")
    assert not snapshot.is_test_project("KIPP Miami Tech FY27 Summer Strong Start")


def test_filter_projects_drops_test_projects():
    items = [
        {"gid": "1", "name": "TEAM FY27 Summer Strong Start"},
        {"gid": "2", "name": "Newark Test FY27 Summer Strong Start"},
        {"gid": "3", "name": "SPARK FY27 Summer Strong Start"},
    ]
    kept = snapshot.filter_projects(items)
    assert [p["gid"] for p in kept] == ["1", "3"]


# ---- task normalization -----------------------------------------------------

def _raw_task(**over):
    base = {
        "gid": "t1",
        "name": "Do the thing",
        "due_on": "2026-07-31",
        "completed": False,
        "completed_at": None,
        "resource_subtype": "default_task",
        "custom_fields": [
            {"name": "Workstream", "display_value": "Attendance"},
            {"name": "Applicable Region", "display_value": "Newark Only"},
            {"name": "Review Stage", "display_value": None},
            {"name": "List Type", "display_value": "Stock List"},
            {"name": "Driver", "display_value": "DSO"},
        ],
    }
    base.update(over)
    return base


def test_task_to_record_flattens_fields():
    rec = snapshot.task_to_record(_raw_task())
    assert rec["gid"] == "t1"
    assert rec["due_on"] == "2026-07-31"
    assert rec["completed"] is False
    assert rec["workstream"] == "Attendance"
    assert rec["list_type"] == "Stock List"
    assert rec["review_stage"] is None
    assert rec["driver"] == "DSO"


def test_task_to_record_handles_completed_and_missing_fields():
    rec = snapshot.task_to_record(_raw_task(
        completed=True, completed_at="2026-07-20T14:00:00.000Z", due_on=None,
        custom_fields=[],
    ))
    assert rec["completed"] is True
    assert rec["completed_at"] == "2026-07-20T14:00:00.000Z"
    assert rec["due_on"] is None
    # missing custom fields normalize to None, never KeyError
    assert rec["workstream"] is None
    assert rec["review_stage"] is None


# ---- pagination assembly ----------------------------------------------------

class FakeSession:
    """Returns queued pages regardless of URL; records calls."""
    def __init__(self, pages):
        self._pages = list(pages)
        self.calls = 0

    def get(self, url, params=None, timeout=None):
        self.calls += 1
        page = self._pages.pop(0)
        return _FakeResp(page)


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200

    def json(self):
        return self._payload

    def raise_for_status(self):
        pass


def test_paginate_assembles_all_pages():
    pages = [
        {"data": [{"gid": "a"}, {"gid": "b"}], "next_page": {"offset": "X"}},
        {"data": [{"gid": "c"}], "next_page": None},
    ]
    sess = FakeSession(pages)
    rows = snapshot.paginate(sess, "https://example/tasks", {})
    assert [r["gid"] for r in rows] == ["a", "b", "c"]
    assert sess.calls == 2


# ---- build_snapshot joins region_map by GID ---------------------------------

def test_build_snapshot_attaches_region_and_manager_group():
    region_map = {
        "schools": {
            "p_team":  {"name": "TEAM",  "region": "Newark", "grade_band": "MS"},
            "p_spark": {"name": "SPARK", "region": "Newark", "grade_band": "ES"},
            "p_khs":   {"name": "KHS",   "region": "Camden", "grade_band": "HS"},
        }
    }
    projects = [
        {"gid": "p_team", "name": "TEAM FY27 Summer Strong Start"},
        {"gid": "p_khs",  "name": "KHS FY27 Summer Strong Start"},
    ]
    tasks_by_project = {"p_team": [_raw_task()], "p_khs": [_raw_task(gid="t2")]}
    snap = snapshot.build_snapshot(projects, tasks_by_project, region_map,
                                   pulled_at="2026-06-10T00:00:00Z")
    by_gid = {s["gid"]: s for s in snap["schools"]}
    assert by_gid["p_team"]["region"] == "Newark"
    assert by_gid["p_team"]["manager_group"] == "Newark:MS"
    assert by_gid["p_khs"]["manager_group"] == "Camden"  # non-Newark = region
    assert len(by_gid["p_team"]["tasks"]) == 1
    assert snap["meta"]["pulled_at"] == "2026-06-10T00:00:00Z"


def test_manager_group_rule():
    assert snapshot.manager_group("Newark", "ES") == "Newark:ES"
    assert snapshot.manager_group("Newark", "HS") == "Newark:HS"
    assert snapshot.manager_group("Camden", "HS") == "Camden"
    assert snapshot.manager_group("Miami", "MS") == "Miami"


def test_region_map_file_has_24_schools_and_resolves_6_manager_groups():
    """Guards the real config: exactly 24 schools, 6 manager groups."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(here, "region_map.json"), encoding="utf-8") as f:
        rm = json.load(f)
    schools = rm["schools"]
    assert len(schools) == 24
    groups = {snapshot.manager_group(s["region"], s["grade_band"]) for s in schools.values()}
    assert groups == {"Newark:ES", "Newark:MS", "Newark:HS", "Camden", "Miami", "Paterson"}
