import httpx
import pytest

from app.mcp.client import McpClient, McpError


def test_decode_json_response() -> None:
    response = httpx.Response(200, json={"jsonrpc": "2.0", "result": {"tools": []}})
    assert McpClient("https://example.test")._decode_response(response) == {"jsonrpc": "2.0", "result": {"tools": []}}


def test_decode_sse_response() -> None:
    response = httpx.Response(
        200,
        headers={"content-type": "text/event-stream"},
        text='event: message\ndata: {"jsonrpc":"2.0","result":{"ok":true}}\n\n',
    )

    assert McpClient("https://example.test")._decode_response(response) == {
        "jsonrpc": "2.0",
        "result": {"ok": True},
    }


def test_decode_sse_response_rejects_unreadable_stream() -> None:
    response = httpx.Response(
        200,
        headers={"content-type": "text/event-stream"},
        text="event: ping\n\n",
    )

    with pytest.raises(McpError):
        McpClient("https://example.test")._decode_response(response)

