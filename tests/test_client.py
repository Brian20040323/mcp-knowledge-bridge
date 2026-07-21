"""Tests for LocalMCPClient."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mcp_bridge.client import LocalMCPClient


def test_client_initialize():
    c = LocalMCPClient()
    info = c.initialize()
    assert info["serverInfo"]["name"] == "mcp-knowledge-bridge"


def test_client_list_tools():
    c = LocalMCPClient()
    tools = c.list_tools()
    names = [t["name"] for t in tools]
    assert "kb_search" in names


def test_client_call_tool():
    c = LocalMCPClient()
    result = c.call_tool("kb_search", {"query": "MCP"})
    assert "MCP" in result or "mcp" in result.lower()


def test_client_list_resources():
    c = LocalMCPClient()
    resources = c.list_resources()
    assert len(resources) > 0


def test_client_read_resource():
    c = LocalMCPClient()
    resources = c.list_resources()
    uri = resources[0]["uri"]
    content = c.read_resource(uri)
    assert len(content) > 0


def test_client_list_prompts():
    c = LocalMCPClient()
    prompts = c.list_prompts()
    assert len(prompts) > 0


def test_client_get_prompt():
    c = LocalMCPClient()
    prompt = c.get_prompt("research_brief", {"topic": "test"})
    assert "messages" in prompt
