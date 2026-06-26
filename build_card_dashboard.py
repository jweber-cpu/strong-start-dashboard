"""Build the card-based FY27 Summer Strong Start dashboard.

Reads school_data.json (output of fetch_all_schools.py) and writes index.html.

Usage:
    python build_card_dashboard.py YYYY-MM-DD
"""
import json
import os
import sys

SCHOOLS = [
    {"name": "KURA",             "cohort": "Newark ES"},
    {"name": "Life",             "cohort": "Newark ES"},
    {"name": "Seek",             "cohort": "Newark ES"},
    {"name": "SPARK",            "cohort": "Newark ES"},
    {"name": "THRIVE",           "cohort": "Newark ES"},
    {"name": "BOLD",             "cohort": "Newark MS"},
    {"name": "Justice",          "cohort": "Newark MS"},
    {"name": "Purpose",          "cohort": "Newark MS"},
    {"name": "Rise",             "cohort": "Newark MS"},
    {"name": "TEAM",             "cohort": "Newark MS"},
    {"name": "Lab",              "cohort": "Newark HS"},
    {"name": "NCA",              "cohort": "Newark HS"},
    {"name": "Hatch",            "cohort": "Camden K-12"},
    {"name": "KHS",              "cohort": "Camden K-12"},
    {"name": "LSM",              "cohort": "Camden K-12"},
    {"name": "LSP",              "cohort": "Camden K-12"},
    {"name": "Sumner",           "cohort": "Camden K-12"},
    {"name": "KCA",              "cohort": "Miami K-12"},
    {"name": "KIPP Miami Tech",  "cohort": "Miami K-12"},
    {"name": "KRA",              "cohort": "Miami K-12"},
    {"name": "Legacy ES",        "cohort": "Miami K-12"},
    {"name": "Legacy MS",        "cohort": "Miami K-12"},
    {"name": "Paterson Prep ES", "cohort": "Paterson K-8"},
    {"name": "Paterson Prep MS", "cohort": "Paterson K-8"},
]

COHORT_ORDER = ["Newark ES", "Newark MS", "Newark HS", "Camden K-12", "Miami K-12", "Paterson K-8"]
COHORT_COLORS = {
    "Newark ES":    "#EE3C37",
    "Newark MS":    "#F9A21A",
    "Newark HS":    "#4CAF50",
    "Camden K-12":  "#57C0E9",
    "Miami K-12":   "#001E62",
    "Paterson K-8": "#9B59B6",
}

MONTHS = ["January","February","March","April","May","June",
          "July","August","September","October","November","December"]


def pct(num, denom):
    if not denom:
        return "0%"
    return str(round((num / denom) * 100)) + "%"


def school_card(s):
    on_track     = s["overdueTasks"] == 0
    status_color = "#22a55b" if on_track else "#EE3C37"
    status_text  = "On track" if on_track else "Off track"
    actual_color = "#22a55b" if on_track else "#EE3C37"
    overdue_color = "#EE3C37" if s["overdueTasks"] > 0 else "#555"

    return (
        f'<div style="background:#fff;border-radius:8px;box-shadow:0 1px 4px rgba(0,0,0,.10);'
        f'border-left:4px solid {status_color};padding:16px 18px;min-width:180px;flex:1 1 180px;max-width:240px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">'
        f'<span style="font-weight:700;font-size:15px;color:#222;">{s["name"]}</span>'
        f'<span style="font-size:12px;color:#888;">{s["totalStockList"]} tasks</span>'
        f'</div>'
        f'<div style="margin-bottom:12px;">'
        f'<span style="display:inline-block;background:{status_color}20;color:{status_color};'
        f'border-radius:12px;padding:2px 10px;font-size:12px;font-weight:600;">'
        f'<span style="display:inline-block;width:7px;height:7px;border-radius:50%;'
        f'background:{status_color};margin-right:5px;vertical-align:middle;"></span>'
        f'{status_text}</span></div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:4px;">'
        f'<div><div style="font-size:10px;color:#888;line-height:1.3;">Expected<br>Tasks</div>'
        f'<div style="font-weight:700;font-size:15px;color:#333;">{s["expectedTasks"]}</div></div>'
        f'<div><div style="font-size:10px;color:#888;line-height:1.3;">Expected<br>%</div>'
        f'<div style="font-weight:700;font-size:15px;color:#333;">{pct(s["expectedTasks"], s["totalStockList"])}</div></div>'
        f'<div><div style="font-size:10px;color:#888;line-height:1.3;">Actual<br>%</div>'
        f'<div style="font-weight:700;font-size:15px;color:{actual_color};">{pct(s["completedExpected"], s["totalStockList"])}</div></div>'
        f'<div><div style="font-size:10px;color:#888;line-height:1.3;">Overdue<br>Tasks</div>'
        f'<div style="font-weight:700;font-size:15px;color:{overdue_color};">{s["overdueTasks"]}</div></div>'
        f'</div></div>'
    )


def cohort_section(cohort_name, schools):
    color = COHORT_COLORS.get(cohort_name, "#555")
    cards = "\n".join(school_card(s) for s in schools)
    return (
        f'<div style="margin-bottom:28px;">'
        f'<div style="margin-bottom:12px;">'
        f'<span style="display:inline-block;background:{color};color:#fff;border-radius:12px;'
        f'padding:4px 14px;font-size:13px;font-weight:700;">{cohort_name}</span>'
        f'</div>'
        f'<div style="display:flex;flex-wrap:wrap;gap:12px;">{cards}</div>'
        f'</div>'
    )


def build_html(school_data, today):
    parts = today.split("-")
    display_date = f"{MONTHS[int(parts[1]) - 1]} {int(parts[2])}, {parts[0]}"

    by_name = {s["name"]: s for s in school_data}
    on_track_count  = sum(1 for s in school_data if s["overdueTasks"] == 0)
    off_track_count = sum(1 for s in school_data if s["overdueTasks"] > 0)

    sections = []
    for cohort_name in COHORT_ORDER:
        schools = [by_name[s["name"]] for s in SCHOOLS
                   if s["cohort"] == cohort_name and s["name"] in by_name]
        if schools:
            sections.append(cohort_section(cohort_name, schools))

    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>FY27 Summer Strong Start Dashboard</title>'
        '<style>*{box-sizing:border-box;margin:0;padding:0;}'
        'body{font-family:Calibri,Verdana,sans-serif;background:#f4f5f7;color:#333;}'
        '.header{background:#001E62;padding:20px 32px;display:flex;justify-content:space-between;align-items:center;}'
        '.header-left{display:flex;align-items:center;gap:14px;}'
        '.k-mark{width:38px;height:38px;background:#EE3C37;border-radius:6px;display:flex;align-items:center;'
        'justify-content:center;font-weight:900;font-size:22px;color:#fff;font-family:Georgia,serif;}'
        '.header h1{color:#fff;font-size:20px;font-weight:700;line-height:1.2;}'
        '.header p{color:#aac4e8;font-size:13px;margin-top:2px;}'
        '.date-chip{background:#ffffff22;color:#fff;border-radius:6px;padding:6px 14px;font-size:13px;white-space:nowrap;}'
        '.summary{display:flex;gap:16px;padding:20px 32px;flex-wrap:wrap;}'
        '.stat-card{background:#fff;border-radius:8px;box-shadow:0 1px 4px rgba(0,0,0,.08);padding:16px 24px;min-width:160px;flex:1;}'
        '.stat-card .label{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:#888;font-weight:600;}'
        '.stat-card .value{font-size:32px;font-weight:800;margin-top:4px;color:#222;}'
        '.stat-card .value.green{color:#22a55b;}.stat-card .value.red{color:#EE3C37;}'
        '.content{padding:8px 32px 32px;}'
        '.footer{padding:16px 32px;font-size:11px;color:#999;border-top:1px solid #e5e7eb;margin-top:8px;line-height:1.7;}'
        '</style></head><body>'
        '<div class="header">'
        '<div class="header-left">'
        '<div class="k-mark">K</div>'
        '<div>'
        '<h1>FY27 Summer Strong Start &ndash; <em>are we on pace for strong first days of school?</em></h1>'
        '<p>Progress monitoring dashboard &middot; Stock List tasks only</p>'
        '</div></div>'
        f'<div class="date-chip">Data as of {display_date}</div>'
        '</div>'
        '<div class="summary">'
        f'<div class="stat-card"><div class="label">Total Schools</div><div class="value">{len(school_data)}</div></div>'
        f'<div class="stat-card"><div class="label">On Track</div><div class="value green">{on_track_count}</div></div>'
        f'<div class="stat-card"><div class="label">Off Track</div><div class="value red">{off_track_count}</div></div>'
        '<div class="stat-card"><div class="label">Checklist Window</div>'
        '<div class="value" style="font-size:18px;margin-top:8px;">Jun 5 &ndash; Aug 14</div></div>'
        '</div>'
        f'<div class="content">{"".join(sections)}</div>'
        '<div class="footer">'
        f'Data pulled from Asana &middot; {display_date} &middot; Stock List tasks only<br>'
        'Expected % = tasks due on or before today &divide; total Stock List tasks &nbsp;&middot;&nbsp;'
        'Actual % = completed expected tasks &divide; total Stock List tasks &nbsp;&middot;&nbsp;'
        'On Track = zero overdue tasks'
        '</div></body></html>'
    )


def main():
    if len(sys.argv) < 2:
        print("Usage: python build_card_dashboard.py YYYY-MM-DD", file=sys.stderr)
        sys.exit(1)

    today = sys.argv[1]
    here  = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(here, "school_data.json"), encoding="utf-8") as f:
        school_data = json.load(f)

    html = build_html(school_data, today)
    out  = os.path.join(here, "index.html")

    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Wrote {out} ({len(html) // 1024} KB) — {len(school_data)} schools, data as of {today}")


if __name__ == "__main__":
    main()
