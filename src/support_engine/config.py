from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://support:support_dev@postgres:5432/support"
    redis_url: str = "redis://redis:6379/0"
    environment: str = Field(default="development", pattern=r"^[a-zA-Z0-9_-]+$")
    tenant_id: str = Field(default="demo-tenant", pattern=r"^[a-zA-Z0-9_-]+$")
    webhook_key_id: str = "demo"
    webhook_secret: str = Field(default="local-webhook-secret-change-me", min_length=16)
    operator_token: str = Field(default="local-operator-token-change-me", min_length=16)
    mock_service_token: str = Field(default="local-mock-token-change-me", min_length=16)
    mock_api_url: str = "http://mock-api:8000"
    queue_name: str = "support"
    webhook_window_seconds: int = 300
    demo_step_delay_seconds: float = Field(default=0.0, ge=0, le=2)

    def channel(self, tenant_id: str | None = None) -> str:
        return f"support:{self.environment}:tenant:{tenant_id or self.tenant_id}:run-events"


@lru_cache
def get_settings() -> Settings:
    return Settings()
