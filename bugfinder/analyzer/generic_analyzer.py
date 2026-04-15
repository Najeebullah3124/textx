from __future__ import annotations

from pathlib import Path
import re

from bugfinder.models import AnalysisIssue

HARD_CODED_SECRET_PATTERN = re.compile(
    r"(api[_-]?key|secret|token|passwd|password)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
    re.IGNORECASE,
)

PRIVATE_KEY_MARKERS = (
    "-----begin private key-----",
    "-----begin rsa private key-----",
    "-----begin openssh private key-----",
)


def analyze_generic_file(file_path: Path) -> list[AnalysisIssue]:
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    rel = str(file_path)
    if not text.strip():
        return []

    lines = text.splitlines()
    issues: list[AnalysisIssue] = []
    for idx, line in enumerate(lines, start=1):
        lower = line.lower()
        if "todo" in lower or "fixme" in lower or "hack" in lower:
            issues.append(
                AnalysisIssue(
                    issue_type="code_smell",
                    severity="low",
                    description="TODO/FIXME/HACK marker indicates unfinished risky code path.",
                    file_path=rel,
                    line=idx,
                    fix="Track this item in issue management and complete or remove it.",
                    source="static",
                )
            )
        if "password" in lower and ("=" in line or ":" in line):
            issues.append(
                AnalysisIssue(
                    issue_type="security",
                    severity="medium",
                    description="Potential hardcoded password/secret assignment.",
                    file_path=rel,
                    line=idx,
                    fix="Load secrets from environment variables or secret manager.",
                    source="static",
                )
            )
        if HARD_CODED_SECRET_PATTERN.search(line):
            issues.append(
                AnalysisIssue(
                    issue_type="security",
                    severity="high",
                    description="Potential hardcoded credential/token detected.",
                    file_path=rel,
                    line=idx,
                    fix="Move secrets to environment variables or a dedicated secret manager.",
                    source="static",
                )
            )
        if any(marker in lower for marker in PRIVATE_KEY_MARKERS):
            issues.append(
                AnalysisIssue(
                    issue_type="security",
                    severity="high",
                    description="Private key material appears to be committed in source.",
                    file_path=rel,
                    line=idx,
                    fix="Remove key material from source control and rotate affected credentials.",
                    source="static",
                )
            )
        if "console.log(" in lower or "debugger;" in lower:
            issues.append(
                AnalysisIssue(
                    issue_type="code_smell",
                    severity="low",
                    description="Debug logging or debugger statement found in source.",
                    file_path=rel,
                    line=idx,
                    fix="Remove debug statements from production code paths.",
                    source="static",
                )
            )
    return issues
