from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


@dataclass(slots=True)
class Config:
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    default_provider: str = "none"
    default_model: str | None = None
    max_cost: float = 10.0
    rate_limit_per_minute: int = 30


def load_config(config_path: str | None = None) -> Config:
    env_openai = os.getenv("OPENAI_API_KEY")
    env_anthropic = os.getenv("ANTHROPIC_API_KEY")
    config = Config(
        openai_api_key=env_openai,
        anthropic_api_key=env_anthropic,
    )

    path = Path(config_path) if config_path else Path(".bugfinder.toml")
    if path.exists() and tomllib is not None:
        with path.open("rb") as f:
            data = tomllib.load(f)
        ai_cfg = data.get("ai", {})
        config.openai_api_key = ai_cfg.get("openai_api_key", config.openai_api_key)
        config.anthropic_api_key = ai_cfg.get("anthropic_api_key", config.anthropic_api_key)
        config.default_provider = ai_cfg.get("default_provider", config.default_provider)
        config.default_model = ai_cfg.get("default_model", config.default_model)
        config.max_cost = float(ai_cfg.get("max_cost", config.max_cost))
        config.rate_limit_per_minute = int(ai_cfg.get("rate_limit_per_minute", config.rate_limit_per_minute))

    return config
