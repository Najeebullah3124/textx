import json
from pathlib import Path

from bugfinder.analyzer.ast_analyzer import analyze_file_with_ast
from bugfinder.analyzer.generic_analyzer import analyze_generic_file
from bugfinder.models import AnalysisIssue, AnalysisReport
from bugfinder.reporters import render_json


def test_ast_analyzer_flags_subprocess_shell_true(tmp_path: Path) -> None:
    file_path = tmp_path / "unsafe.py"
    file_path.write_text(
        "import subprocess\n"
        "def run(cmd: str) -> None:\n"
        "    subprocess.run(cmd, shell=True)\n",
        encoding="utf-8",
    )

    issues = analyze_file_with_ast(file_path)
    assert any("shell=True" in issue.description for issue in issues)


def test_generic_analyzer_flags_hardcoded_secret_pattern(tmp_path: Path) -> None:
    file_path = tmp_path / "config.js"
    file_path.write_text('const apiKey = "123456789abcdef";\n', encoding="utf-8")

    issues = analyze_generic_file(file_path)
    assert any(issue.issue_type == "security" and issue.severity == "high" for issue in issues)


def test_report_json_contains_audit_summary() -> None:
    report = AnalysisReport(
        root_path=".",
        issues=[
            AnalysisIssue("security", "high", "x", "a.py", 1),
            AnalysisIssue("bug", "medium", "y", "a.py", 2),
            AnalysisIssue("bug", "low", "z", "b.py", 3, source="ai:openai"),
        ],
        files_scanned=2,
    )

    payload = json.loads(render_json(report))
    assert payload["audit_summary"]["total_issues"] == 3
    assert payload["audit_summary"]["severity_counts"]["high"] == 1
    assert payload["audit_summary"]["top_risky_files"][0]["file"] == "a.py"
