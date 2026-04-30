import json
import logging
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import httpx

logger = logging.getLogger(__name__)


class McpError(RuntimeError):
    """Raised when the MCP server returns an error or cannot be reached."""


@dataclass(frozen=True)
class McpTool:
    name: str
    description: str
    input_schema: dict[str, Any]


class McpClient:
    def __init__(self, server_url: str, timeout: float = 20.0) -> None:
        self.server_url = server_url
        self.timeout = timeout
        self._request_id = 0

    async def list_tools(self) -> list[McpTool]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            session_id = await self._initialize(client)
            await self._send_initialized(client, session_id)
            response = await self._request(client, "tools/list", {}, session_id)

        tools = response.get("tools", [])
        discovered = [
            McpTool(
                name=tool["name"],
                description=tool.get("description", ""),
                input_schema=tool.get("inputSchema", {"type": "object"}),
            )
            for tool in tools
            if "name" in tool
        ]
        logger.info("Discovered MCP tools: %s", [tool.name for tool in discovered])
        return discovered

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            session_id = await self._initialize(client)
            await self._send_initialized(client, session_id)
            return await self._request(
                client,
                "tools/call",
                {"name": name, "arguments": arguments},
                session_id,
            )

    async def _initialize(self, client: httpx.AsyncClient) -> str | None:
        result, headers = await self._raw_request(
            client,
            "initialize",
            {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {
                    "name": "meridian-support-backend",
                    "version": "0.1.0",
                },
            },
            session_id=None,
        )
        session_id = headers.get("mcp-session-id")
        logger.debug("MCP initialize response keys: %s", list(result.keys()))
        return session_id

    async def _send_initialized(
        self,
        client: httpx.AsyncClient,
        session_id: str | None,
    ) -> None:
        payload = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }
        await self._post(client, payload, session_id)

    async def _request(
        self,
        client: httpx.AsyncClient,
        method: str,
        params: dict[str, Any],
        session_id: str | None,
    ) -> dict[str, Any]:
        result, _headers = await self._raw_request(client, method, params, session_id)
        return result

    async def _raw_request(
        self,
        client: httpx.AsyncClient,
        method: str,
        params: dict[str, Any],
        session_id: str | None,
    ) -> tuple[dict[str, Any], httpx.Headers]:
        self._request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        }
        response = await self._post(client, payload, session_id)
        body = self._decode_response(response)

        if "error" in body:
            raise McpError(f"MCP {method} failed: {body['error']}")
        result = body.get("result")
        if not isinstance(result, dict):
            raise McpError(f"MCP {method} returned an unexpected response")
        return result, response.headers

    async def _post(
        self,
        client: httpx.AsyncClient,
        payload: dict[str, Any],
        session_id: str | None,
    ) -> httpx.Response:
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "MCP-Protocol-Version": "2025-03-26",
        }
        if session_id:
            headers["Mcp-Session-Id"] = session_id

        try:
            response = await client.post(self.server_url, headers=headers, json=payload)
            response.raise_for_status()
            return response
        except httpx.HTTPError as exc:
            raise McpError(f"MCP server request failed: {exc}") from exc

    def _decode_response(self, response: httpx.Response) -> dict[str, Any]:
        content_type = response.headers.get("content-type", "")
        if "text/event-stream" in content_type:
            return self._decode_sse(response.text)
        try:
            body = response.json()
        except json.JSONDecodeError as exc:
            raise McpError("MCP server returned invalid JSON") from exc
        if not isinstance(body, dict):
            raise McpError("MCP server returned a non-object JSON response")
        return body

    def _decode_sse(self, text: str) -> dict[str, Any]:
        for event in text.split("\n\n"):
            data_lines = [
                line.removeprefix("data:").strip()
                for line in event.splitlines()
                if line.startswith("data:")
            ]
            if not data_lines:
                continue
            try:
                body = json.loads("\n".join(data_lines))
            except json.JSONDecodeError:
                continue
            if isinstance(body, dict) and ("result" in body or "error" in body):
                return body
        raise McpError("MCP server returned an unreadable event-stream response")


def new_request_id() -> str:
    return uuid4().hex[:12]

