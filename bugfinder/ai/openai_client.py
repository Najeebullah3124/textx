from __future__ import annotations

import json
from urllib import request

from bugfinder.ai.base import AIUsage, parse_llm_json_to_issues


OPENAI_PRICING_PER_1K = {
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4o": (0.005, 0.015),
}


class OpenAIClient:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", timeout: int = 60) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def analyze_code(self, prompt: str, file_path: str) -> tuple[list, AIUsage]:
        payload = {
            "model": self.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "You are a precise code analysis assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            "https://api.openai.com/v1/chat/completions",
            method="POST",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        with request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        in_tok = int(usage.get("prompt_tokens", 0))
        out_tok = int(usage.get("completion_tokens", 0))
        in_price, out_price = OPENAI_PRICING_PER_1K.get(self.model, (0.001, 0.003))
        cost = (in_tok / 1000.0) * in_price + (out_tok / 1000.0) * out_price
        issues, _ = parse_llm_json_to_issues(text, file_path=file_path, source="ai:openai")
        return issues, AIUsage(input_tokens=in_tok, output_tokens=out_tok, estimated_cost_usd=cost)
