"""In-memory knowledge base."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

_WORD = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]")


@dataclass
class Entry:
    id: str
    title: str
    content: str
    tags: list[str]


class KnowledgeBase:
    def __init__(self, entries: list[Entry]) -> None:
        self.entries = {e.id: e for e in entries}

    @classmethod
    def from_json(cls, path: Path) -> "KnowledgeBase":
        raw = json.loads(path.read_text(encoding="utf-8"))
        entries = [
            Entry(
                id=item["id"],
                title=item["title"],
                content=item["content"],
                tags=list(item.get("tags") or []),
            )
            for item in raw
        ]
        return cls(entries)

    def get(self, entry_id: str) -> Entry | None:
        return self.entries.get(entry_id)

    def search(self, query: str, top_k: int = 3) -> list[tuple[Entry, float]]:
        q = set(_WORD.findall((query or "").lower()))
        if not q:
            return []
        scored: list[tuple[Entry, float]] = []
        for e in self.entries.values():
            bag = set(_WORD.findall(f"{e.title} {e.content} {' '.join(e.tags)}".lower()))
            overlap = len(q & bag)
            if overlap:
                scored.append((e, overlap / len(q)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
