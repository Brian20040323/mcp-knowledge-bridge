"""HTTP companion for MCP Knowledge Bridge (stdlib only)."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .tools import STORE, call_tool, tool_schemas


AUTH_TOKEN = os.getenv("MCP_BRIDGE_TOKEN", "dev-token")


class Handler(BaseHTTPRequestHandler):
    server_version = "MCPKnowledgeBridgeHTTP/0.2"

    def _auth_ok(self) -> bool:
        header = self.headers.get("Authorization", "")
        if header == f"Bearer {AUTH_TOKEN}":
            return True
        # also allow query token for quick demos
        qs = parse_qs(urlparse(self.path).query)
        return qs.get("token", [None])[0] == AUTH_TOKEN

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
        except json.JSONDecodeError:
            return self._json(400, {"error": "invalid json"})

        if path == "/tools/call":
            name = str(data.get("name") or "")
            arguments = data.get("arguments") or {}
            text = call_tool(name, arguments if isinstance(arguments, dict) else {})
            return self._json(200, {"content": text})
        if path == "/resources/read":
            uri = str(data.get("uri") or "")
            text = STORE.read_resource(uri)
            if text is None:
                return self._json(404, {"error": "not found"})
            return self._json(200, {"uri": uri, "text": text})
        return self._json(404, {"error": "not found"})

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003
        return


def main(host: str = "127.0.0.1", port: int = 8765) -> None:
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"MCP Knowledge Bridge HTTP on http://{host}:{port}")
    print(f"Auth: Authorization: Bearer {AUTH_TOKEN}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
