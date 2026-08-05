"""Muhit sozlamalari (.env dan o'qiladi)."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Telegram ---
    bot_token: str = ""
    webapp_url: str = "http://localhost:5173"

    # --- OpenAI ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # --- DB ---
    database_url: str = "sqlite+aiosqlite:///./data/luqma.db"

    # --- API ---
    cors_origins: str = "*"
    media_dir: str = "./data/media"
    media_url_prefix: str = "/media"

    # initData ning maksimal "yoshi" (sekund). 0 = tekshirilmaydi.
    initdata_max_age: int = 24 * 60 * 60

    # DEV rejimi: initData tekshiruvisiz test qilish uchun (productionda FALSE!)
    dev_mode: bool = False
    dev_telegram_id: int = 111111111

    @property
    def cors_origin_list(self) -> list[str]:
        raw = (self.cors_origins or "").strip()
        if not raw or raw == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]

    @property
    def media_path(self) -> Path:
        p = Path(self.media_dir)
        if not p.is_absolute():
            p = BASE_DIR / p
        return p


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
