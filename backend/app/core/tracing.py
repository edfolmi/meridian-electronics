import logging
from contextlib import nullcontext
from typing import Any

from app.core.config import Settings

logger = logging.getLogger(__name__)

try:
    from agents import custom_span, guardrail_span, set_tracing_export_api_key, trace
except ImportError:  # pragma: no cover - optional dependency path
    custom_span = None
    guardrail_span = None
    set_tracing_export_api_key = None
    trace = None


def tracing_enabled(settings: Settings) -> bool:
    return (
        settings.openai_tracing_enabled
        and bool(settings.openai_api_key)
        and trace is not None
        and set_tracing_export_api_key is not None
    )


def chat_trace(settings: Settings, request_id: str, authenticated: bool):
    if not tracing_enabled(settings):
        return nullcontext()

    try:
        set_tracing_export_api_key(settings.openai_api_key)
        return trace(
            "Meridian support chat",
            group_id=request_id,
            metadata={
                "request_id": request_id,
                "authenticated": authenticated,
                "sensitive_data_included": False,
            },
        )
    except Exception as exc:  # pragma: no cover - defensive optional integration
        logger.warning("OpenAI tracing disabled after setup error: %s", exc.__class__.__name__)
        return nullcontext()


def safe_custom_span(name: str, data: dict[str, Any] | None = None):
    if custom_span is None:
        return nullcontext()
    return custom_span(name, data or {})


def safe_guardrail_span(name: str, triggered: bool):
    if guardrail_span is None:
        return nullcontext()
    return guardrail_span(name, triggered=triggered)

