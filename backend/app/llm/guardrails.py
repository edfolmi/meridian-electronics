import json
import logging
from dataclasses import dataclass

from openai import AsyncOpenAI, OpenAIError

from app.core.config import Settings
from app.schemas.chat import ChatMessage

logger = logging.getLogger(__name__)

ACCOUNT_INTENT_PROMPT = """Classify whether the latest customer message requires signed-in account context.

Return only JSON with:
- requires_auth: boolean
- reason: short string

requires_auth should be true for order history, order lookup, placing orders, customer profile, invoices, payments, shipping for a specific customer, or any account-specific support.
requires_auth should be false for general product availability, product search, store policy, and generic troubleshooting.
"""


@dataclass(frozen=True)
class SafetyDecision:
    allowed: bool
    reason: str


@dataclass(frozen=True)
class IntentDecision:
    requires_auth: bool
    reason: str


class GuardrailService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = AsyncOpenAI(
            api_key=settings.openrouter_api_key or "missing",
            base_url=settings.openrouter_base_url,
        )

    async def check_input(self, message: str) -> SafetyDecision:
        if not self._enabled():
            return SafetyDecision(allowed=True, reason="guardrails disabled")

        try:
            response = await self.client.chat.completions.create(
                model=self.settings.openrouter_guardrail_model,
                messages=[{"role": "user", "content": message}],
                temperature=0,
            )
        except OpenAIError as exc:
            logger.warning("guardrail unavailable: %s", exc.__class__.__name__)
            return SafetyDecision(allowed=False, reason="guardrail unavailable")

        verdict = (response.choices[0].message.content or "").strip().lower()
        if verdict.startswith("unsafe") and self.settings.safety_guardrail_enforce:
            return SafetyDecision(allowed=False, reason="llama guard blocked input")
        return SafetyDecision(allowed=True, reason="safe")

    async def evaluate_account_intent(
        self,
        messages: list[ChatMessage],
    ) -> IntentDecision:
        if not self._enabled():
            return IntentDecision(requires_auth=False, reason="guardrails disabled")

        latest_user_message = next(
            (message.content for message in reversed(messages) if message.role == "user"),
            "",
        )
        if not latest_user_message:
            return IntentDecision(requires_auth=False, reason="no user message")

        try:
            response = await self.client.chat.completions.create(
                model=self.settings.openrouter_evaluator_model,
                messages=[
                    {"role": "system", "content": ACCOUNT_INTENT_PROMPT},
                    {"role": "user", "content": latest_user_message},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
        except OpenAIError as exc:
            logger.warning("intent evaluator unavailable: %s", exc.__class__.__name__)
            return self._keyword_account_intent(latest_user_message)

        content = response.choices[0].message.content or "{}"
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return self._keyword_account_intent(latest_user_message)

        return IntentDecision(
            requires_auth=bool(parsed.get("requires_auth")),
            reason=str(parsed.get("reason") or "classified by evaluator"),
        )

    def _enabled(self) -> bool:
        return self.settings.guardrails_enabled and bool(self.settings.openrouter_api_key)

    def _keyword_account_intent(self, message: str) -> IntentDecision:
        text = message.lower()
        keywords = (
            "my order",
            "my recent order",
            "order history",
            "recent orders",
            "track my",
            "my account",
            "invoice",
            "payment",
            "shipping status",
            "place an order",
            "create order",
        )
        return IntentDecision(
            requires_auth=any(keyword in text for keyword in keywords),
            reason="keyword fallback",
        )
