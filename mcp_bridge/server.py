"""Small, hand-written MCP server using newline-delimited JSON-RPC over stdio."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any, BinaryIO

from .tools import STORE, call_tool, tool_schemas

PROTOCOL_VERSION = "2025-11-25"
SERVER_INFO = {"name": "mcp-knowledge-bridge", "version": "0.3.0"}


def _read_line(stream: BinaryIO) -> tuple[bool, Any]:
    """Return (has_input, decoded JSON); malformed input is represented by an exception."""
    line = stream.readline()
    if not line:
        return False, None
    try:
        # MCP stdio messages are one JSON value per line and may not contain newlines.
        return True, json.loads(line.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return True, exc


def _write_message(payload: dict[str, Any], stream: BinaryIO) -> None:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    stream.write(raw + b"\n")
    stream.flush()


def _ok(req_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _err(req_id: Any, code: int, message: str, data: Any = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": req_id, "error": error}


@dataclass
class MCPServer:
    """Protocol state for one MCP connection."""

    initialized: bool = False
    initialize_responded: bool = False

    def handle(self, msg: Any) -> dict[str, Any] | None:
        if not isinstance(msg, dict):
            return _err(None, -32600, "Invalid Request")

        has_id = "id" in msg
        req_id = msg.get("id") if has_id else None
        method = msg.get("method")
        is_notification = not has_id
        valid_id = req_id is None or (
            isinstance(req_id, (str, int, float)) and not isinstance(req_id, bool)
        )
        valid_shape = (
            msg.get("jsonrpc") == "2.0"
            and isinstance(method, str)
            and valid_id
            and ("params" not in msg or isinstance(msg["params"], (dict, list)))
        )
        if not valid_shape:
            return None if is_notification else _err(None, -32600, "Invalid Request")

        params = msg.get("params", {})
        if method == "ping":
            return None if is_notification else _ok(req_id, {})

        if method == "initialize":
            if is_notification:
                return None
            if self.initialize_responded:
                return _err(req_id, -32600, "Initialize may only be requested once")
            if not isinstance(params, dict):
                return _err(req_id, -32602, "Invalid initialize parameters")
            version = params.get("protocolVersion")
            client_info = params.get("clientInfo")
            capabilities = params.get("capabilities")
            if (
                version != PROTOCOL_VERSION
                or not isinstance(client_info, dict)
                or not isinstance(capabilities, dict)
            ):
                return _err(
                    req_id,
                    -32602,
                    f"Unsupported or invalid protocol parameters; supported version is {PROTOCOL_VERSION}",
                )
            self.initialize_responded = True
            return _ok(
                req_id,
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
                    "serverInfo": SERVER_INFO,
                },
            )

        if method == "notifications/initialized":
            if not is_notification:
                return _err(req_id, -32600, "notifications/initialized must be a notification")
            if self.initialize_responded:
                self.initialized = True
            return None

        if not self.initialized:
            return None if is_notification else _err(req_id, -32600, "Server is not initialized")

        if not isinstance(params, dict):
            return None if is_notification else _err(req_id, -32602, "Parameters must be an object")

        response = self._business_method(method, req_id, params)
        return None if is_notification else response

    def _business_method(
        self, method: str, req_id: Any, params: dict[str, Any]
    ) -> dict[str, Any]:
        if method == "tools/list":
            return _ok(req_id, {"tools": tool_schemas()})
        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments", {})
            if not isinstance(name, str) or not isinstance(arguments, dict):
                return _err(req_id, -32602, "tools/call requires a string name and object arguments")
            result = call_tool(name, arguments)
            return _ok(
                req_id,
                {
                    "content": [{"type": "text", "text": result.text}],
                    "isError": result.is_error,
                },
            )
        if method == "resources/list":
            return _ok(req_id, {"resources": STORE.list_resources()})
        if method == "resources/read":
            uri = params.get("uri")
            if not isinstance(uri, str):
                return _err(req_id, -32602, "resources/read requires a string uri")
            text = STORE.read_resource(uri)
            if text is None:
                return _err(req_id, -32002, f"Resource not found: {uri}")
            return _ok(
                req_id,
                {"contents": [{"uri": uri, "mimeType": "text/plain", "text": text}]},
            )
        if method == "prompts/list":
            return _ok(req_id, {"prompts": STORE.list_prompts()})
        if method == "prompts/get":
            name = params.get("name")
            arguments = params.get("arguments", {})
            if not isinstance(name, str) or not isinstance(arguments, dict):
                return _err(req_id, -32602, "prompts/get requires a string name and object arguments")
            prompt = STORE.get_prompt(name, arguments)
            if prompt is None:
                return _err(req_id, -32002, f"Prompt not found: {name}")
            return _ok(req_id, prompt)
        return _err(req_id, -32601, f"Method not found: {method}")


def serve(input_stream: BinaryIO, output_stream: BinaryIO) -> None:
    server = MCPServer()
    while True:
        has_input, msg = _read_line(input_stream)
        if not has_input:
            break
        if isinstance(msg, (UnicodeDecodeError, json.JSONDecodeError)):
            _write_message(_err(None, -32700, "Parse error"), output_stream)
            continue
        response = server.handle(msg)
        if response is not None:
            _write_message(response, output_stream)


def main() -> None:
    serve(sys.stdin.buffer, sys.stdout.buffer)


if __name__ == "__main__":
    main()
