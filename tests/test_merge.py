from bugfinder.analyzer.hybrid_analyzer import HybridAnalyzer
from bugfinder.models import AnalysisIssue


def test_merge_issues_deduplicates() -> None:
    issues = [
        AnalysisIssue("bug", "high", "same", "a.py", 10),
        AnalysisIssue("bug", "high", "same", "a.py", 10),
        AnalysisIssue("bug", "high", "different", "a.py", 10),
    ]
    merged = HybridAnalyzer._merge_issues(issues)
    assert len(merged) == 2
