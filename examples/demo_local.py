"""Local tool calls without stdio framing."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp_bridge.tools import call_tool, tool_schemas


def main() -> None:
    print("tools:", [t["name"] for t in tool_schemas()])
    print("--- kb_search ---")
    print(call_tool("kb_search", {"query": "混合检索 RAG", "top_k": 2}))
    print("--- kb_get ---")
    print(call_tool("kb_get", {"id": "kb-mcp"}))


if __name__ == "__main__":
    main()
