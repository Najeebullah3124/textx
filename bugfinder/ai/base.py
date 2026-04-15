from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from bugfinder.models import AnalysisIssue


@dataclass(slots=True)
class AIUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0


class RateLimiter:
    def __init__(self, calls_per_minute: int = 30) -> None:
        self.calls_per_minute = max(1, calls_per_minute)
        self.min_interval = 60.0 / self.calls_per_minute
        self._last_call_time = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        delta = now - self._last_call_time
        if delta < self.min_interval:
            time.sleep(self.min_interval - delta)
        self._last_call_time = time.monotonic()


def parse_llm_json_to_issues(raw_text: str, file_path: str, source: str) -> tuple[list[AnalysisIssue], dict[str, Any]]:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
    payload = json.loads(cleaned)
    issues_data = payload.get("issues", [])
    issues: list[AnalysisIssue] = []
    for item in issues_data:
        issues.append(
            AnalysisIssue(
                issue_type=str(item.get("type", "bug")),
                severity=str(item.get("severity", "medium")),
                description=str(item.get("description", "Issue found by AI analyzer.")),
                file_path=file_path,
                line=item.get("line"),
                fix=item.get("fix"),
                source=source,
            )
        )
    return issues, payload
