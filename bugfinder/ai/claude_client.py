from __future__ import annotations

import json
from urllib import request

from bugfinder.ai.base import AIUsage, parse_llm_json_to_issues


ANTHROPIC_PRICING_PER_1K = {
    "claude-3-5-sonnet-latest": (0.003, 0.015),
    "claude-3-5-haiku-latest": (0.0008, 0.004),
}


class ClaudeClient:
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-latest", timeout: int = 60) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def analyze_code(self, prompt: str, file_path: str) -> tuple[list, AIUsage]:
        payload = {
            "model": self.model,
            "max_tokens": 1200,
            "temperature": 0.1,
            "messages": [{"role": "user", "content": prompt}],
            "system": "You are a precise code analysis assistant that returns valid JSON only.",
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            "https://api.anthropic.com/v1/messages",
            method="POST",
            data=body,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )
        with request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text_parts = [item.get("text", "") for item in data.get("content", []) if item.get("type") == "text"]
        text = "\n".join(text_parts).strip()
        usage = data.get("usage", {})
        in_tok = int(usage.get("input_tokens", 0))
        out_tok = int(usage.get("output_tokens", 0))
        in_price, out_price = ANTHROPIC_PRICING_PER_1K.get(self.model, (0.003, 0.015))
        cost = (in_tok / 1000.0) * in_price + (out_tok / 1000.0) * out_price
        issues, _ = parse_llm_json_to_issues(text, file_path=file_path, source="ai:claude")
        return issues, AIUsage(input_tokens=in_tok, output_tokens=out_tok, estimated_cost_usd=cost)
