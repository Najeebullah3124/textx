# textx Architecture

This document describes the internal architecture of `textx`, including component boundaries, runtime flow, data contracts, and operational behavior.

## 1. System Goals

- Provide reliable static bug and security detection with zero external dependencies.
- Add optional AI-powered deeper reasoning when users allow outbound calls.
- Keep analysis economically predictable via cost guardrails and caching.
- Emit structured results for both humans and automation.

## 2. High-Level Topology

`textx` is a local-first CLI analyzer with modular layers:

1. **Interface Layer**
   - CLI argument handling and output selection.
2. **Configuration Layer**
   - env/TOML merge with safe defaults.
3. **Discovery Layer**
   - source enumeration with extension filtering and ignore set.
4. **Analysis Layer**
   - static analyzers + optional AI analyzers.
5. **Aggregation Layer**
   - issue normalization, deduplication, summary generation.
6. **Presentation Layer**
   - text, JSON, HTML report renderers.

## 3. Runtime Sequence

### 3.1 CLI Entry

- File: `bugfinder/cli.py`
- Parser exposes `scan` subcommand and analysis/output options.
- Loads config using `load_config`.
- Instantiates `HybridAnalyzer`.
- Invokes `analyze_codebase`.
- Routes final report through renderer and optional file output.

### 3.2 Configuration

- File: `bugfinder/config.py`
- `Config` dataclass stores AI and budget settings.
- `load_config` resolution:
  1. environment (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`)
  2. TOML (`.bugfinder.toml` or `--config`)
- Defaults provide safe offline operation (`default_provider="none"`).

### 3.3 File Discovery

- File: `bugfinder/scanner.py`
- `scan_source_files` recursively discovers files from root path.
- Filters:
  - excluded directories (`.venv`, `node_modules`, caches, build outputs, etc.)
  - supported extensions set
- `chunk_source_file`:
  - Python: AST-aware top-level class/function chunking
  - Non-Python: fixed-size line chunking fallback

### 3.4 Static Analysis

- **Python AST analyzer** (`bugfinder/analyzer/ast_analyzer.py`)
  - Detects:
    - dynamic execution (`eval`, `exec`)
    - bare and broad exception catches
    - mutable defaults
    - potential unreachable code
    - unsafe subprocess `shell=True`
    - unsafe `yaml.load` patterns
    - runtime `assert` misuse
- **Generic analyzer** (`bugfinder/analyzer/generic_analyzer.py`)
  - Detects:
    - TODO/FIXME/HACK markers
    - debug artifacts (`console.log`, `debugger`)
    - hardcoded password/secret/token patterns
    - private key headers

### 3.5 AI Analysis (Optional)

- Orchestrator: `bugfinder/analyzer/hybrid_analyzer.py`
- Provider adapters:
  - `bugfinder/ai/openai_client.py`
  - `bugfinder/ai/claude_client.py`
- Prompt builder:
  - `bugfinder/ai/prompt_builder.py`
- Flow per chunk:
  1. Build cache key from provider/model/file/content hash.
  2. Return cached issues when available.
  3. Enforce rate limiter wait.
  4. Request provider.
  5. Parse strict JSON payload into normalized `AnalysisIssue`.
  6. Update cost and persist cache entry.

### 3.6 Aggregation and Reporting

- Data model: `bugfinder/models.py`
  - `AnalysisIssue`: issue contract
  - `AnalysisReport`: global report + computed summaries
- Dedup key dimensions:
  - type, severity, description, file, line
- Reporter module: `bugfinder/reporters.py`
  - `render_text`
  - `render_json`
  - `render_html`

## 4. Data Contracts

## 4.1 AnalysisIssue

Fields:

- `issue_type`
- `severity`
- `description`
- `file_path`
- `line` (optional)
- `fix` (optional)
- `source`
- `confidence` (optional)

## 4.2 AnalysisReport

Core fields:

- `root_path`
- `issues`
- `files_scanned`
- `chunks_analyzed`
- `ai_provider`
- `ai_model`
- `estimated_cost_usd`

Computed summary:

- `total_issues`
- `severity_counts`
- `type_counts`
- `source_counts`
- `top_risky_files`

## 5. Performance and Cost Controls

- **Rate limiting**
  - `RateLimiter` enforces call spacing based on calls/minute.
- **Budget cutoff**
  - `max_cost` halts chunk analysis once estimated spend is reached.
- **Cache**
  - SQLite persistence avoids re-analyzing unchanged chunks.
  - Key structure includes provider + model + file + content hash.

## 6. Error Handling Strategy

- Provider failures are converted into low-severity system issues, preserving full scan continuity.
- Syntax errors in Python files are surfaced as high-severity static issues.
- Unsupported or empty files are ignored safely.

## 7. Security Model

- No hard dependency on AI; offline mode available.
- API keys loaded from process environment/config and not printed by core logic.
- Secret and private-key heuristics included in static checks.
- Recommended to run publishing workflows with restricted CI environments.

## 8. Test Architecture

Tests under `tests/` validate:

- chunking and scanning
- cache behavior
- dedup behavior
- deep-audit regression checks

This suite validates core deterministic behavior; provider integration tests are typically run manually with controlled credentials.

## 9. Extension Points

Primary extension seams:

- add new static rules in analyzer visitors
- introduce language-specific analyzers and route by extension
- add new AI provider adapters implementing `analyze_code`
- add output renderer (for example SARIF or markdown)
- add richer scoring/confidence pipeline in `models.py`

## 10. Known Constraints

- Single-process execution model (no worker pool yet).
- Generic analyzer rules are heuristic and may require tuning per codebase.
- AI quality depends on model choice, prompt tuning, and chunk granularity.
- Current dedup key can merge semantically different issues sharing same signature fields.

## 11. Suggested Production Deployment Pattern

1. Run static-only scans on every pull request.
2. Run hybrid scans nightly with tight `max_cost`.
3. Store reports as CI artifacts.
4. Triage top risky files first.
5. Track recurring issue signatures and convert them into deterministic static rules.
