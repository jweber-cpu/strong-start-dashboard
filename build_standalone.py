"""Build a single self-contained dashboard.html (inlines app.js + metrics.js).

Produces one portable file that opens in any browser with no other files and no
server — suitable for emailing, dropping in SharePoint/Notion, attaching to a
Claude Project, or pasting as a Claude artifact. Data is frozen at the last
`python metrics.py` run.

Usage:  python build_standalone.py        (after snapshot.py + metrics.py)
Output: dashboard.html
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))


def _read(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return f.read()


def main():
    html = _read("index.html")
    for src in ("metrics.js", "app.js"):
        path = os.path.join(HERE, src)
        if not os.path.exists(path):
            raise SystemExit(f"Missing {src}. Run: python snapshot.py && python metrics.py")
        inline = "<script>\n" + _read(src) + "\n</script>"
        # replace <script src="metrics.js"></script> (allow attribute/space variations)
        pattern = re.compile(r'<script[^>]*\ssrc=["\']' + re.escape(src) + r'["\'][^>]*>\s*</script>')
        html, n = pattern.subn(inline, html)
        if n == 0:
            raise SystemExit(f"Could not find <script src=\"{src}\"> tag in index.html")

    out = os.path.join(HERE, "dashboard.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    size = os.path.getsize(out) // 1024
    print(f"Wrote {out} ({size} KB) — self-contained, opens with no other files.")


if __name__ == "__main__":
    main()
