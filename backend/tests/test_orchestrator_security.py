from app.core.config import Settings
from app.llm.orchestrator import ChatOrchestrator
from app.mcp.client import McpTool
from app.schemas.auth import CustomerSession
from app.schemas.chat import ChatMessage


def test_auth_tool_is_not_exposed_to_chat() -> None:
    orchestrator = ChatOrchestrator(Settings(OPENROUTER_API_KEY="test"))

    class FakeMcpClient:
        async def list_tools(self):
            return [
                McpTool("verify_customer_pin", "Verify PIN", {"type": "object"}),
                McpTool("search_products", "Search products", {"type": "object"}),
            ]

    orchestrator.mcp_client = FakeMcpClient()

    tools = _run(orchestrator._discover_tools())

    assert [tool.name for tool in tools] == ["search_products"]


def test_llm_auth_context_excludes_email_and_pin() -> None:
    orchestrator = ChatOrchestrator(Settings(OPENROUTER_API_KEY="test"))
    customer = CustomerSession(
        customer_id="41c2903a-f1a5-47b7-a81d-86b50ade220f",
        name="Donald Garcia",
        email="donaldgarcia@example.net",
        role="admin",
    )

    messages = orchestrator._build_messages(
        [ChatMessage(role="user", content="Show my orders")],
        customer,
    )
    context = messages[1]["content"]

    assert "41c2903a-f1a5-47b7-a81d-86b50ade220f" in context
    assert "Donald Garcia" in context
    assert "donaldgarcia@example.net" not in context
    assert "PIN" in context


def test_account_intent_blocks_unauthenticated_customer_history() -> None:
    orchestrator = ChatOrchestrator(Settings(OPENROUTER_API_KEY="test"))
    orchestrator.guardrails = FakeGuardrails(requires_auth=True)

    response = _run(
        orchestrator._respond_with_trace(
            "req123",
            [ChatMessage(role="user", content="Show my recent orders")],
            customer=None,
        )
    )

    assert "secure sign-in form" in response.message


def test_safety_guardrail_blocks_before_tool_discovery() -> None:
    orchestrator = ChatOrchestrator(Settings(OPENROUTER_API_KEY="test"))
    orchestrator.guardrails = FakeGuardrails(allowed=False)

    response = _run(
        orchestrator._respond_with_trace(
            "req123",
            [ChatMessage(role="user", content="unsafe request")],
            customer=None,
        )
    )

    assert "cannot help" in response.message


def _run(coro):
    import asyncio

    return asyncio.run(coro)


class FakeDecision:
    def __init__(self, allowed=True, requires_auth=False) -> None:
        self.allowed = allowed
        self.requires_auth = requires_auth
        self.reason = "test"


class FakeGuardrails:
    def __init__(self, allowed=True, requires_auth=False) -> None:
        self.allowed = allowed
        self.requires_auth = requires_auth

    async def check_input(self, _message):
        return FakeDecision(allowed=self.allowed)

    async def evaluate_account_intent(self, _messages):
        return FakeDecision(requires_auth=self.requires_auth)
