"""Assemble a REAL (but sampled) snapshot.json from persisted Asana pulls.

Dev convenience only: builds snapshot.json from 6 schools (one per manager
group), first 100 tasks each, pulled live via the Asana MCP and saved to disk.
Reuses the tested pure functions in snapshot.py. The production path is
`python snapshot.py` with a token, which pulls all 24 schools, fully paginated,
using the same build_snapshot() code.
"""
import json
import os

import snapshot

HERE = os.path.dirname(os.path.abspath(__file__))
TR = r"C:\Users\Jweber\.claude\projects\C--Users-Jweber-Desktop-Claudio-Code-Sessions\b8a06d79-cce3-4af3-997a-0f7643d6f108\tool-results"

# project_gid -> persisted pull file (call order, page 1, limit 100)
FILES = {
    "1214543972018555": "mcp-3ff1e0dd-54eb-4878-9ecc-f70817418e84-get_tasks-1781124888939.txt",  # TEAM (Newark:MS)
    "1214543972018490": "mcp-3ff1e0dd-54eb-4878-9ecc-f70817418e84-get_tasks-1781124890538.txt",  # SPARK (Newark:ES)
    "1214543972018633": "mcp-3ff1e0dd-54eb-4878-9ecc-f70817418e84-get_tasks-1781124893261.txt",  # Lab (Newark:HS)
    "1214566137135725": "mcp-3ff1e0dd-54eb-4878-9ecc-f70817418e84-get_tasks-1781124895413.txt",  # KHS (Camden)
    "1214566137135790": "mcp-3ff1e0dd-54eb-4878-9ecc-f70817418e84-get_tasks-1781124896603.txt",  # KIPP Miami Tech (Miami)
    "1214566137135826": "mcp-3ff1e0dd-54eb-4878-9ecc-f70817418e84-get_tasks-1781124898693.txt",  # Paterson Prep MS (Paterson)
}


def _load_json(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    return json.loads(text[text.index("{"):])  # tolerate any leading header


def main():
    with open(os.path.join(HERE, "region_map.json"), encoding="utf-8") as f:
        region_map = json.load(f)
    cfg = region_map["schools"]

    projects, tasks_by_project = [], {}
    for gid, fname in FILES.items():
        payload = _load_json(os.path.join(TR, fname))
        tasks_by_project[gid] = payload.get("data", [])
        projects.append({"gid": gid, "name": cfg[gid]["name"] + " FY27 Summer Strong Start"})

    snap = snapshot.build_snapshot(projects, tasks_by_project, region_map,
                                   pulled_at="2026-06-10T00:00:00Z")
    snap["meta"]["sample"] = True
    snap["meta"]["sample_note"] = "DEV SAMPLE: 6 schools (one per manager group), first 100 tasks each. Run snapshot.py with a token for the full 24-school snapshot."

    out = os.path.join(HERE, "snapshot.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=2)

    total = sum(len(s["tasks"]) for s in snap["schools"])
    print(f"Wrote {out}")
    for s in snap["schools"]:
        print(f"  {s['name']:<18} {s['region']:<9} {s['manager_group']:<11} {len(s['tasks'])} tasks")
    print(f"Total: {len(snap['schools'])} schools, {total} tasks")


if __name__ == "__main__":
    main()
