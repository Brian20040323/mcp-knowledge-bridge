"""Tool implementations exposed over MCP."""

from __future__ import annotations

import json
from pathlib import Path

from .kb import KnowledgeBase

_DATA = Path(__file__).resolve().parent.parent / "data" / "knowledge.json"
_KB = KnowledgeBase.from_json(_DATA)


def tool_schemas() -> list[dict]:
    return [
        {
            "name": "kb_search",
            "description": "Search the local knowledge base by keyword overlap.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "default": 3},
                },
                "required": ["query"],
            },
        },
        {
            "name": "kb_get",
            "description": "Fetch one knowledge entry by id.",
            "inputSchema": {
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "required": ["id"],
            },
        },
        {
            "name": "echo_debug",
            "description": "Echo payload for wiring tests.",
            "inputSchema": {
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": ["message"],
            },
        },
    ]


def call_tool(name: str, arguments: dict) -> str:
    if name == "kb_search":
        query = str(arguments.get("query") or "")
        top_k = int(arguments.get("top_k") or 3)
        hits = _KB.search(query, top_k=top_k)
        payload = [
            {"id": e.id, "title": e.title, "score": round(s, 4), "snippet": e.content[:120]}
            for e, s in hits
        ]
        return json.dumps(payload, ensure_ascii=False, indent=2)
    if name == "kb_get":
        entry = _KB.get(str(arguments.get("id") or ""))
        if not entry:
            return json.dumps({"error": "not found"}, ensure_ascii=False)
        return json.dumps(
            {"id": entry.id, "title": entry.title, "content": entry.content, "tags": entry.tags},
            ensure_ascii=False,
            indent=2,
        )
    if name == "echo_debug":
        return json.dumps({"echo": arguments.get("message")}, ensure_ascii=False)
    return json.dumps({"error": f"unknown tool: {name}"}, ensure_ascii=False)
