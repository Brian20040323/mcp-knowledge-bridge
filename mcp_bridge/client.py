"""In-process MCP client for tests / Agent adapters (no subprocess needed)."""

from __future__ import annotations

from typing import Any

from .server import PROTOCOL_VERSION, MCPServer


class LocalMCPClient:
    def __init__(self) -> None:
        self._id = 0
        self._server = MCPServer()

    def _req(self, method: str, params: dict | None = None) -> Any:
        self._id += 1
        msg = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params or {}}
        resp = self._server.handle(msg)
        assert resp is not None
        if "error" in resp:
            raise RuntimeError(resp["error"])
        return resp["result"]

    def initialize(self) -> dict:
        result = self._req(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "local-mcp-client", "version": "0.3.0"},
            },
        )
        self._server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return result

    def list_tools(self) -> list:
        return self._req("tools/list")["tools"]

    def call_tool(self, name: str, arguments: dict) -> str:
        result = self._req("tools/call", {"name": name, "arguments": arguments})
        return result["content"][0]["text"]

    def list_resources(self) -> list:
        return self._req("resources/list")["resources"]

    def read_resource(self, uri: str) -> str:
        return self._req("resources/read", {"uri": uri})["contents"][0]["text"]

    def list_prompts(self) -> list:
        return self._req("prompts/list")["prompts"]

    def get_prompt(self, name: str, arguments: dict | None = None) -> dict:
        return self._req("prompts/get", {"name": name, "arguments": arguments or {}})
