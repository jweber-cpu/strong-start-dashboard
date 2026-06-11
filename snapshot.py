"""FY27 Summer Strong Start — Asana snapshot pull (Phase 1, extract).

Reads the FY27 Summer Strong Start portfolio, pulls every in-scope project's
tasks (read-only), normalizes them, joins the school->region/grade_band map,
and writes snapshot.json.

Pure functions (is_test_project, filter_projects, task_to_record, paginate,
manager_group, build_snapshot) are unit-tested without network. main() does the
I/O: loads .env + region_map.json, calls the Asana API, writes snapshot.json.

Usage:
    pip install -r requirements.txt
    copy .env.example .env   # then put your ASANA_TOKEN in it
    python snapshot.py
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone

API = "https://app.asana.com/api/1.0"

TASK_OPT_FIELDS = (
    "name,due_on,completed,completed_at,resource_subtype,"
    "custom_fields.name,custom_fields.display_value"
)

# Map Asana custom-field display names -> flat record keys.
_FIELD_KEYS = {
    "Workstream": "workstream",
    "Applicable Region": "applicable_region",
    "Review Stage": "review_stage",
    "List Type": "list_type",
    "Driver": "driver",
}


# ---- pure helpers -----------------------------------------------------------

def is_test_project(name: str) -> bool:
    """True if the project name marks it as a test/demo (excluded, INV-5)."""
    return "test" in (name or "").lower()


def filter_projects(items: list[dict]) -> list[dict]:
    """Drop test projects from a list of portfolio project items."""
    return [p for p in items if not is_test_project(p.get("name", ""))]


def task_to_record(task: dict) -> dict:
    """Flatten an Asana task into the normalized shape the dashboard uses."""
    fields = {k: None for k in _FIELD_KEYS.values()}
    for cf in task.get("custom_fields") or []:
        key = _FIELD_KEYS.get(cf.get("name"))
        if key:
            fields[key] = cf.get("display_value")
    return {
        "gid": task.get("gid"),
        "name": task.get("name"),
        "due_on": task.get("due_on"),
        "completed": bool(task.get("completed")),
        "completed_at": task.get("completed_at"),
        "resource_subtype": task.get("resource_subtype"),
        **fields,
    }


def manager_group(region: str, grade_band: str) -> str:
    """Newark managers are by grade band; elsewhere one manager per region."""
    return f"Newark:{grade_band}" if region == "Newark" else region


def build_snapshot(projects, tasks_by_project, region_map, pulled_at) -> dict:
    """Assemble the snapshot dict: one entry per in-scope school with its tasks."""
    schools_cfg = region_map["schools"]
    schools = []
    for proj in filter_projects(projects):
        gid = proj["gid"]
        cfg = schools_cfg.get(gid)
        if cfg is None:
            # In the portfolio but not in region_map — surface, don't silently drop.
            cfg = {"name": proj.get("name"), "region": "UNMAPPED", "grade_band": "?"}
        raw = tasks_by_project.get(gid, [])
        schools.append({
            "gid": gid,
            "name": cfg["name"],
            "region": cfg["region"],
            "grade_band": cfg["grade_band"],
            "manager_group": manager_group(cfg["region"], cfg["grade_band"]),
            "tasks": [task_to_record(t) for t in raw],
        })
    return {
        "meta": {
            "pulled_at": pulled_at,
            "portfolio_gid": region_map.get("_portfolio_gid"),
            "school_count": len(schools),
        },
        "schools": schools,
    }


# ---- API I/O ----------------------------------------------------------------

def paginate(session, url: str, params: dict) -> list[dict]:
    """Follow Asana's next_page offsets, returning the concatenated data rows."""
    rows: list[dict] = []
    params = dict(params)
    while True:
        resp = _get_with_retry(session, url, params)
        payload = resp.json()
        rows.extend(payload.get("data", []))
        nxt = payload.get("next_page")
        if not nxt:
            return rows
        params["offset"] = nxt["offset"]


def _get_with_retry(session, url, params, attempts=5):
    """GET with basic 429/5xx backoff so a full pull survives rate limits."""
    for i in range(attempts):
        resp = session.get(url, params=params, timeout=60)
        status = getattr(resp, "status_code", 200)
        if status == 429 or status >= 500:
            wait = float(resp.headers.get("Retry-After", 2 ** i)) if hasattr(resp, "headers") else 2 ** i
            time.sleep(min(wait, 30))
            continue
        resp.raise_for_status()
        return resp
    resp.raise_for_status()
    return resp


def get_portfolio_items(session, portfolio_gid: str) -> list[dict]:
    return paginate(session, f"{API}/portfolios/{portfolio_gid}/items",
                    {"opt_fields": "name", "limit": 100})


def get_project_tasks(session, project_gid: str) -> list[dict]:
    return paginate(session, f"{API}/projects/{project_gid}/tasks",
                    {"opt_fields": TASK_OPT_FIELDS, "limit": 100})


# ---- entrypoint -------------------------------------------------------------

def _load_env(path=".env"):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


def main():
    import requests  # imported here so pure-function tests don't require it

    _load_env()
    token = os.environ.get("ASANA_TOKEN")
    if not token:
        raise SystemExit("ASANA_TOKEN not set. Copy .env.example to .env and add your token.")
    portfolio_gid = os.environ.get("ASANA_PORTFOLIO_GID", "1214543972018645")

    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "region_map.json"), encoding="utf-8") as f:
        region_map = json.load(f)
    region_map["_portfolio_gid"] = portfolio_gid

    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}"})

    print(f"Pulling portfolio {portfolio_gid} ...")
    items = filter_projects(get_portfolio_items(session, portfolio_gid))
    print(f"  {len(items)} in-scope projects")

    tasks_by_project = {}
    for i, proj in enumerate(items, 1):
        tasks = get_project_tasks(session, proj["gid"])
        tasks_by_project[proj["gid"]] = tasks
        print(f"  [{i}/{len(items)}] {proj['name']}: {len(tasks)} tasks")

    pulled_at = datetime.now(timezone.utc).isoformat()
    snap = build_snapshot(items, tasks_by_project, region_map, pulled_at)

    out = os.path.join(here, "snapshot.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=2)
    total = sum(len(s["tasks"]) for s in snap["schools"])
    print(f"Wrote {out}: {snap['meta']['school_count']} schools, {total} tasks")


if __name__ == "__main__":
    main()
