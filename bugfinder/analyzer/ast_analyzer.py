from __future__ import annotations

import ast
from pathlib import Path

from bugfinder.models import AnalysisIssue


class _AstVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.issues: list[AnalysisIssue] = []

    def _add(self, issue_type: str, severity: str, desc: str, line: int | None, fix: str | None = None) -> None:
        self.issues.append(
            AnalysisIssue(
                issue_type=issue_type,
                severity=severity,
                description=desc,
                file_path=self.file_path,
                line=line,
                fix=fix,
                source="static",
            )
        )

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec"}:
            self._add(
                "security",
                "high",
                f"Use of {node.func.id} can execute untrusted code.",
                getattr(node, "lineno", None),
                "Avoid dynamic execution or validate/whitelist inputs strictly.",
            )
        if isinstance(node.func, ast.Attribute):
            # subprocess.*(..., shell=True) enables command injection when inputs are not tightly controlled.
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess":
                for keyword in node.keywords:
                    if keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                        self._add(
                            "security",
                            "high",
                            "subprocess call uses shell=True, increasing command injection risk.",
                            getattr(node, "lineno", None),
                            "Pass argument lists and avoid shell=True unless absolutely required.",
                        )
                        break
            # yaml.load without SafeLoader can execute arbitrary objects.
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "yaml"
                and node.func.attr == "load"
                and not any(keyword.arg == "Loader" for keyword in node.keywords)
            ):
                self._add(
                    "security",
                    "high",
                    "yaml.load used without explicit SafeLoader.",
                    getattr(node, "lineno", None),
                    "Use yaml.safe_load or yaml.load(..., Loader=yaml.SafeLoader).",
                )
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        for handler in node.handlers:
            if handler.type is None:
                self._add(
                    "bug",
                    "medium",
                    "Bare except detected; it may hide real failures.",
                    getattr(handler, "lineno", None),
                    "Catch specific exception classes instead of a bare except.",
                )
            elif isinstance(handler.type, ast.Name) and handler.type.id == "Exception":
                self._add(
                    "bug",
                    "medium",
                    "Broad 'except Exception' may swallow critical failures.",
                    getattr(handler, "lineno", None),
                    "Catch only expected exception types and re-raise unknown failures.",
                )
        self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> None:
        self._add(
            "bug",
            "low",
            "assert used for runtime checks; assertions can be disabled with optimization flags.",
            getattr(node, "lineno", None),
            "Use explicit conditional checks and raise concrete exceptions for runtime validation.",
        )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_mutable_defaults(node)
        self._check_unreachable(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_mutable_defaults(node)
        self._check_unreachable(node)
        self.generic_visit(node)

    def _check_mutable_defaults(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        for default in node.args.defaults:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self._add(
                    "bug",
                    "medium",
                    f"Mutable default argument in function '{node.name}'.",
                    getattr(default, "lineno", getattr(node, "lineno", None)),
                    "Use None as default and initialize inside the function.",
                )

    def _check_unreachable(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        for idx, stmt in enumerate(node.body[:-1]):
            if isinstance(stmt, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                next_stmt = node.body[idx + 1]
                self._add(
                    "code_smell",
                    "low",
                    f"Potential unreachable code after {type(stmt).__name__.lower()} in '{node.name}'.",
                    getattr(next_stmt, "lineno", None),
                    "Remove dead code or restructure control flow.",
                )
                break


def analyze_file_with_ast(file_path: Path) -> list[AnalysisIssue]:
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    rel = str(file_path)
    if not text.strip():
        return []
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return [
            AnalysisIssue(
                issue_type="bug",
                severity="high",
                description=f"Syntax error: {exc.msg}",
                file_path=rel,
                line=exc.lineno,
                fix="Fix syntax and rerun analysis.",
                source="static",
            )
        ]
    visitor = _AstVisitor(rel)
    visitor.visit(tree)
    return visitor.issues
