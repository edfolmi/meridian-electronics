from typing import Any

from pydantic import BaseModel


class ToolInfo(BaseModel):
    name: str
    description: str = ""
    input_schema: dict[str, Any]


class ToolDiscoveryResponse(BaseModel):
    ok: bool
    tools: list[ToolInfo] = []
    error: str | None = None

