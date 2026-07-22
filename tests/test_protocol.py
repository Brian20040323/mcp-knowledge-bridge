from __future__ import annotations

import io
import json

import pytest

from mcp_bridge.server import PROTOCOL_VERSION, MCPServer, serve


def request(method: str, params: object = None, request_id: object = 1) -> dict:
    message = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        message["params"] = params
    return message


def ready_server() -> MCPServer:
    server = MCPServer()
    response = server.handle(
        request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "pytest", "version": "1"},
            },
        )
    )
    assert response and response["result"]["protocolVersion"] == PROTOCOL_VERSION
    assert server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    return server


def error_code(response: dict | None) -> int:
    assert response is not None
    return response["error"]["code"]


def test_initialize_lifecycle_and_capabilities() -> None:
    server = MCPServer()
    assert error_code(server.handle(request("tools/list"))) == -32600
    initialized = server.handle(
        request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "test"},
            },
        )
    )
    assert initialized is not None
    assert set(initialized["result"]["capabilities"]) == {"tools", "resources", "prompts"}
    assert error_code(server.handle(request("tools/list", request_id=2))) == -32600
    server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"})
    assert "result" in server.handle(request("tools/list", request_id=3))
    assert error_code(server.handle(request("initialize", {}, 4))) == -32600


def test_ping_is_allowed_during_lifecycle() -> None:
    assert MCPServer().handle(request("ping")) == {"jsonrpc": "2.0", "id": 1, "result": {}}
    assert MCPServer().handle({"jsonrpc": "2.0", "method": "ping"}) is None


@pytest.mark.parametrize(
    "message",
    [
        [],
        {"jsonrpc": "1.0", "id": 1, "method": "ping"},
        {"jsonrpc": "2.0", "id": True, "method": "ping"},
        {"jsonrpc": "2.0", "id": 1, "method": 4},
        {"jsonrpc": "2.0", "id": 1, "method": "ping", "params": "bad"},
    ],
)
def test_invalid_request_shapes(message: object) -> None:
    assert error_code(MCPServer().handle(message)) == -32600


def test_invalid_request_notification_has_no_response() -> None:
    assert MCPServer().handle({"jsonrpc": "1.0", "method": "ping"}) is None


def test_method_not_found() -> None:
    response = ready_server().handle(request("missing/method"))
    assert error_code(response) == -32601


@pytest.mark.parametrize(
    ("method", "params"),
    [
        ("tools/call", {"name": 3, "arguments": {}}),
        ("tools/call", {"name": "kb_get", "arguments": []}),
        ("resources/read", {"uri": 3}),
        ("prompts/get", {"name": "research_brief", "arguments": []}),
        ("tools/list", []),
    ],
)
def test_invalid_params(method: str, params: object) -> None:
    assert error_code(ready_server().handle(request(method, params))) == -32602


def test_protocol_version_rejected() -> None:
    response = MCPServer().handle(
        request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "old"},
            },
        )
    )
    assert error_code(response) == -32602


def test_notifications_never_receive_responses() -> None:
    server = ready_server()
    assert server.handle({"jsonrpc": "2.0", "method": "missing/method"}) is None
    assert server.handle({"jsonrpc": "2.0", "method": "tools/call", "params": []}) is None


def test_tool_success_and_error_are_explicit() -> None:
    server = ready_server()
    success = server.handle(request("tools/call", {"name": "echo_debug", "arguments": {"message": "ok"}}))
    failure = server.handle(request("tools/call", {"name": "kb_get", "arguments": {"id": "missing"}}, 2))
    assert success and success["result"]["isError"] is False
    assert failure and failure["result"]["isError"] is True
    assert "not found" in failure["result"]["content"][0]["text"]


def test_domain_not_found_errors_are_preserved() -> None:
    server = ready_server()
    resource = server.handle(request("resources/read", {"uri": "kb://missing"}))
    prompt = server.handle(request("prompts/get", {"name": "missing", "arguments": {}}, 2))
    assert error_code(resource) == -32002
    assert error_code(prompt) == -32002


def test_newline_transport_unicode_parse_error_and_recovery() -> None:
    messages = [
        request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "测试"},
            },
        ),
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        request("tools/call", {"name": "echo_debug", "arguments": {"message": "你好 🌍"}}, 2),
    ]
    wire = (
        json.dumps(messages[0], ensure_ascii=False).encode()
        + b"\n{broken json\n"
        + json.dumps(messages[1]).encode()
        + b"\n"
        + json.dumps(messages[2], ensure_ascii=False).encode()
        + b"\n"
    )
    output = io.BytesIO()
    serve(io.BytesIO(wire), output)
    raw_lines = output.getvalue().splitlines()
    assert len(raw_lines) == 3
    responses = [json.loads(line) for line in raw_lines]
    assert responses[1]["error"]["code"] == -32700
    assert "你好 🌍" in responses[2]["result"]["content"][0]["text"]
    assert b"Content-Length" not in output.getvalue()
