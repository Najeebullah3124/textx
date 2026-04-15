from __future__ import annotations

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_pdf(output_path: Path) -> None:
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        title="Bug Audit and Fix Plan",
        author="testx analysis",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=24,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=14,
    )
    subtitle_style = ParagraphStyle(
        "SubtitleCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#334155"),
        leading=14,
        spaceAfter=18,
    )
    h2 = ParagraphStyle(
        "H2Custom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=8,
        spaceAfter=8,
    )
    body = ParagraphStyle(
        "BodyCustom",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor("#0F172A"),
    )
    code = ParagraphStyle(
        "CodeCustom",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#111827"),
        backColor=colors.HexColor("#F8FAFC"),
        borderColor=colors.HexColor("#CBD5E1"),
        borderWidth=0.5,
        borderPadding=6,
        borderRadius=3,
    )

    story = []
    story.append(Paragraph("Bug Audit and Fix Plan", title_style))
    story.append(
        Paragraph(
            "Project: <b>testx</b><br/>"
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}<br/>"
            "Scope: code review + test run + static scan",
            subtitle_style,
        )
    )

    summary_data = [
        ["Metric", "Result"],
        ["Automated tests", "5 passed"],
        ["Static scanner output", "No issues reported (false-negative risk confirmed)"],
        ["High-confidence logic bugs found", "2"],
    ]
    summary_table = Table(summary_data, colWidths=[7.2 * cm, 8.4 * cm])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0EA5E9")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
                ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#CBD5E1")),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 0.35 * cm))

    story.append(Paragraph("Bug 1 - Generic Analyzer Misses TODO/FIXME/HACK", h2))
    story.append(
        Paragraph(
            "What needs to fix: detection logic currently flags a comment only when "
            "<b>TODO</b> and one of <b>FIXME/HACK</b> exist on the same line. "
            "This creates false negatives and hides unfinished risky paths.",
            body,
        )
    )
    story.append(
        Paragraph(
            "Current condition:<br/>if &quot;todo&quot; in lower and (&quot;fixme&quot; in lower or &quot;hack&quot; in lower):",
            code,
        )
    )
    story.append(
        Paragraph(
            "How it will work after fix: trigger when <b>any</b> of TODO/FIXME/HACK is present. "
            "That means each marker is treated as a valid warning signal and the scanner "
            "will report incomplete risky code more reliably.",
            body,
        )
    )
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("Bug 2 - Reported AI Model Can Be Incorrect", h2))
    story.append(
        Paragraph(
            "What needs to fix: final report stores <b>self.model</b>, but runtime clients may "
            "silently choose defaults (for example gpt-4o-mini). If user omits --model, output "
            "can show null instead of actual model used.",
            body,
        )
    )
    story.append(
        Paragraph(
            "Current report field:<br/>ai_model=self.model",
            code,
        )
    )
    story.append(
        Paragraph(
            "How it will work after fix: use the resolved client model in reports, such as "
            "<b>self.client.model</b> when AI is enabled. This makes cost traces, caching keys, "
            "and audit output consistent with real execution.",
            body,
        )
    )
    story.append(Spacer(1, 0.45 * cm))

    story.append(Paragraph("Recommended Patch Logic", h2))
    story.append(
        Paragraph(
            "1) In generic analyzer, replace AND logic with OR logic for TODO/FIXME/HACK markers.<br/>"
            "2) In hybrid analyzer report, emit effective model from active client.<br/>"
            "3) Add regression tests for both behaviors.",
            body,
        )
    )

    doc.build(story)


if __name__ == "__main__":
    output = Path("bug_fix_report.pdf")
    build_pdf(output)
    print(f"PDF generated: {output.resolve()}")
