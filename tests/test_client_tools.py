from __future__ import annotations

import json

import pytest

from mcp_bridge.client import LocalMCPClient
from mcp_bridge.tools import ToolResult, call_tool


def test_local_client_initializes_full_session() -> None:
    client = LocalMCPClient()
    info = client.initialize()
    assert info["serverInfo"]["version"] == "0.3.0"
    assert "kb_search" in {tool["name"] for tool in client.list_tools()}
    assert client.list_resources()
    assert client.list_prompts()
    resource = client.list_resources()[0]
    assert client.read_resource(resource["uri"]).startswith("# ")
    research_prompt = client.get_prompt("research_brief", {"topic": "MCP"})
    assert "Research topic: MCP" in research_prompt["messages"][0]["content"]["text"]
    assert "kb-react" in client.get_prompt("compare_topics")["messages"][0]["content"]["text"]


def test_local_clients_own_independent_sessions() -> None:
    first = LocalMCPClient()
    second = LocalMCPClient()
    first.initialize()
    assert first.list_tools()
    with pytest.raises(RuntimeError, match="not initialized"):
        second.list_tools()
    second.initialize()
    assert second.list_tools()


def test_client_preserves_simple_text_api() -> None:
    client = LocalMCPClient()
    client.initialize()
    payload = json.loads(client.call_tool("echo_debug", {"message": "hello"}))
    assert payload == {"echo": "hello"}


def test_tool_layer_returns_structured_results() -> None:
    success = call_tool("echo_debug", {"message": "hello"})
    failure = call_tool("does-not-exist", {})
    invalid = call_tool("kb_search", {"query": "", "top_k": "bad"})
    assert success == ToolResult.success('{"echo": "hello"}')
    assert failure.is_error is True
    assert invalid.is_error is True


def test_all_knowledge_tools_success_and_validation() -> None:
    search = call_tool("kb_search", {"query": "MCP", "top_k": 2})
    fetched = call_tool("kb_get", {"id": "kb-mcp"})
    compared = call_tool("kb_compare", {"left_id": "kb-react", "right_id": "kb-mcp"})
    assert json.loads(search.text)[0]["id"] == "kb-mcp"
    assert json.loads(fetched.text)["title"] == "Model Context Protocol"
    assert json.loads(compared.text)["left"]["id"] == "kb-react"
    assert call_tool("kb_search", {"query": "MCP", "top_k": 0}).is_error
    assert call_tool("kb_get", {}).is_error
    assert call_tool("kb_compare", {"left_id": 1, "right_id": "kb-mcp"}).is_error
    assert call_tool("kb_compare", {"left_id": "missing", "right_id": "kb-mcp"}).is_error
    assert call_tool("echo_debug", {"message": 1}).is_error
