from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

import pytest

from mcp_bridge.http_server import bearer_token_matches, create_server


def test_bearer_auth_requires_exact_header() -> None:
    assert bearer_token_matches("Bearer secret", "secret")
    assert not bearer_token_matches(None, "secret")
    assert not bearer_token_matches("Basic secret", "secret")
    assert not bearer_token_matches("Bearer wrong", "secret")
    assert not bearer_token_matches("Bearer secret", "")


def test_server_rejects_empty_token() -> None:
    with pytest.raises(ValueError, match="MCP_BRIDGE_TOKEN"):
        create_server("127.0.0.1", 0, "")


@pytest.fixture
def rest_url() -> str:
    server = create_server("127.0.0.1", 0, "test-token")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def get_json(url: str, token: str | None = None) -> tuple[int, dict]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        return exc.code, json.load(exc)


def post_json(url: str, payload: object, token: str) -> tuple[int, dict]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        return exc.code, json.load(exc)


def test_health_is_public_but_api_requires_header(rest_url: str) -> None:
    assert get_json(f"{rest_url}/health") == (200, {"ok": True, "auth_required": True})
    assert get_json(f"{rest_url}/tools")[0] == 401
    assert get_json(f"{rest_url}/tools?token=test-token")[0] == 401
    assert get_json(f"{rest_url}/tools", "test-token")[0] == 200
    assert get_json(f"{rest_url}/resources", "test-token")[0] == 200
    assert get_json(f"{rest_url}/prompts", "test-token")[0] == 200
    assert get_json(f"{rest_url}/missing", "test-token")[0] == 404


def test_rest_tool_result_exposes_error_flag(rest_url: str) -> None:
    status, success = post_json(
        f"{rest_url}/tools/call",
        {"name": "echo_debug", "arguments": {"message": "ok"}},
        "test-token",
    )
    _, failure = post_json(
        f"{rest_url}/tools/call",
        {"name": "kb_get", "arguments": {"id": "missing"}},
        "test-token",
    )
    assert status == 200
    assert success["isError"] is False
    assert failure["isError"] is True


def test_rest_rejects_bad_request_shape(rest_url: str) -> None:
    status, body = post_json(f"{rest_url}/tools/call", [], "test-token")
    assert status == 400
    assert "object" in body["error"]
    assert post_json(f"{rest_url}/tools/call", {"name": 1}, "test-token")[0] == 400
    assert post_json(f"{rest_url}/missing", {}, "test-token")[0] == 404


def test_rest_reads_resources_and_reports_missing(rest_url: str) -> None:
    _, resources = get_json(f"{rest_url}/resources", "test-token")
    uri = resources["resources"][0]["uri"]
    status, found = post_json(f"{rest_url}/resources/read", {"uri": uri}, "test-token")
    missing_status, _ = post_json(
        f"{rest_url}/resources/read",
        {"uri": "kb://missing"},
        "test-token",
    )
    assert status == 200
    assert found["uri"] == uri
    assert missing_status == 404


def test_rest_rejects_malformed_json_and_unauthorized_post(rest_url: str) -> None:
    malformed = urllib.request.Request(
        f"{rest_url}/tools/call",
        data=b"{bad",
        headers={"Authorization": "Bearer test-token"},
        method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(malformed)
    assert exc_info.value.code == 400

    unauthorized = urllib.request.Request(
        f"{rest_url}/tools/call",
        data=b"{}",
        method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(unauthorized)
    assert exc_info.value.code == 401
