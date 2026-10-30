"""Application settings, read from environment variables (or a .env file).

Nothing secret is hard-coded: JWT_SECRET and MONGODB_URI must come from the environment.
"""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Database ---
    mongodb_uri: str
    mongodb_db: str = "apiwatch"

    # --- Auth ---
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # --- API server ---
    cors_origins: str = "http://localhost:5173"  # comma-separated
    rate_limit_enabled: bool = True

    # --- Business limits ---
    max_monitors_per_user: int = 20
    min_interval_seconds: int = 30
    results_retention_days: int = 30

    # --- Worker ---
    worker_tick_seconds: int = 10
    worker_concurrency: int = 20
    worker_batch_size: int = 100

    # --- SSRF protection ---
    allowed_ports: str = "80,443,8080,8443"
    max_redirects: int = 5

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def allowed_port_set(self) -> set[int]:
        return {int(p) for p in self.allowed_ports.split(",") if p.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
