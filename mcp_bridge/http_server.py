"""HTTP companion for MCP Knowledge Bridge (stdlib only)."""

from __future__ import annotations

import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .tools import STORE, call_tool, tool_schemas


def bearer_token_matches(header: str | None, token: str) -> bool:
    if not header or not token:
        return False
    scheme, separator, supplied = header.partition(" ")
    return separator == " " and scheme == "Bearer" and hmac.compare_digest(supplied, token)


class BridgeHTTPServer(ThreadingHTTPServer):
    auth_token: str


class Handler(BaseHTTPRequestHandler):
    server_version = "MCPKnowledgeBridgeREST/0.3"

    def _auth_ok(self) -> bool:
        server = self.server
        assert isinstance(server, BridgeHTTPServer)
        return bearer_token_matches(self.headers.get("Authorization"), server.auth_token)

    def _json(self, code: int, payload: dict) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/health":
            return self._json(200, {"ok": True, "auth_required": True})
        if not self._auth_ok():
            return self._json(401, {"error": "unauthorized"})
        if path == "/tools":
            return self._json(200, {"tools": tool_schemas()})
        if path == "/resources":
            return self._json(200, {"resources": STORE.list_resources()})
        if path == "/prompts":
            return self._json(200, {"prompts": STORE.list_prompts()})
        return self._json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if not self._auth_ok():
            return self._json(401, {"error": "unauthorized"})
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(body.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self._json(400, {"error": "invalid json"})
        if not isinstance(data, dict):
            return self._json(400, {"error": "request body must be an object"})

        if path == "/tools/call":
            name = data.get("name")
            arguments = data.get("arguments", {})
            if not isinstance(name, str) or not isinstance(arguments, dict):
                return self._json(400, {"error": "name must be a string and arguments an object"})
            result = call_tool(name, arguments)
            return self._json(200, {"content": result.text, "isError": result.is_error})
        if path == "/resources/read":
            uri = str(data.get("uri") or "")
            text = STORE.read_resource(uri)
            if text is None:
                return self._json(404, {"error": "not found"})
            return self._json(200, {"uri": uri, "text": text})
        return self._json(404, {"error": "not found"})

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003
        return


def create_server(host: str, port: int, token: str) -> BridgeHTTPServer:
    if not token:
        raise ValueError("MCP_BRIDGE_TOKEN must be set and non-empty")
    httpd = BridgeHTTPServer((host, port), Handler)
    httpd.auth_token = token
    return httpd


def main(host: str = "127.0.0.1", port: int = 8765) -> None:
    token = os.getenv("MCP_BRIDGE_TOKEN")
    if not token:
        raise SystemExit("MCP_BRIDGE_TOKEN is required to start the REST companion")
    httpd = create_server(host, port, token)
    print(f"MCP Knowledge Bridge REST companion listening on http://{host}:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
