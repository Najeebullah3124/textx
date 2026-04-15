from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _summary_table(payload: dict) -> Table:
    audit = payload.get("audit_summary", {})
    severity = ", ".join(f"{k}={v}" for k, v in audit.get("severity_counts", {}).items()) or "none"
    issue_types = ", ".join(f"{k}={v}" for k, v in audit.get("type_counts", {}).items()) or "none"
    sources = ", ".join(f"{k}={v}" for k, v in audit.get("source_counts", {}).items()) or "none"
    rows = [
        ["Root", str(payload.get("root_path", ""))],
        ["Files scanned", str(payload.get("files_scanned", 0))],
        ["AI provider/model", f"{payload.get('ai_provider', 'none')}/{payload.get('ai_model') or 'n/a'}"],
        ["Estimated AI cost (USD)", f"{payload.get('estimated_cost_usd', 0.0):.6f}"],
        ["Total issues", str(audit.get("total_issues", 0))],
        ["Severity", severity],
        ["Types", issue_types],
        ["Sources", sources],
    ]
    table = Table(rows, colWidths=[4.2 * cm, 12.0 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E2E8F0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _issues_table(payload: dict, limit: int = 120) -> Table:
    rows = [["Severity", "Type", "File", "Line", "Description", "Fix"]]
    for issue in payload.get("issues", [])[:limit]:
        rows.append(
            [
                str(issue.get("severity", "")),
                str(issue.get("type", "")),
                str(issue.get("file", "")),
                str(issue.get("line", "")),
                str(issue.get("description", ""))[:180],
                str(issue.get("fix", ""))[:180],
            ]
        )
    if len(rows) == 1:
        rows.append(["-", "-", "-", "-", "No issues found.", "-"])
    table = Table(rows, colWidths=[1.6 * cm, 2.0 * cm, 3.0 * cm, 1.0 * cm, 4.9 * cm, 4.0 * cm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F766E")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8.5),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 7.8),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return table


def build_pdf(input_json: Path, output_pdf: Path) -> None:
    payload = json.loads(input_json.read_text(encoding="utf-8"))
    styles = getSampleStyleSheet()
    title = ParagraphStyle("Title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=21)
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=12.5)

    doc = SimpleDocTemplate(
        str(output_pdf),
        pagesize=A4,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        rightMargin=1.2 * cm,
        title="Complete Audit Report",
    )
    story = [
        Paragraph("Complete Audit Report", title),
        Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", body),
        Spacer(1, 0.2 * cm),
        _summary_table(payload),
        Spacer(1, 0.35 * cm),
        Paragraph("Detailed Issues", styles["Heading2"]),
        Paragraph("The table below includes all findings (or first 120 if very large).", body),
        Spacer(1, 0.15 * cm),
        _issues_table(payload),
    ]
    doc.build(story)


if __name__ == "__main__":
    input_path = Path("complete_audit_report.json")
    output_path = Path("complete_audit_report.pdf")
    build_pdf(input_path, output_path)
    print(f"PDF generated: {output_path.resolve()}")
