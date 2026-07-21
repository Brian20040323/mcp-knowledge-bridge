# Changelog

## 0.2.0 (2025-07)

- `prompts/list` + `prompts/get` for full-er MCP surface
- HTTP companion: `/tools`, `/tools/call`, `/resources`, `/prompts` with Bearer token
- Auth stub with `MCP_BRIDGE_TOKEN`
- In-process `LocalMCPClient` for testing and agent adapters

## 0.1.0

- Initial release: MCP stdio JSON-RPC server
- `tools/list` + `tools/call` (kb_search, kb_get, kb_compare, echo_debug)
- `resources/list` + `resources/read`
- Local BM25 knowledge store with JSON + Markdown sources
