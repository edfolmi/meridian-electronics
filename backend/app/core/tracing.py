import logging
from contextlib import ExitStack, contextmanager, nullcontext
from typing import Any

from app.core.config import Settings

logger = logging.getLogger(__name__)

try:
    from agents import (
        custom_span,
        flush_traces,
        gen_trace_id,
        guardrail_span,
        set_tracing_export_api_key,
        set_tracing_disabled,
        trace,
    )
except ImportError:  # pragma: no cover - optional dependency path
    custom_span = None
    flush_traces = None
    gen_trace_id = None
    guardrail_span = None
    set_tracing_export_api_key = None
    set_tracing_disabled = None
    trace = None

try:
    from langfuse import Langfuse, get_client
except ImportError:  # pragma: no cover - optional dependency path
    Langfuse = None
    get_client = None


def tracing_enabled(settings: Settings) -> bool:
    return openai_tracing_enabled(settings) or langfuse_tracing_enabled(settings)


def openai_tracing_enabled(settings: Settings) -> bool:
    return (
        settings.openai_tracing_enabled
        and bool(settings.openai_api_key)
        and trace is not None
        and set_tracing_export_api_key is not None
    )


def langfuse_tracing_enabled(settings: Settings) -> bool:
    return (
        settings.langfuse_tracing_enabled
        and bool(settings.langfuse_public_key)
        and bool(settings.langfuse_secret_key)
        and Langfuse is not None
        and get_client is not None
    )


def chat_trace(settings: Settings, request_id: str, authenticated: bool):
    if not tracing_enabled(settings):
        return nullcontext()

    return _combined_chat_trace(settings, request_id, authenticated)


@contextmanager
def _combined_chat_trace(settings: Settings, request_id: str, authenticated: bool):
    with ExitStack() as stack:
        if openai_tracing_enabled(settings):
            stack.enter_context(_openai_chat_trace(settings, request_id, authenticated))
        if langfuse_tracing_enabled(settings):
            stack.enter_context(_langfuse_chat_trace(settings, request_id, authenticated))
        yield


@contextmanager
def _openai_chat_trace(settings: Settings, request_id: str, authenticated: bool):
    try:
        set_tracing_export_api_key(settings.openai_api_key)
        if set_tracing_disabled is not None:
            set_tracing_disabled(False)
        trace_id = gen_trace_id() if gen_trace_id is not None else None
        with trace(
            "Meridian support chat",
            trace_id=trace_id,
            group_id=request_id,
            metadata={
                "request_id": request_id,
                "authenticated": authenticated,
                "sensitive_data_included": False,
            },
        ):
            yield
    except Exception as exc:  # pragma: no cover - defensive optional integration
        logger.warning("OpenAI tracing disabled after setup error: %s", exc.__class__.__name__)
        yield
    finally:
        if flush_traces is not None:
            try:
                flush_traces()
            except Exception as exc:  # pragma: no cover - defensive optional integration
                logger.warning("OpenAI trace flush failed: %s", exc.__class__.__name__)


@contextmanager
def _langfuse_chat_trace(settings: Settings, request_id: str, authenticated: bool):
    client = None
    try:
        Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            base_url=settings.langfuse_base_url,
            flush_at=1,
            flush_interval=1,
        )
        client = get_client()
        with client.start_as_current_observation(
            as_type="span",
            name="Meridian support chat",
            input={
                "request_id": request_id,
                "authenticated": authenticated,
                "sensitive_data_included": False,
            },
        ) as span:
            yield
            span.update(
                output={
                    "status": "completed",
                    "sensitive_data_included": False,
                }
            )
    except Exception as exc:  # pragma: no cover - defensive optional integration
        logger.warning("Langfuse tracing disabled after setup error: %s", exc.__class__.__name__)
        yield
    finally:
        if client is not None:
            try:
                client.flush()
            except Exception as exc:  # pragma: no cover - defensive optional integration
                logger.warning("Langfuse trace flush failed: %s", exc.__class__.__name__)


def tracing_status(settings: Settings) -> dict[str, bool | str]:
    return {
        "enabled": tracing_enabled(settings),
        "openai_enabled": openai_tracing_enabled(settings),
        "openai_requested": settings.openai_tracing_enabled,
        "openai_key_present": bool(settings.openai_api_key),
        "agents_sdk_available": trace is not None,
        "openai_flush_available": flush_traces is not None,
        "langfuse_enabled": langfuse_tracing_enabled(settings),
        "langfuse_requested": settings.langfuse_tracing_enabled,
        "langfuse_public_key_present": bool(settings.langfuse_public_key),
        "langfuse_secret_key_present": bool(settings.langfuse_secret_key),
        "langfuse_sdk_available": Langfuse is not None,
        "langfuse_base_url": settings.langfuse_base_url,
        "mode": "metadata_only",
    }


def safe_custom_span(name: str, data: dict[str, Any] | None = None):
    if custom_span is None:
        return nullcontext()
    return custom_span(name, data or {})


def safe_guardrail_span(name: str, triggered: bool):
    if guardrail_span is None:
        return nullcontext()
    return guardrail_span(name, triggered=triggered)
