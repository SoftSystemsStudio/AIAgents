from pydantic import BaseSettings, Field, SecretStr, AnyUrl
from typing import Optional

class Settings(BaseSettings):
    # Environment
    ENV: str = Field("development", env="ENV")

    # Infrastructure
    DATABASE_URL: Optional[AnyUrl] = Field(None, env="DATABASE_URL")
    REDIS_URL: Optional[str] = Field(None, env="REDIS_URL")

    # LLM / provider
    LLM_PROVIDER_API_KEY: Optional[SecretStr] = Field(None, env="LLM_PROVIDER_API_KEY")
    LLM_PROVIDER_URL: Optional[str] = Field(None, env="LLM_PROVIDER_URL")

    # App secrets
    SECRET_KEY: Optional[SecretStr] = Field(None, env="SECRET_KEY")

    # Observability
    SENTRY_DSN: Optional[str] = Field(None, env="SENTRY_DSN")

    class Config:
        env_file = ".env"
        case_sensitive = True

    def validate_required(self) -> None:
        """Explicit validation helper to be called by startup paths.

        Keeps import-time side-effects small so library imports do not
        raise during tests. Call this during application startup to
        enforce required settings.
        """
        missing = []
        if not self.DATABASE_URL:
            missing.append("DATABASE_URL")
        if not self.SECRET_KEY:
            missing.append("SECRET_KEY")
        if not self.LLM_PROVIDER_API_KEY and not self.LLM_PROVIDER_URL:
            # Accept either an API key or provider URL depending on deployment
            missing.append("LLM_PROVIDER_API_KEY or LLM_PROVIDER_URL")
        if missing:
            raise RuntimeError(f"Missing required config: {', '.join(missing)}")


# Export a single settings instance for convenience; callers may choose to
# construct their own in tests with different env_files.
settings = Settings()
