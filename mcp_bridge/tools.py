"""MCP-compatible knowledge bridge with tools + resources."""

from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "knowledge.json"
CORPUS_DIR = ROOT / "knowledge_docs"

_WORD = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]")


def tokenize(text: str) -> list[str]:
    return _WORD.findall((text or "").lower())


@dataclass
class Entry:
    id: str
    title: str
    content: str
    tags: list[str]
    uri: str


class KnowledgeStore:
    def __init__(self) -> None:
        self.entries: dict[str, Entry] = {}
        self._load_json()
        self._load_docs()
        self._tokens = {eid: tokenize(f"{e.title} {e.content} {' '.join(e.tags)}") for eid, e in self.entries.items()}
        self.n = max(len(self.entries), 1)
        self.df: Counter[str] = Counter()
        for toks in self._tokens.values():
            for t in set(toks):
                self.df[t] += 1
        self.doc_len = {eid: len(toks) or 1 for eid, toks in self._tokens.items()}
        self.avgdl = sum(self.doc_len.values()) / self.n

    def _load_json(self) -> None:
        raw = json.loads(DATA.read_text(encoding="utf-8"))
        for item in raw:
            eid = item["id"]
            self.entries[eid] = Entry(
                id=eid,
                title=item["title"],
                content=item["content"],
                tags=list(item.get("tags") or []),
                uri=f"kb://entry/{eid}",
            )

    def _load_docs(self) -> None:
        if not CORPUS_DIR.exists():
            return
        for fp in CORPUS_DIR.glob("*.md"):
            eid = f"doc-{fp.stem}"
            text = fp.read_text(encoding="utf-8").strip()
            title = text.splitlines()[0].lstrip("# ").strip() if text else fp.stem
            self.entries[eid] = Entry(id=eid, title=title, content=text, tags=["doc"], uri=f"kb://doc/{fp.stem}")

    def list_resources(self) -> list[dict[str, Any]]:
        return [
            {"uri": e.uri, "name": e.title, "mimeType": "text/plain", "description": e.id}
            for e in self.entries.values()
        ]

    def read_resource(self, uri: str) -> str | None:
        for e in self.entries.values():
            if e.uri == uri:
                return f"# {e.title}\n\n{e.content}\n\ntags: {', '.join(e.tags)}"
        return None

    def list_prompts(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "research_brief",
                "description": "Ask the model to research a topic using kb_search then summarize with citations.",
                "arguments": [{"name": "topic", "description": "Topic to research", "required": True}],
            },
            {
                "name": "compare_topics",
                "description": "Compare two knowledge entry ids with kb_compare.",
                "arguments": [
                    {"name": "left_id", "required": True},
                    {"name": "right_id", "required": True},
                ],
            },
        ]

    def get_prompt(self, name: str, arguments: dict | None = None) -> dict[str, Any] | None:
        arguments = arguments or {}
        if name == "research_brief":
            topic = arguments.get("topic", "{{topic}}")
            text = (
                f"Research topic: {topic}\n"
                "1) Call kb_search on the topic\n"
                "2) Optionally kb_get the top hit\n"
                "3) Write a short brief with source ids"
            )
            return {"name": name, "messages": [{"role": "user", "content": {"type": "text", "text": text}}]}
        if name == "compare_topics":
            left = arguments.get("left_id", "kb-react")
            right = arguments.get("right_id", "kb-mcp")
            text = f"Compare knowledge entries {left} vs {right} using kb_compare, then explain differences."
            return {"name": name, "messages": [{"role": "user", "content": {"type": "text", "text": text}}]}
        return None

    def get(self, entry_id: str) -> Entry | None:
        return self.entries.get(entry_id)

    def _bm25(self, q: list[str], eid: str) -> float:
        toks = self._tokens[eid]
        tf = Counter(toks)
        dl = self.doc_len[eid]
        score = 0.0
        k1, b = 1.5, 0.75
        for t in q:
            if t not in tf:
                continue
            df = self.df[t]
            idf = math.log(1 + (self.n - df + 0.5) / (df + 0.5))
            freq = tf[t]
            score += idf * (freq * (k1 + 1)) / (freq + k1 * (1 - b + b * dl / self.avgdl))
        return score

    def search(self, query: str, top_k: int = 3) -> list[tuple[Entry, float]]:
        q = tokenize(query)
        if not q:
            return []
        scored = [(e, self._bm25(q, e.id)) for e in self.entries.values()]
        scored = [(e, s) for e, s in scored if s > 0]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


STORE = KnowledgeStore()


def tool_schemas() -> list[dict]:
    return [
        {
            "name": "kb_search",
            "description": "BM25 search over local knowledge entries and markdown docs.",
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
            "name": "kb_compare",
            "description": "Compare two knowledge topics and return a structured diff summary.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "left_id": {"type": "string"},
                    "right_id": {"type": "string"},
                },
                "required": ["left_id", "right_id"],
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
        hits = STORE.search(str(arguments.get("query") or ""), int(arguments.get("top_k") or 3))
        payload = [
            {
                "id": e.id,
                "title": e.title,
                "score": round(s, 4),
                "uri": e.uri,
                "snippet": e.content[:160].replace("\n", " "),
            }
            for e, s in hits
        ]
        return json.dumps(payload, ensure_ascii=False, indent=2)
    if name == "kb_get":
        entry = STORE.get(str(arguments.get("id") or ""))
        if not entry:
            return json.dumps({"error": "not found"}, ensure_ascii=False)
        return json.dumps(
            {"id": entry.id, "title": entry.title, "content": entry.content, "tags": entry.tags, "uri": entry.uri},
            ensure_ascii=False,
            indent=2,
        )
    if name == "kb_compare":
        left = STORE.get(str(arguments.get("left_id") or ""))
        right = STORE.get(str(arguments.get("right_id") or ""))
        if not left or not right:
            return json.dumps({"error": "one or both ids not found"}, ensure_ascii=False)
        lt, rt = set(tokenize(left.content)), set(tokenize(right.content))
        payload = {
            "left": {"id": left.id, "title": left.title},
            "right": {"id": right.id, "title": right.title},
            "shared_terms": sorted(lt & rt)[:20],
            "left_only": sorted(lt - rt)[:20],
            "right_only": sorted(rt - lt)[:20],
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)
    if name == "echo_debug":
        return json.dumps({"echo": arguments.get("message")}, ensure_ascii=False)
    return json.dumps({"error": f"unknown tool: {name}"}, ensure_ascii=False)
