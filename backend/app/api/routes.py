from fastapi import APIRouter, HTTPException, status

from app.api.auth import router as auth_router
from app.core.config import get_settings
from app.core.tracing import tracing_status
from app.llm.orchestrator import ChatOrchestrationError, ChatOrchestrator
from app.mcp.client import McpClient, McpError
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.mcp import ToolDiscoveryResponse, ToolInfo

router = APIRouter()
router.include_router(auth_router)


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "meridian-support-api"}


@router.get("/tracing/status")
async def get_tracing_status() -> dict[str, bool | str]:
    return tracing_status(get_settings())


@router.get("/mcp/tools", response_model=ToolDiscoveryResponse)
async def list_mcp_tools() -> ToolDiscoveryResponse:
    settings = get_settings()
    client = McpClient(settings.mcp_server_url)
    try:
        tools = await client.list_tools()
    except McpError as exc:
        return ToolDiscoveryResponse(ok=False, error=str(exc))
    return ToolDiscoveryResponse(
        ok=True,
        tools=[
            ToolInfo(
                name=tool.name,
                description=tool.description,
                input_schema=tool.input_schema,
            )
            for tool in tools
        ],
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    settings = get_settings()
    orchestrator = ChatOrchestrator(settings)
    try:
        return await orchestrator.respond(request.messages, request.customer)
    except ChatOrchestrationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
