# MCP Knowledge Bridge

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-tools%20%2B%20resources-blueviolet.svg)](#features)
[![Cursor-ready](https://img.shields.io/badge/Cursor-MCP%20server-black.svg)](#use-with-cursor)
[![Zero deps](https://img.shields.io/badge/runtime-stdlib%20only-success.svg)](#quickstart)
[![Stars](https://img.shields.io/github/stars/Brian20040323/mcp-knowledge-bridge?style=social)](https://github.com/Brian20040323/mcp-knowledge-bridge)

> A **minimal MCP-compatible knowledge server** for the agent era:  
> stdio **JSON-RPC**, `tools/*` + `resources/*`, local **BM25** knowledge base, and an in-process client for tests.  
> Plug into **Cursor**, custom agents, or [lite-react-agent](https://github.com/Brian20040323/lite-react-agent).

**Related repos:** [lite-react-agent](https://github.com/Brian20040323/lite-react-agent) · [hybrid-rag-kit](https://github.com/Brian20040323/hybrid-rag-kit)

---

## Why this matters now

**Model Context Protocol (MCP)** is becoming the USB-C of AI tools — IDEs and agents need standard ways to discover and call capabilities.  
This repo is a **small, readable bridge** you can actually own:

| Feature | Description | Trending angle |
|---------|-------------|----------------|
| MCP subset | `initialize`, `tools/list`, `tools/call`, `resources/list`, `resources/read` | MCP servers |
| BM25 KB | JSON entries + markdown docs | Tool-augmented RAG |
| `kb_compare` | Structured topic comparison | Multi-tool agent demos |
| `LocalMCPClient` | Protocol path without spawning a subprocess | CI / unit testing MCP |
| Agent adapter | Works with lite-react-agent demo | Agent ↔ MCP |

---

## Quickstart

```bash
git clone https://github.com/Brian20040323/mcp-knowledge-bridge.git
cd mcp-knowledge-bridge

python -m examples.demo_local
python -m examples.demo_protocol

# Run as MCP stdio server
python -m mcp_bridge.server
```

---

## Use with Cursor

Add to your MCP config:

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

Then ask Cursor to search your local knowledge base via `kb_search` / `kb_get`.

---

## Tools

| Tool | Input | Purpose |
|------|-------|---------|
| `kb_search` | `query`, `top_k?` | BM25 search over entries + docs |
| `kb_get` | `id` | Fetch one entry |
| `kb_compare` | `left_id`, `right_id` | Term-overlap comparison |
| `echo_debug` | `message` | Wiring / smoke test |

Resources are exposed as `kb://entry/...` and `kb://doc/...` URIs.

---

## In-process client

```python
from mcp_bridge.client import LocalMCPClient

c = LocalMCPClient()
c.initialize()
print(c.call_tool("kb_search", {"query": "MCP resources", "top_k": 2}))
```

---

## Ecosystem story (star-worthy trilogy)

```text
mcp-knowledge-bridge   →  standardize knowledge as tools/resources
hybrid-rag-kit         →  measure & fuse retrieval quality
lite-react-agent       →  plan + act + observe with guardrails
```

Together: **Protocol → Retrieval → Agent runtime**.

---

## Honest boundaries

- MCP *subset* (not a full official SDK surface)  
- Local BM25 ≠ hosted enterprise search  
- Designed for demos, learning, and portfolio-grade integrations

---

## Roadmap

- [ ] HTTP/SSE transport companion  
- [ ] OAuth-style auth stub for remote mounts  
- [ ] Prompt templates via MCP `prompts/*`  
- [ ] Packaging as `pip install mcp-knowledge-bridge`  

---

## License

MIT © Brian20040323
