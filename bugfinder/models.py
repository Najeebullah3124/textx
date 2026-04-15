from __future__ import annotations

from dataclasses import dataclass, field
from collections import Counter
from typing import Any


@dataclass(slots=True)
class AnalysisIssue:
    issue_type: str
    severity: str
    description: str
    file_path: str
    line: int | None = None
    fix: str | None = None
    source: str = "static"
    confidence: float | None = None

    def key(self) -> tuple[Any, ...]:
        return (
            self.issue_type.strip().lower(),
            self.severity.strip().lower(),
            self.description.strip().lower(),
            self.file_path,
            self.line,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.issue_type,
            "severity": self.severity,
            "description": self.description,
            "file": self.file_path,
            "line": self.line,
            "fix": self.fix,
            "source": self.source,
            "confidence": self.confidence,
        }


@dataclass(slots=True)
class AnalysisReport:
    root_path: str
    issues: list[AnalysisIssue] = field(default_factory=list)
    files_scanned: int = 0
    chunks_analyzed: int = 0
    ai_provider: str = "none"
    ai_model: str | None = None
    estimated_cost_usd: float = 0.0

    def severity_counts(self) -> dict[str, int]:
        counts = Counter(issue.severity.lower() for issue in self.issues)
        return {k: counts[k] for k in sorted(counts)}

    def type_counts(self) -> dict[str, int]:
        counts = Counter(issue.issue_type.lower() for issue in self.issues)
        return {k: counts[k] for k in sorted(counts)}

    def source_counts(self) -> dict[str, int]:
        counts = Counter(issue.source.lower() for issue in self.issues)
        return {k: counts[k] for k in sorted(counts)}

    def top_risky_files(self, limit: int = 5) -> list[dict[str, Any]]:
        counts = Counter(issue.file_path for issue in self.issues)
        ranked = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
        return [{"file": file_path, "issue_count": issue_count} for file_path, issue_count in ranked[:limit]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_path": self.root_path,
            "files_scanned": self.files_scanned,
            "chunks_analyzed": self.chunks_analyzed,
            "ai_provider": self.ai_provider,
            "ai_model": self.ai_model,
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
            "audit_summary": {
                "total_issues": len(self.issues),
                "severity_counts": self.severity_counts(),
                "type_counts": self.type_counts(),
                "source_counts": self.source_counts(),
                "top_risky_files": self.top_risky_files(),
            },
            "issues": [issue.to_dict() for issue in self.issues],
        }
