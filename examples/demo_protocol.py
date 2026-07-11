"""Exercise full MCP request path via LocalMCPClient."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp_bridge.client import LocalMCPClient


def main() -> None:
    c = LocalMCPClient()
    info = c.initialize()
    print("server:", info["serverInfo"])
    tools = [t["name"] for t in c.list_tools()]
    print("tools:", tools)
    print("search:", c.call_tool("kb_search", {"query": "MCP resources 评测", "top_k": 2})[:300])
    resources = c.list_resources()
    print("resources:", len(resources))
    if resources:
        print("read:", c.read_resource(resources[0]["uri"])[:200])
    prompts = c.list_prompts()
    print("prompts:", [p["name"] for p in prompts])
    print("prompt.get:", c.get_prompt("research_brief", {"topic": "MCP"})["messages"][0]["content"]["text"][:120])
    print("compare:", c.call_tool("kb_compare", {"left_id": "kb-react", "right_id": "kb-mcp"})[:300])


if __name__ == "__main__":
    main()
