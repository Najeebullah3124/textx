from __future__ import annotations

from dataclasses import dataclass, field

from bugfinder.analyzer.hybrid_analyzer import HybridAnalyzer, SEVERITY_RANK
from bugfinder.config import load_config
from bugfinder.models import AnalysisReport
from bugfinder.reporters import render_html, render_json, render_text


@dataclass(slots=True)
class AuditOptions:
    ai_provider: str | None = None
    model: str | None = None
    max_cost: float | None = None
    cache_db: str = ".bugfinder_cache.sqlite3"
    config_path: str | None = None
    exclude_dirs: set[str] = field(default_factory=set)
    include_extensions: set[str] = field(default_factory=set)
    min_severity: str | None = None


def run_audit(path: str, options: AuditOptions | None = None) -> AnalysisReport:
    opts = options or AuditOptions()
    cfg = load_config(opts.config_path)
    provider = opts.ai_provider if opts.ai_provider is not None else cfg.default_provider
    model = opts.model if opts.model is not None else cfg.default_model
    max_cost = opts.max_cost if opts.max_cost is not None else cfg.max_cost

    analyzer = HybridAnalyzer(
        ai_provider=provider,
        model=model,
        openai_api_key=cfg.openai_api_key,
        anthropic_api_key=cfg.anthropic_api_key,
        max_cost=max_cost,
        cache_db=opts.cache_db,
        rate_limit_per_minute=cfg.rate_limit_per_minute,
    )
    exclude_dirs = opts.exclude_dirs or None
    include_extensions = opts.include_extensions or None
    return analyzer.analyze_codebase(
        path,
        exclude_dirs=exclude_dirs,
        include_extensions=include_extensions,
        min_severity=opts.min_severity,
    )


def render_report(report: AnalysisReport, output: str = "text") -> str:
    if output == "json":
        return render_json(report)
    if output == "html":
        return render_html(report)
    return render_text(report)


def should_fail_ci(report: AnalysisReport, fail_on_severity: str | None) -> bool:
    if not fail_on_severity:
        return False
    threshold = SEVERITY_RANK.get(fail_on_severity.lower())
    if threshold is None:
        return False
    for issue in report.issues:
        if SEVERITY_RANK.get(issue.severity.lower(), 0) >= threshold:
            return True
    return False
