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
