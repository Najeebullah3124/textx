from pathlib import Path

from bugfinder.analyzer.generic_analyzer import analyze_generic_file
from bugfinder.analyzer.hybrid_analyzer import HybridAnalyzer


def test_generic_analyzer_flags_todo_fixme_and_hack_independently(tmp_path: Path) -> None:
    sample = tmp_path / "notes.js"
    sample.write_text(
        "// TODO: clean this path\n"
        "// FIXME: edge case remains\n"
        "// HACK: temporary workaround\n",
        encoding="utf-8",
    )

    issues = analyze_generic_file(sample)
    flagged_lines = {issue.line for issue in issues}

    assert {1, 2, 3}.issubset(flagged_lines)


def test_hybrid_analyzer_reports_effective_client_model(tmp_path: Path) -> None:
    analyzer = HybridAnalyzer(ai_provider="none")
    analyzer.client = type("DummyClient", (), {"model": "resolved-model-v1"})()

    report = analyzer.analyze_codebase(str(tmp_path))

    assert report.ai_model == "resolved-model-v1"
