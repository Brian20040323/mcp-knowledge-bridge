# MCP Knowledge Bridge

[![CI](https://github.com/Brian20040323/mcp-knowledge-bridge/actions/workflows/ci.yml/badge.svg)](https://github.com/Brian20040323/mcp-knowledge-bridge/actions/workflows/ci.yml)

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-0.2.0-blueviolet.svg)](#whats-new-in-v020)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-tools%20%2B%20resources%20%2B%20prompts-blueviolet.svg)](#features)
[![HTTP](https://img.shields.io/badge/transport-stdio%20%2B%20HTTP-success.svg)](#http-companion)
[![Stars](https://img.shields.io/github/stars/Brian20040323/mcp-knowledge-bridge?style=social)](https://github.com/Brian20040323/mcp-knowledge-bridge)

> **v0.2** MCP-compatible knowledge bridge with **tools + resources + prompts**, local BM25 KB, in-process client, and a **token-guarded HTTP companion** (stdlib only).  
> Independent protocol-layer demo for Cursor / custom agents — not an SDK re-export.

**Related:** [lite-react-agent](https://github.com/Brian20040323/lite-react-agent) · [hybrid-rag-kit](https://github.com/Brian20040323/hybrid-rag-kit)

---

## What's new in v0.2

| Addition | Why |
|----------|-----|
| **`prompts/list` + `prompts/get`** | Full-er MCP surface for agent workflows |
| **HTTP companion** | `/tools`, `/tools/call`, `/resources`, `/prompts` with Bearer token |
| **Auth stub** | `MCP_BRIDGE_TOKEN` (default `dev-token`) |

---

## Quickstart

```bash
git clone https://github.com/Brian20040323/mcp-knowledge-bridge.git
cd mcp-knowledge-bridge
python -m examples.demo_protocol
python -m mcp_bridge.server          # stdio MCP
python -m mcp_bridge.http_server     # HTTP on :8765
```

```bash
curl -H "Authorization: Bearer dev-token" http://127.0.0.1:8765/tools
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

---

## Independence thesis

MCP hype is real; most demos hide behind opaque SDKs. This bridge keeps JSON-RPC framing, tool schemas, resources, and prompts **readable in one repo**, so you can explain protocol design in interviews.

---

## License

MIT © Brian20040323
