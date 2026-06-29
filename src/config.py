from functools import lru_cache
import logging

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    SERVICE_NAME: str = "nexus-memory-mcp"
    SERVICE_PORT: int = 8002
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = "postgresql://nexus_user:nexus_password@localhost:5432/nexus"
    REDIS_URL: str = "redis://localhost:6379/0"
    MCP_VERSION: str = "1.0"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def setup_logging() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
