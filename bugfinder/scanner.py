from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


DEFAULT_EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".tox",
}

SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".go",
    ".rs",
    ".php",
    ".rb",
    ".cs",
    ".cpp",
    ".cc",
    ".cxx",
    ".c",
    ".h",
    ".hpp",
    ".swift",
    ".kt",
    ".kts",
    ".scala",
    ".sql",
    ".sh",
    ".yaml",
    ".yml",
    ".json",
}

EXTENSION_LANGUAGE = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".php": "php",
    ".rb": "ruby",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".swift": "swift",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".scala": "scala",
    ".sql": "sql",
    ".sh": "bash",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
}


@dataclass(slots=True)
class CodeChunk:
    file_path: str
    start_line: int
    end_line: int
    content: str
    language: str


def scan_python_files(root_path: str, exclude_dirs: set[str] | None = None) -> list[Path]:
    root = Path(root_path).resolve()
    excludes = exclude_dirs or DEFAULT_EXCLUDED_DIRS
    files: list[Path] = []
    for p in root.rglob("*.py"):
        if any(part in excludes for part in p.parts):
            continue
        files.append(p)
    return files


def scan_source_files(
    root_path: str,
    exclude_dirs: set[str] | None = None,
    include_extensions: set[str] | None = None,
) -> list[Path]:
    root = Path(root_path).resolve()
    excludes = exclude_dirs or DEFAULT_EXCLUDED_DIRS
    exts = include_extensions or SUPPORTED_EXTENSIONS
    files: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in excludes for part in p.parts):
            continue
        if p.suffix.lower() in exts:
            files.append(p)
    return files


def language_for_path(file_path: Path) -> str:
    return EXTENSION_LANGUAGE.get(file_path.suffix.lower(), "text")


def _fallback_chunk(source_lines: list[str], file_path: str, max_lines: int) -> list[CodeChunk]:
    chunks: list[CodeChunk] = []
    lang = language_for_path(Path(file_path))
    for i in range(0, len(source_lines), max_lines):
        start = i + 1
        end = min(i + max_lines, len(source_lines))
        content = "".join(source_lines[i:end])
        chunks.append(CodeChunk(file_path=file_path, start_line=start, end_line=end, content=content, language=lang))
    return chunks


def chunk_python_file(file_path: Path, max_lines: int = 120) -> list[CodeChunk]:
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines(keepends=True)
    rel = str(file_path)
    if not text.strip():
        return []

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return _fallback_chunk(lines, rel, max_lines=max_lines)

    chunks: list[CodeChunk] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = getattr(node, "lineno", None)
            end = getattr(node, "end_lineno", None)
            if start is None or end is None:
                continue
            content = "".join(lines[start - 1 : end])
            if content.strip():
                chunks.append(
                    CodeChunk(
                        file_path=rel,
                        start_line=start,
                        end_line=end,
                        content=content,
                        language="python",
                    )
                )

    if not chunks:
        return _fallback_chunk(lines, rel, max_lines=max_lines)

    final_chunks: list[CodeChunk] = []
    for chunk in chunks:
        chunk_len = chunk.end_line - chunk.start_line + 1
        if chunk_len <= max_lines:
            final_chunks.append(chunk)
            continue
        split_lines = chunk.content.splitlines(keepends=True)
        for i in range(0, len(split_lines), max_lines):
            start_line = chunk.start_line + i
            end_line = min(chunk.start_line + i + max_lines - 1, chunk.end_line)
            content = "".join(split_lines[i : i + max_lines])
            final_chunks.append(
                CodeChunk(
                    file_path=chunk.file_path,
                    start_line=start_line,
                    end_line=end_line,
                    content=content,
                    language=chunk.language,
                )
            )
    return final_chunks


def chunk_source_file(file_path: Path, max_lines: int = 120) -> list[CodeChunk]:
    if file_path.suffix.lower() == ".py":
        return chunk_python_file(file_path, max_lines=max_lines)
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines(keepends=True)
    if not text.strip():
        return []
    return _fallback_chunk(lines, str(file_path), max_lines=max_lines)
