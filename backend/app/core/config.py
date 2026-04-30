from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mcp_server_url: str = Field(
        default="https://order-mcp-74afyau24q-uc.a.run.app/mcp",
        alias="MCP_SERVER_URL",
    )
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="gpt-4o-mini", alias="OPENROUTER_MODEL")
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="OPENROUTER_BASE_URL",
    )
    guardrails_enabled: bool = Field(default=True, alias="GUARDRAILS_ENABLED")
    safety_guardrail_enforce: bool = Field(
        default=False,
        alias="SAFETY_GUARDRAIL_ENFORCE",
    )
    openrouter_guardrail_model: str = Field(
        default="meta-llama/llama-guard-3-8b",
        alias="OPENROUTER_GUARDRAIL_MODEL",
    )
    openrouter_evaluator_model: str = Field(
        default="openai/gpt-4o-mini",
        alias="OPENROUTER_EVALUATOR_MODEL",
    )
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_tracing_enabled: bool = Field(default=False, alias="OPENAI_TRACING_ENABLED")
    langfuse_tracing_enabled: bool = Field(default=False, alias="LANGFUSE_TRACING_ENABLED")
    langfuse_public_key: str = Field(default="", alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field(default="", alias="LANGFUSE_SECRET_KEY")
    langfuse_base_url: str = Field(
        default="https://cloud.langfuse.com",
        alias="LANGFUSE_BASE_URL",
    )
    app_env: str = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    frontend_origin: str = Field(
        default="http://localhost:3000",
        alias="FRONTEND_ORIGIN",
    )

    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
