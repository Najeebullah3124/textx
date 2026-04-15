from __future__ import annotations

import json


def build_analysis_prompt(file_path: str, language: str, start_line: int, end_line: int, code: str) -> str:
    schema = {
        "issues": [
            {
                "type": "bug/security/performance/code_smell",
                "severity": "low/medium/high",
                "description": "string",
                "line": 0,
                "fix": "string",
            }
        ],
        "quality_score": 0,
        "summary": "string",
    }
    return (
        "You are a senior software engineer performing deep code audit. Analyze the following code and identify:\n"
        "- Bugs and edge-case failures\n- Security issues and unsafe APIs\n- Performance bottlenecks and complexity risks\n- Reliability and maintainability code smells\n\n"
        "Be precise and actionable. Prefer fewer high-confidence findings over speculative findings.\n"
        "For every issue include:\n"
        "- exact risk\n- why it can fail in production\n- concrete fix that can be implemented\n\n"
        "Return strictly valid JSON only, no markdown.\n"
        f"Expected JSON schema example:\n{json.dumps(schema)}\n\n"
        f"Context: file={file_path}, language={language}, lines={start_line}-{end_line}\n"
        "Code:\n"
        f"```{language}\n"
        f"{code}\n"
        "```"
    )
