# textx

`textx` is a production-oriented Python library and CLI that analyzes full codebases for bugs using:

- Static analysis (Python AST + generic cross-language heuristics)
- Optional AI analysis (OpenAI or Anthropic Claude)
- Caching to reduce repeated API calls and cost

## Features

- Recursive multi-language project scanning with ignore rules
- Smart chunking by functions/classes for Python and size-based chunking for other languages
- Hybrid analysis engine (static + AI)
- Structured issues with severity and fix suggestions
- Output formats: text, json, html
- Cost guardrails (`--max-cost`) and offline mode (`--ai none`)
- API key loading from environment variables or `.bugfinder.toml`
- Works across Python, React/JS/TS, Java, Go, Rust, C/C++, C#, Ruby, PHP, SQL, shell, YAML, and JSON files

## Installation

```bash
pip install textx
```

For local development:

```bash
pip install -e ".[dev]"
```

## Configuration

Configuration is loaded from:

1. Environment variables
2. `.bugfinder.toml` in current directory (optional)

Environment variables:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`

Example `.bugfinder.toml`:

```toml
[ai]
openai_api_key = "sk-..."
anthropic_api_key = "sk-ant-..."
default_provider = "openai"
default_model = "gpt-4o-mini"
max_cost = 5.0
rate_limit_per_minute = 30
```

## Usage

```bash
textx scan ./project --ai openai --model gpt-4o-mini --output text
```

Options:

- `--ai`: `openai | claude | none`
- `--model`: provider-specific model name
- `--max-cost`: stop AI calls when estimated spend exceeds this USD value
- `--output`: `text | json | html`
- `--output-file`: optional path to write report
- `--cache-db`: custom sqlite cache path

## Example Commands

```bash
# Offline static analysis only
textx scan . --ai none --output text

# OpenAI + static analysis with JSON output
textx scan . --ai openai --model gpt-4o-mini --output json --output-file report.json

# Claude + static analysis with budget cap
textx scan . --ai claude --model claude-3-5-sonnet-latest --max-cost 2.50 --output html --output-file report.html
```

## Testing

```bash
pytest
```

## Publish To PyPI

1. Build distribution:
   ```bash
   python -m pip install --upgrade build twine
   python -m build
   ```
2. Check package metadata:
   ```bash
   twine check dist/*
   ```
3. Upload to TestPyPI:
   ```bash
   twine upload --repository testpypi dist/*
   ```
4. Upload to PyPI:
   ```bash
   twine upload dist/*
   ```

## Security Notes

- API keys are never printed in logs.
- AI requests are opt-in and can be disabled with `--ai none`.
- Results are cached by file content hash to reduce external calls.

