from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import Any

from bugfinder.api import AuditOptions, render_report, run_audit
from bugfinder.fixer import apply_safe_fixes

SERVER_NAME = "testx-mcp"
SERVER_VERSION = "1.0.0"

_LATEST_AUDIT: dict[str, Any] | None = None


def _read_message() -> dict[str, Any] | None:
    """
    Read an MCP/JSON-RPC message using Content-Length framing.
    Falls back to newline-delimited JSON for lightweight clients.
    """
    stdin = sys.stdin.buffer
    first = stdin.readline()
    if not first:
        return None
    if first.startswith(b"Content-Length:"):
        length = int(first.split(b":", 1)[1].strip())
        # consume remaining headers
        while True:
            line = stdin.readline()
            if line in {b"\r\n", b"\n", b""}:
                break
        body = stdin.read(length)
        return json.loads(body.decode("utf-8"))
    # fallback: newline JSON transport
    return json.loads(first.decode("utf-8").strip())


def _write_message(payload: dict[str, Any]) -> None:
    body = json.dumps(payload).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
    sys.stdout.buffer.write(header)
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def _ok(msg_id: Any, result: dict[str, Any]) -> None:
    _write_message({"jsonrpc": "2.0", "id": msg_id, "result": result})


def _err(msg_id: Any, code: int, message: str) -> None:
    _write_message(
        {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": code, "message": message},
        }
    )


def _tool_specs() -> list[dict[str, Any]]:
    return [
        {
            "name": "scan_codebase",
            "description": "Run deep codebase scan and return report.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "ai_provider": {"type": "string", "enum": ["none", "openai", "claude"]},
                    "model": {"type": "string"},
                    "max_cost": {"type": "number"},
                    "output": {"type": "string", "enum": ["text", "json", "html"]},
                    "min_severity": {"type": "string", "enum": ["low", "medium", "high"]},
                },
                "required": ["path"],
            },
        },
        {
            "name": "fix_codebase",
            "description": "Apply safe fixes and return fix summary with remaining issues.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "dry_run": {"type": "boolean"},
                    "force": {"type": "boolean"},
                    "ai_provider": {"type": "string", "enum": ["none", "openai", "claude"]},
                    "model": {"type": "string"},
                    "max_cost": {"type": "number"},
                    "min_severity": {"type": "string", "enum": ["low", "medium", "high"]},
                },
                "required": ["path"],
            },
        },
        {
            "name": "enterprise_audit",
            "description": "Run enterprise-grade audit with risk scoring and remediation summary.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "ai_provider": {"type": "string", "enum": ["none", "openai", "claude"]},
                    "model": {"type": "string"},
                    "max_cost": {"type": "number"},
                    "force_fixes": {"type": "boolean"},
                },
                "required": ["path"],
            },
        },
        {
            "name": "remediation_plan",
            "description": "Generate prioritized remediation plan from latest audit results.",
            "inputSchema": {
                "type": "object",
                "properties": {},
            },
        },
    ]


def _handle_scan(args: dict[str, Any]) -> dict[str, Any]:
    global _LATEST_AUDIT
    output = args.get("output", "json")
    report = run_audit(
        args["path"],
        AuditOptions(
            ai_provider=args.get("ai_provider"),
            model=args.get("model"),
            max_cost=args.get("max_cost"),
            min_severity=args.get("min_severity"),
        ),
    )
    rendered = render_report(report, output=output)
    _LATEST_AUDIT = report.to_dict()
    return {
        "content": [{"type": "text", "text": rendered}],
        "structuredContent": report.to_dict(),
    }


def _handle_fix(args: dict[str, Any]) -> dict[str, Any]:
    global _LATEST_AUDIT
    path = args["path"]
    report = run_audit(
        path,
        AuditOptions(
            ai_provider=args.get("ai_provider"),
            model=args.get("model"),
            max_cost=args.get("max_cost"),
            min_severity=args.get("min_severity"),
        ),
    )
    fix_report = apply_safe_fixes(
        report.issues,
        root_path=path,
        dry_run=bool(args.get("dry_run", False)),
        force=bool(args.get("force", False)),
    )
    post_report = run_audit(
        path,
        AuditOptions(
            ai_provider=args.get("ai_provider"),
            model=args.get("model"),
            max_cost=args.get("max_cost"),
            min_severity=args.get("min_severity"),
        ),
    )
    summary = {
        "total_issues": fix_report.total_issues,
        "suggested_fixes": fix_report.suggested_fixes,
        "safe_fix_candidates": fix_report.safe_fix_candidates,
        "applied_count": fix_report.applied_count,
        "skipped_count": fix_report.skipped_count,
        "actions": [
            {
                "file_path": a.file_path,
                "line": a.line,
                "description": a.description,
                "status": a.status,
                "confidence": a.confidence,
                "preview_before": a.preview_before,
                "preview_after": a.preview_after,
            }
            for a in fix_report.actions
        ],
        "remaining_issues": len(post_report.issues),
    }
    _LATEST_AUDIT = post_report.to_dict()
    return {
        "content": [{"type": "text", "text": json.dumps(summary, indent=2)}],
        "structuredContent": summary,
    }


def _risk_score(report: dict[str, Any]) -> int:
    sev = report.get("audit_summary", {}).get("severity_counts", {})
    high = int(sev.get("high", 0))
    medium = int(sev.get("medium", 0))
    low = int(sev.get("low", 0))
    score = min(100, (high * 12) + (medium * 4) + low)
    return score


def _build_remediation_plan(report: dict[str, Any]) -> dict[str, Any]:
    issues = report.get("issues", [])
    critical = [i for i in issues if str(i.get("severity", "")).lower() == "high"]
    major = [i for i in issues if str(i.get("severity", "")).lower() == "medium"]
    minor = [i for i in issues if str(i.get("severity", "")).lower() == "low"]
    return {
        "priorities": [
            {
                "priority": "P0",
                "title": "Resolve high-severity security and reliability issues",
                "count": len(critical),
                "items": critical[:25],
            },
            {
                "priority": "P1",
                "title": "Stabilize medium-severity bugs and reliability gaps",
                "count": len(major),
                "items": major[:25],
            },
            {
                "priority": "P2",
                "title": "Clean up low-severity code quality debt",
                "count": len(minor),
                "items": minor[:25],
            },
        ],
        "recommended_order": ["P0", "P1", "P2"],
    }


def _handle_enterprise_audit(args: dict[str, Any]) -> dict[str, Any]:
    global _LATEST_AUDIT
    path = args["path"]
    report = run_audit(
        path,
        AuditOptions(
            ai_provider=args.get("ai_provider"),
            model=args.get("model"),
            max_cost=args.get("max_cost"),
        ),
    )
    fix_report = apply_safe_fixes(
        report.issues,
        root_path=path,
        dry_run=True,
        force=bool(args.get("force_fixes", False)),
    )
    report_dict = report.to_dict()
    plan = _build_remediation_plan(report_dict)
    payload = {
        "audit": report_dict,
        "risk_score": _risk_score(report_dict),
        "dry_run_fix_summary": {
            "suggested_fixes": fix_report.suggested_fixes,
            "safe_fix_candidates": fix_report.safe_fix_candidates,
            "planned_count": sum(1 for a in fix_report.actions if a.status == "planned"),
            "skipped_count": fix_report.skipped_count,
        },
        "remediation_plan": plan,
    }
    _LATEST_AUDIT = report_dict
    return {
        "content": [{"type": "text", "text": json.dumps(payload, indent=2)}],
        "structuredContent": payload,
    }


def _handle_remediation_plan() -> dict[str, Any]:
    if _LATEST_AUDIT is None:
        payload = {"message": "No prior audit found. Run scan_codebase or enterprise_audit first."}
    else:
        payload = _build_remediation_plan(_LATEST_AUDIT)
    return {
        "content": [{"type": "text", "text": json.dumps(payload, indent=2)}],
        "structuredContent": payload,
    }


def main() -> None:
    while True:
        try:
            msg = _read_message()
        except EOFError:
            break
        except Exception:
            _write_message(
                {
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": "Parse error"},
                }
            )
            continue

        if msg is None:
            continue

        method = msg.get("method")
        msg_id = msg.get("id")
        params = msg.get("params", {})

        try:
            if method == "initialize":
                _ok(
                    msg_id,
                    {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                    },
                )
            elif method == "notifications/initialized":
                # Notification: no response required.
                continue
            elif method == "tools/list":
                _ok(msg_id, {"tools": _tool_specs()})
            elif method == "tools/call":
                name = params.get("name")
                arguments = params.get("arguments", {})
                if name == "scan_codebase":
                    _ok(msg_id, _handle_scan(arguments))
                elif name == "fix_codebase":
                    _ok(msg_id, _handle_fix(arguments))
                elif name == "enterprise_audit":
                    _ok(msg_id, _handle_enterprise_audit(arguments))
                elif name == "remediation_plan":
                    _ok(msg_id, _handle_remediation_plan())
                else:
                    _err(msg_id, -32601, f"Unknown tool: {name}")
            else:
                _err(msg_id, -32601, f"Method not found: {method}")
        except Exception as exc:  # pragma: no cover
            _err(msg_id, -32000, f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}")


if __name__ == "__main__":
    # Ensure relative paths from client resolve against server launch directory.
    Path(".").resolve()
    main()
