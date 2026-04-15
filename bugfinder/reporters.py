from __future__ import annotations

import html
import json

from bugfinder.models import AnalysisReport


def render_text(report: AnalysisReport) -> str:
    summary = report.to_dict()["audit_summary"]
    lines = [
        f"BugFinder Report: {report.root_path}",
        f"Files scanned: {report.files_scanned}",
        f"Chunks analyzed: {report.chunks_analyzed}",
        f"AI provider/model: {report.ai_provider}/{report.ai_model or 'n/a'}",
        f"Estimated AI cost (USD): {report.estimated_cost_usd:.6f}",
        f"Total issues: {summary['total_issues']}",
        "",
    ]
    if not report.issues:
        lines.append("No issues found.")
        return "\n".join(lines)

    lines.append("Severity counts: " + ", ".join(f"{k}={v}" for k, v in summary["severity_counts"].items()))
    lines.append("Type counts: " + ", ".join(f"{k}={v}" for k, v in summary["type_counts"].items()))
    lines.append("Source counts: " + ", ".join(f"{k}={v}" for k, v in summary["source_counts"].items()))
    if summary["top_risky_files"]:
        lines.append("Top risky files:")
        for item in summary["top_risky_files"]:
            lines.append(f"  - {item['file']} ({item['issue_count']} issues)")
    lines.append("")
    for idx, issue in enumerate(report.issues, start=1):
        loc = f"{issue.file_path}:{issue.line}" if issue.line else issue.file_path
        lines.append(f"{idx}. [{issue.severity.upper()}] {issue.issue_type} @ {loc}")
        lines.append(f"   {issue.description}")
        if issue.fix:
            lines.append(f"   Fix: {issue.fix}")
        lines.append(f"   Source: {issue.source}")
        lines.append("")
    return "\n".join(lines).strip()


def render_json(report: AnalysisReport) -> str:
    return json.dumps(report.to_dict(), indent=2)


def render_html(report: AnalysisReport) -> str:
    summary = report.to_dict()["audit_summary"]
    rows = []
    for issue in report.issues:
        rows.append(
            "<tr>"
            f"<td>{html.escape(issue.severity)}</td>"
            f"<td>{html.escape(issue.issue_type)}</td>"
            f"<td>{html.escape(issue.file_path)}</td>"
            f"<td>{'' if issue.line is None else issue.line}</td>"
            f"<td>{html.escape(issue.description)}</td>"
            f"<td>{html.escape(issue.fix or '')}</td>"
            f"<td>{html.escape(issue.source)}</td>"
            "</tr>"
        )
    table_rows = "\n".join(rows) if rows else "<tr><td colspan='7'>No issues found.</td></tr>"
    hotspots = "".join(
        f"<li><code>{html.escape(item['file'])}</code> - {item['issue_count']} issues</li>"
        for item in summary["top_risky_files"]
    ) or "<li>No hotspots identified.</li>"
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>BugFinder Report</title>
  <style>
    body {{ font-family: sans-serif; margin: 24px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; vertical-align: top; }}
    th {{ background: #f5f5f5; text-align: left; }}
  </style>
</head>
<body>
  <h1>BugFinder Report</h1>
  <p><strong>Root:</strong> {html.escape(report.root_path)}</p>
  <p><strong>Files scanned:</strong> {report.files_scanned}</p>
  <p><strong>Chunks analyzed:</strong> {report.chunks_analyzed}</p>
  <p><strong>AI:</strong> {html.escape(report.ai_provider)} / {html.escape(report.ai_model or "n/a")}</p>
  <p><strong>Estimated AI cost (USD):</strong> {report.estimated_cost_usd:.6f}</p>
  <h2>Audit Summary</h2>
  <p><strong>Total issues:</strong> {summary['total_issues']}</p>
  <p><strong>Severity:</strong> {html.escape(", ".join(f"{k}={v}" for k, v in summary["severity_counts"].items()) or "none")}</p>
  <p><strong>Types:</strong> {html.escape(", ".join(f"{k}={v}" for k, v in summary["type_counts"].items()) or "none")}</p>
  <p><strong>Sources:</strong> {html.escape(", ".join(f"{k}={v}" for k, v in summary["source_counts"].items()) or "none")}</p>
  <h3>Top Risky Files</h3>
  <ul>
    {hotspots}
  </ul>
  <table>
    <thead>
      <tr>
        <th>Severity</th><th>Type</th><th>File</th><th>Line</th><th>Description</th><th>Fix</th><th>Source</th>
      </tr>
    </thead>
    <tbody>
      {table_rows}
    </tbody>
  </table>
</body>
</html>"""
