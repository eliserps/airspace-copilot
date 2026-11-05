from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]

Language = Literal["en", "pt"]
LANGUAGE_NAMES: dict[Language, str] = {"en": "English", "pt": "Brazilian Portuguese"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    groq_api_key: str | None = None
    llm_model: str = "openai/gpt-oss-120b"
    llm_timeout_seconds: float = 30

    opensky_client_id: str | None = None
    opensky_client_secret: str | None = None

    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]
    ask_rate_limit_per_minute: int = 10
    weather_rate_limit_per_minute: int = 20

    use_system_truststore: bool = False
    log_level: str = "INFO"
    log_format: Literal["text", "json"] = "text"

    knowledge_dir: Path = BACKEND_DIR / "knowledge"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [o.strip().rstrip("/") for o in value.split(",") if o.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


def configure_tls(settings: Settings) -> None:
    if settings.use_system_truststore:
        import truststore

        truststore.inject_into_ssl()
