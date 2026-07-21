"""Tests for MCP Knowledge Bridge server handle function."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mcp_bridge.server import handle


def test_initialize():
    resp = handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert resp is not None
    assert resp["result"]["serverInfo"]["name"] == "mcp-knowledge-bridge"
    assert "tools" in resp["result"]["capabilities"]
    assert "resources" in resp["result"]["capabilities"]
    assert "prompts" in resp["result"]["capabilities"]


def test_tools_list():
    resp = handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    assert resp is not None
    tools = resp["result"]["tools"]
    assert len(tools) >= 3
    names = [t["name"] for t in tools]
    assert "kb_search" in names
    assert "kb_get" in names
    assert "kb_compare" in names


def test_tools_call_kb_search():
    resp = handle({
        "jsonrpc": "2.0", "id": 3, "method": "tools/call",
        "params": {"name": "kb_search", "arguments": {"query": "MCP", "top_k": 2}}
    })
    assert resp is not None
    assert "content" in resp["result"]
    text = resp["result"]["content"][0]["text"]
    assert "MCP" in text or "mcp" in text.lower()


def test_tools_call_kb_get():
    resp = handle({
        "jsonrpc": "2.0", "id": 4, "method": "tools/call",
        "params": {"name": "kb_get", "arguments": {"id": "kb-mcp"}}
    })
    assert resp is not None
    text = resp["result"]["content"][0]["text"]
    assert "mcp" in text.lower()


def test_tools_call_kb_compare():
    resp = handle({
        "jsonrpc": "2.0", "id": 5, "method": "tools/call",
        "params": {"name": "kb_compare", "arguments": {"left_id": "kb-react", "right_id": "kb-mcp"}}
    })
    assert resp is not None
    text = resp["result"]["content"][0]["text"]
    assert "shared_terms" in text.lower()


def test_tools_call_echo():
    resp = handle({
        "jsonrpc": "2.0", "id": 6, "method": "tools/call",
        "params": {"name": "echo_debug", "arguments": {"message": "hello"}}
    })
    assert resp is not None
    assert "hello" in resp["result"]["content"][0]["text"]


def test_resources_list():
    resp = handle({"jsonrpc": "2.0", "id": 7, "method": "resources/list"})
    assert resp is not None
    resources = resp["result"]["resources"]
    assert len(resources) > 0
    assert "uri" in resources[0]


def test_resources_read():
    resources = handle({"jsonrpc": "2.0", "id": 8, "method": "resources/list"})
    uri = resources["result"]["resources"][0]["uri"]
    resp = handle({"jsonrpc": "2.0", "id": 9, "method": "resources/read", "params": {"uri": uri}})
    assert resp is not None
    assert "contents" in resp["result"]
    assert len(resp["result"]["contents"][0]["text"]) > 0


def test_prompts_list():
    resp = handle({"jsonrpc": "2.0", "id": 10, "method": "prompts/list"})
    assert resp is not None
    prompts = resp["result"]["prompts"]
    names = [p["name"] for p in prompts]
    assert "research_brief" in names


def test_prompts_get():
    resp = handle({"jsonrpc": "2.0", "id": 11, "method": "prompts/get", "params": {"name": "research_brief", "arguments": {"topic": "MCP"}}})
    assert resp is not None
    messages = resp["result"]["messages"]
    assert len(messages) == 1
    assert "MCP" in messages[0]["content"]["text"]


def test_ping():
    resp = handle({"jsonrpc": "2.0", "id": 12, "method": "ping"})
    assert resp is not None
    assert resp["result"] == {}


def test_unknown_method():
    resp = handle({"jsonrpc": "2.0", "id": 13, "method": "nonexistent"})
    assert resp is not None
    assert "error" in resp
    assert resp["error"]["code"] == -32601


def test_notification_returns_none():
    resp = handle({"jsonrpc": "2.0", "method": "notifications/initialized"})
    assert resp is None
