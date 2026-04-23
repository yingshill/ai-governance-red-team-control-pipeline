"""Generate a simple HTML report from per-control eval results."""
from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path

_CSS = (
    "body{font-family:system-ui,sans-serif;margin:2rem;}"
    "table{border-collapse:collapse;width:100%;}"
    "th,td{border:1px solid #ddd;padding:.5rem .75rem;text-align:left;}"
    "th{background:#f5f5f5;}"
    ".pass{color:#0a7d2c;font-weight:600;}"
    ".fail{color:#c11;font-weight:600;}"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    reports_dir = Path("reports")
    rows: list[str] = []
    if reports_dir.exists():
        for report_file in sorted(reports_dir.glob("CTRL-*.json")):
            data = json.loads(report_file.read_text())
            m = data["metrics"]
            ok = m["pass_rate"] >= 0.95
            rows.append(
                "<tr>"
                f"<td>{escape(m['control_id'])}</td>"
                f"<td>{m['total']}</td>"
                f"<td>{m['passed']}</td>"
                f"<td>{m['pass_rate']:.2%}</td>"
                f"<td>{m['latency_p50']:.1f}</td>"
                f"<td>{m['latency_p95']:.1f}</td>"
                f"<td class='{'pass' if ok else 'fail'}'>{'PASS' if ok else 'FAIL'}</td>"
                "</tr>"
            )

    html = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>AI Safety Eval Report</title>"
        f"<style>{_CSS}</style></head><body>"
        "<h1>AI Safety Eval Report</h1>"
        f"<p>Generated from <code>{escape(str(args.results))}</code></p>"
        "<table><thead><tr>"
        "<th>Control</th><th>Total</th><th>Passed</th><th>Pass rate</th>"
        "<th>P50 (ms)</th><th>P95 (ms)</th><th>Status</th></tr></thead><tbody>"
        + "\n".join(rows)
        + "</tbody></table></body></html>"
    )

    (args.out / "index.html").write_text(html)
    print(f"Wrote {args.out / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
