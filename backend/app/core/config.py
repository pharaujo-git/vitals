from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://localhost:5432/vitals"

    @field_validator("database_url")
    @classmethod
    def _psycopg_scheme(cls, value: str) -> str:
        """Managed Postgres hands out postgres:// URLs; pin the psycopg driver."""
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix):]
        return value
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    refresh_token_days: int = 7
    # Set true behind HTTPS so the refresh cookie is Secure.
    cookie_secure: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
