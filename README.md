# MCP Knowledge Bridge

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-0.3.0-blueviolet.svg)](#scope)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An educational, hand-written implementation of a useful MCP subset. Version 0.3.0 supports the
`2025-11-25` protocol version over stdio with tools, resources, prompts, ping, initialization
lifecycle enforcement, and JSON-RPC errors. It is intentionally small and is not a complete MCP
SDK or production gateway.

## Install and run

```bash
python -m pip install -e ".[dev]"
python -m examples.demo_protocol
python -m mcp_bridge.server
```

The stable MCP stdio transport uses one UTF-8 JSON-RPC message per line. Each message must be on a
single line; this project does not use `Content-Length` framing.

Installed console script:

```bash
mcp-knowledge-bridge
```

### Cursor MCP config

```json
{
  "mcpServers": {
    "knowledge-bridge": {
      "command": "python",
      "args": ["-m", "mcp_bridge.server"],
      "cwd": "/absolute/path/to/mcp-knowledge-bridge"
    }
  }
}
```

## Custom REST companion

`mcp_bridge.http_server` is a custom authenticated REST companion. It is **not MCP Streamable
HTTP**, does not implement MCP over HTTP, and does not implement OAuth. It exposes convenience
endpoints for this repository's tools and resources.

Startup requires an explicit `MCP_BRIDGE_TOKEN`; there is no default token and query-string tokens
are rejected. `/health` remains public and does not reveal the token.

```bash
export MCP_BRIDGE_TOKEN="replace-with-a-secret"
mcp-knowledge-bridge-rest
curl -H "Authorization: Bearer replace-with-a-secret" http://127.0.0.1:8765/tools
```

On PowerShell, set the environment variable with:

```powershell
$env:MCP_BRIDGE_TOKEN = "replace-with-a-secret"
```

## Scope

The implemented MCP surface is `initialize`, `notifications/initialized`, `ping`, `tools/list`,
`tools/call`, `resources/list`, `resources/read`, `prompts/list`, and `prompts/get`. Protocol
negotiation currently accepts only `2025-11-25`. The in-process client creates an independent
server session for tests and simple adapters.

The repository does not claim support for sampling, roots, elicitation, subscriptions, completion,
logging, tasks, Streamable HTTP, or other unimplemented MCP features.

## Development

```bash
python -m ruff check .
python -m pytest --cov=mcp_bridge --cov-report=term-missing
```

MIT © Brian20040323
