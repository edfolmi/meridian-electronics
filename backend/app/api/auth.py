import re

from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.llm.tools import format_tool_result
from app.mcp.client import McpClient, McpError
from app.schemas.auth import AuthRequest, AuthResponse, CustomerSession

router = APIRouter()


@router.post("/auth/sign-in", response_model=AuthResponse)
async def sign_in(request: AuthRequest) -> AuthResponse:
    client = McpClient(get_settings().mcp_server_url)
    try:
        result = await client.call_tool(
            "verify_customer_pin",
            {"email": str(request.email), "pin": request.pin},
        )
    except McpError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not verify customer credentials: {exc}",
        ) from exc

    text = format_tool_result(result)
    if result.get("isError"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or PIN could not be verified.",
        )

    customer = _parse_customer(text)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="MCP verification response did not include customer context.",
        )

    return AuthResponse(
        ok=True,
        customer=customer,
        message="Signed in successfully.",
    )


def _parse_customer(text: str) -> CustomerSession | None:
    name = _match(r"Customer verified:\s*(.+)", text)
    customer_id = _match(r"Customer ID:\s*([a-f0-9-]+)", text)
    email = _match(r"Email:\s*(\S+)", text)
    role = _match(r"Role:\s*(.+)", text)

    if not name or not customer_id or not email:
        return None

    return CustomerSession(
        customer_id=customer_id,
        name=name.strip(),
        email=email.strip(),
        role=role.strip() if role else None,
    )


def _match(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1) if match else None

