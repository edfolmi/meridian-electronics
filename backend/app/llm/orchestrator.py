import logging
import time
from typing import Any

from openai import AsyncOpenAI, OpenAIError

from app.core.config import Settings
from app.llm.prompts import SYSTEM_PROMPT
from app.llm.tools import format_tool_result, mcp_tool_to_openai, parse_tool_arguments
from app.mcp.client import McpClient, McpError, new_request_id
from app.schemas.auth import CustomerSession
from app.schemas.chat import ChatMessage, ChatResponse, ToolCallSummary

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 4
CHAT_BLOCKED_TOOLS = {"verify_customer_pin"}
CUSTOMER_REQUIRED_TOOLS = {"get_customer", "list_orders", "get_order", "create_order"}


class ChatOrchestrationError(RuntimeError):
    pass


class ChatOrchestrator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.mcp_client = McpClient(settings.mcp_server_url)
        self.openai_client = AsyncOpenAI(
            api_key=settings.openrouter_api_key or "missing",
            base_url=settings.openrouter_base_url,
        )

    async def respond(
        self,
        messages: list[ChatMessage],
        customer: CustomerSession | None,
    ) -> ChatResponse:
        request_id = new_request_id()
        if not self.settings.openrouter_api_key:
            raise ChatOrchestrationError("OPENROUTER_API_KEY is not configured")

        started = time.perf_counter()
        tool_summaries: list[ToolCallSummary] = []
        mcp_tools = await self._discover_tools()
        llm_messages = self._build_messages(messages, customer)
        openai_tools = [mcp_tool_to_openai(tool) for tool in mcp_tools]

        for _round in range(MAX_TOOL_ROUNDS):
            completion = await self._chat_completion(llm_messages, openai_tools)
            message = completion.choices[0].message
            tool_calls = message.tool_calls or []

            if not tool_calls:
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                logger.info(
                    "chat request_id=%s completed latency_ms=%s tools=%s",
                    request_id,
                    elapsed_ms,
                    [summary.name for summary in tool_summaries],
                )
                return ChatResponse(
                    message=message.content or "",
                    request_id=request_id,
                    tool_calls=tool_summaries,
                )

            llm_messages.append(
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": "function",
                            "function": {
                                "name": call.function.name,
                                "arguments": call.function.arguments,
                            },
                        }
                        for call in tool_calls
                    ],
                }
            )
            for call in tool_calls:
                tool_started = time.perf_counter()
                tool_name = call.function.name
                try:
                    arguments = parse_tool_arguments(call.function.arguments)
                    self._validate_tool_call(tool_name, arguments, customer)
                    result = await self.mcp_client.call_tool(tool_name, arguments)
                    content = format_tool_result(result)
                    ok = not bool(result.get("isError"))
                except (ValueError, McpError) as exc:
                    content = f"Tool call failed: {exc}"
                    ok = False

                latency_ms = int((time.perf_counter() - tool_started) * 1000)
                tool_summaries.append(
                    ToolCallSummary(
                        name=tool_name,
                        ok=ok,
                        latency_ms=latency_ms,
                    )
                )
                logger.info(
                    "tool request_id=%s name=%s ok=%s latency_ms=%s",
                    request_id,
                    tool_name,
                    ok,
                    latency_ms,
                )
                llm_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "name": tool_name,
                        "content": content,
                    }
                )

        raise ChatOrchestrationError("The assistant used too many tool-call rounds")

    async def _discover_tools(self) -> list[Any]:
        try:
            tools = await self.mcp_client.list_tools()
            return [tool for tool in tools if tool.name not in CHAT_BLOCKED_TOOLS]
        except McpError as exc:
            raise ChatOrchestrationError(f"Could not reach Meridian MCP tools: {exc}") from exc

    async def _chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> Any:
        try:
            return await self.openai_client.chat.completions.create(
                model=self.settings.openrouter_model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.2,
            )
        except OpenAIError as exc:
            raise ChatOrchestrationError(f"LLM request failed: {exc}") from exc

    def _build_messages(
        self,
        messages: list[ChatMessage],
        customer: CustomerSession | None,
    ) -> list[dict[str, Any]]:
        auth_context = self._auth_context_message(customer)
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": auth_context},
            *[
                {"role": message.role, "content": message.content}
                for message in messages
            ],
        ]

    def _auth_context_message(self, customer: CustomerSession | None) -> str:
        if customer:
            return (
                "Customer is authenticated. Safe customer context: "
                f"customer_id={customer.customer_id}; "
                f"name={customer.name}. "
                "No PIN or credential secret is available."
            )
        return (
            "Customer is not authenticated. For order history, order placement, "
            "or account-specific questions, ask the user to use the secure "
            "sign-in form in the app. Do not ask for credentials in chat."
        )

    def _validate_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        customer: CustomerSession | None,
    ) -> None:
        if tool_name in CHAT_BLOCKED_TOOLS:
            raise ValueError("Authentication tools are not available in chat")

        if tool_name not in CUSTOMER_REQUIRED_TOOLS:
            return

        if not customer:
            raise ValueError("Customer must sign in before account-specific tools run")

        if tool_name in {"get_customer", "list_orders", "create_order"}:
            provided_customer_id = arguments.get("customer_id")
            if provided_customer_id and provided_customer_id != customer.customer_id:
                raise ValueError("Tool call customer_id does not match signed-in customer")
            arguments["customer_id"] = customer.customer_id
