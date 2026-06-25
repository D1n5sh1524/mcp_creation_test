from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://ielts:ielts123@localhost:5432/ielts_booking"
    local_ai_base_url: str = "http://localhost:11434"
    local_ai_model: str = "qwen3.5:9b"
    local_ai_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
