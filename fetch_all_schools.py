import urllib.request
import json
import os
import sys
import time

SCHOOLS = [
    {"name": "KURA",             "gid": "1214543972018542", "cohort": "Newark ES"},
    {"name": "Life",             "gid": "1214543972018529", "cohort": "Newark ES"},
    {"name": "Seek",             "gid": "1214543972018516", "cohort": "Newark ES"},
    {"name": "SPARK",            "gid": "1214543972018490", "cohort": "Newark ES"},
    {"name": "THRIVE",           "gid": "1214543972018503", "cohort": "Newark ES"},
    {"name": "BOLD",             "gid": "1214543972018581", "cohort": "Newark MS"},
    {"name": "Justice",          "gid": "1214543972018607", "cohort": "Newark MS"},
    {"name": "Purpose",          "gid": "1214543972018594", "cohort": "Newark MS"},
    {"name": "Rise",             "gid": "1214543972018568", "cohort": "Newark MS"},
    {"name": "TEAM",             "gid": "1214543972018555", "cohort": "Newark MS"},
    {"name": "Lab",              "gid": "1214543972018633", "cohort": "Newark HS"},
    {"name": "NCA",              "gid": "1214543972018620", "cohort": "Newark HS"},
    {"name": "Hatch",            "gid": "1214566137135712", "cohort": "Camden K-12"},
    {"name": "KHS",              "gid": "1214566137135725", "cohort": "Camden K-12"},
    {"name": "LSM",              "gid": "1214566202106004", "cohort": "Camden K-12"},
    {"name": "LSP",              "gid": "1214566202106030", "cohort": "Camden K-12"},
    {"name": "Sumner",           "gid": "1214566202106017", "cohort": "Camden K-12"},
    {"name": "KCA",              "gid": "1214566137135751", "cohort": "Miami K-12"},
    {"name": "KIPP Miami Tech",  "gid": "1214566137135790", "cohort": "Miami K-12"},
    {"name": "KRA",              "gid": "1214566137135738", "cohort": "Miami K-12"},
    {"name": "Legacy ES",        "gid": "1214566137135764", "cohort": "Miami K-12"},
    {"name": "Legacy MS",        "gid": "1214566137135777", "cohort": "Miami K-12"},
    {"name": "Paterson Prep ES", "gid": "1214566137135813", "cohort": "Paterson K-8"},
    {"name": "Paterson Prep MS", "gid": "1214566137135826", "cohort": "Paterson K-8"},
]

STOCK_FIELD = "1214472577362529"
STOCK_VALUE = "1214472577362530"


def load_token():
    token = os.environ.get("ASANA_TOKEN") or os.environ.get("ASANA_PAT", "")
    if token:
        return token
    candidates = [
        r"C:\Users\Jweber\Desktop\Claudio\Code Sessions\strong-start-dashboard\.env",
        os.path.expanduser("~/.env"),
    ]
    for path in candidates:
        try:
            for line in open(path):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() in ("ASANA_TOKEN", "ASANA_PAT"):
                        return v.strip()
        except OSError:
            pass
    return ""


def asana_get(url, token, retries=5):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
        except (ConnectionResetError, ConnectionError, OSError) as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise


def fetch_school(school, today, token):
    seen = set()
    tasks = []
    url = (
        "https://app.asana.com/api/1.0/tasks"
        "?project=" + school["gid"] +
        "&opt_fields=gid,completed,due_on,custom_fields&limit=100"
    )
    while url:
        data = asana_get(url, token)
        for t in data.get("data", []):
            if t["gid"] not in seen:
                seen.add(t["gid"])
                tasks.append(t)
        nxt = data.get("next_page")
        url = (
            "https://app.asana.com/api/1.0/tasks"
            "?project=" + school["gid"] +
            "&opt_fields=gid,completed,due_on,custom_fields&limit=100"
            "&offset=" + nxt["offset"]
        ) if nxt else None

    stock = [
        t for t in tasks
        if any(
            f.get("gid") == STOCK_FIELD
            and f.get("enum_value")
            and f["enum_value"].get("gid") == STOCK_VALUE
            for f in t.get("custom_fields", [])
        )
    ]
    expected = [t for t in stock if t.get("due_on") and t["due_on"] <= today]
    completed = [t for t in expected if t.get("completed")]
    overdue   = [t for t in expected if not t.get("completed")]

    return {
        "name":              school["name"],
        "totalStockList":    len(stock),
        "expectedTasks":     len(expected),
        "completedExpected": len(completed),
        "overdueTasks":      len(overdue),
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python fetch_all_schools.py <YYYY-MM-DD> [output.json]", file=sys.stderr)
        sys.exit(1)

    today = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else "school_data.json"

    token = load_token()
    if not token:
        print("ERROR: no ASANA_TOKEN found", file=sys.stderr)
        sys.exit(1)

    results = []
    for i, school in enumerate(SCHOOLS, 1):
        print(f"  [{i}/{len(SCHOOLS)}] {school['name']}...", file=sys.stderr)
        results.append(fetch_school(school, today, token))

    with open(out_path, "w") as f:
        json.dump(results, f)

    print(f"Wrote {len(results)} schools to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
