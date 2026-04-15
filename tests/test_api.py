from pathlib import Path

from bugfinder.api import AuditOptions, run_audit, should_fail_ci
from bugfinder.models import AnalysisIssue, AnalysisReport


def test_run_audit_respects_include_extensions(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / "bad.js").write_text("const apiKey = \"abcdefghi12345\";\n", encoding="utf-8")

    report = run_audit(
        str(tmp_path),
        AuditOptions(
            ai_provider="none",
            include_extensions={".py"},
        ),
    )

    assert all(issue.file_path.endswith(".py") for issue in report.issues)


def test_run_audit_applies_min_severity_filter(tmp_path: Path) -> None:
    sample = tmp_path / "notes.js"
    sample.write_text("console.log('debug')\n", encoding="utf-8")

    report = run_audit(
        str(tmp_path),
        AuditOptions(
            ai_provider="none",
            min_severity="high",
        ),
    )

    assert report.issues == []


def test_should_fail_ci_threshold() -> None:
    report = AnalysisReport(
        root_path=".",
        issues=[
            AnalysisIssue("bug", "low", "a", "x.py", 1),
            AnalysisIssue("security", "high", "b", "y.py", 2),
        ],
    )
    assert should_fail_ci(report, "high") is True
    assert should_fail_ci(report, "medium") is True
    assert should_fail_ci(report, "low") is True
    assert should_fail_ci(report, None) is False
