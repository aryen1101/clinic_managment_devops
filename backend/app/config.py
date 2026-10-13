"""Application settings, read from environment variables (or a local .env file).

Two ways to configure the database:
  1. DATABASE_URL  - one full connection string (used by docker-compose and tests)
  2. DB_HOST / DB_PORT / DB_NAME / DB_USER / DB_PASSWORD - separate parts
     (used by Kubernetes: non-secret parts come from a ConfigMap, the password from a Secret)
"""
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Clinic Management API"
    app_version: str = "1.0.0"
    app_env: str = "dev"
    log_level: str = "INFO"
    cors_origins: str = "*"

    database_url: str | None = None
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "clinic"
    db_user: str = "clinic"
    db_password: str = "clinic"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg://{quote_plus(self.db_user)}:{quote_plus(self.db_password)}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
