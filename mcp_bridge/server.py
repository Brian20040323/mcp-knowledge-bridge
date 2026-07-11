"""Minimal MCP-compatible JSON-RPC server over stdio."""

from __future__ import annotations

import json
import sys
from typing import Any

from .tools import call_tool, tool_schemas

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "mcp-knowledge-bridge", "version": "0.1.0"}


def _read_message() -> dict[str, Any] | None:
    """Read one LSP/MCP-style Content-Length framed message from stdin."""
    headers: dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        key, _, value = line.decode("utf-8").partition(":")
        headers[key.strip().lower()] = value.strip()
    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    body = sys.stdin.buffer.read(length)
    return json.loads(body.decode("utf-8"))


def _write_message(payload: dict[str, Any]) -> None:
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(raw)}\r\n\r\n".encode("ascii"))
    sys.stdout.buffer.write(raw)
    sys.stdout.buffer.flush()


def _ok(req_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _err(req_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def handle(msg: dict[str, Any]) -> dict[str, Any] | None:
    method = msg.get("method")
    req_id = msg.get("id")
    params = msg.get("params") or {}

    # notifications (no id)
    if req_id is None and method in {"notifications/initialized", "initialized"}:
        return None

    if method == "initialize":
        return _ok(
            req_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            },
        )
    if method == "tools/list":
        return _ok(req_id, {"tools": tool_schemas()})
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        text = call_tool(str(name), arguments if isinstance(arguments, dict) else {})
        return _ok(
            req_id,
            {
                "content": [{"type": "text", "text": text}],
                "isError": text.startswith('{"error"'),
            },
        )
    if method == "ping":
        return _ok(req_id, {})

    if req_id is not None:
        return _err(req_id, -32601, f"Method not found: {method}")
    return None


def main() -> None:
    while True:
        msg = _read_message()
        if msg is None:
            break
        resp = handle(msg)
        if resp is not None:
            _write_message(resp)


if __name__ == "__main__":
    main()
