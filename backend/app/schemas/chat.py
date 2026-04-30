from pydantic import BaseModel, Field

from app.schemas.auth import CustomerSession


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=6000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=30)
    customer: CustomerSession | None = None


class ToolCallSummary(BaseModel):
    name: str
    ok: bool
    latency_ms: int


class ChatResponse(BaseModel):
    message: str
    request_id: str
    tool_calls: list[ToolCallSummary] = []


class ChatErrorResponse(BaseModel):
    message: str
    request_id: str | None = None
