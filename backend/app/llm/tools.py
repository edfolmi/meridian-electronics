import json
from typing import Any

from app.mcp.client import McpTool

MAX_TOOL_RESULT_CHARS = 5000


def mcp_tool_to_openai(tool: McpTool) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or f"Call Meridian MCP tool {tool.name}.",
            "parameters": tool.input_schema or {"type": "object", "properties": {}},
        },
    }


def parse_tool_arguments(raw_arguments: str | None) -> dict[str, Any]:
    if not raw_arguments:
        return {}
    parsed = json.loads(raw_arguments)
    if not isinstance(parsed, dict):
        raise ValueError("Tool arguments must be a JSON object")
    return parsed


def format_tool_result(result: dict[str, Any]) -> str:
    if "content" in result and isinstance(result["content"], list):
        text_parts = [
            item.get("text", "")
            for item in result["content"]
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        if text_parts:
            return _truncate("\n".join(text_parts))

    if "structuredContent" in result:
        return _truncate(json.dumps(result["structuredContent"], ensure_ascii=True))

    if "result" in result:
        return _truncate(str(result["result"]))

    return _truncate(json.dumps(result, ensure_ascii=True))


def _truncate(value: str) -> str:
    if len(value) <= MAX_TOOL_RESULT_CHARS:
        return value
    return f"{value[:MAX_TOOL_RESULT_CHARS]}... [truncated]"

