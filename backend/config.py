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

    # Premiumsiz foydalanuvchiga beriladigan tahlil soni (umuman, kunlik
    # emas). 0 = rasm tahlili butunlay premium uchun. Bu qiymatni oshirsangiz
    # yangi foydalanuvchi sotib olishdan oldin sinab ko'ra oladi.
    bepul_tahlil_soni: int = 0

    # Kuniga nechta chek yuborish mumkin (spamdan himoya).
    chek_kunlik_limit: int = 5

    # --- Loglar ---
    log_level: str = "INFO"
    # Bo'sh bo'lsa faqat konsolga yoziladi. Docker da /data/logs/luqma.log
    # qilib qo'ysangiz, konteyner qayta ishga tushsa ham loglar qoladi.
    log_file: str = ""

    # --- Admin ---
    # Vergul bilan ajratilgan Telegram ID lar. Faqat shular /stat va /xabar
    # buyruqlarini ishlata oladi. Bo'sh bo'lsa admin buyruqlari o'chiq.
    admin_ids: str = ""

    # --- Vaqt zonasi ---
    # "Bugun" qachon boshlanishini shu belgilaydi. Server UTC da ishlagani
    # uchun buni sozlamasak, kun O'zbekistonda soat 05:00 da yangilanadi.
    timezone: str = "Asia/Tashkent"

    # --- Kunlik chegaralar (bitta foydalanuvchi uchun) ---
    # OpenAI har chaqiruv uchun pul turadi, shuning uchun chegara shart.
    chat_kunlik_limit: int = 30
    tahlil_kunlik_limit: int = 30

    # Premium foydalanuvchilar uchun kengaytirilgan chegaralar.
    premium_chat_kunlik_limit: int = 200
    premium_tahlil_kunlik_limit: int = 200

    # Butun ilova bo'yicha kunlik AI chaqiruvlari chegarasi. Bitta
    # foydalanuvchi chegarasi hisobni himoya qilmaydi: 1000 odam x 30 = katta
    # summa. 0 = cheklanmagan.
    umumiy_kunlik_limit: int = 5000

    # Rasmlar shuncha kundan keyin diskdan o'chiriladi (0 = o'chirilmaydi).
    rasm_saqlash_kuni: int = 60

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


    @property
    def admin_id_list(self) -> list[int]:
        """admin_ids satrini raqamlar ro'yxatiga o'giradi."""
        natija = []
        for bolak in self.admin_ids.split(","):
            bolak = bolak.strip()
            if bolak.isdigit():
                natija.append(int(bolak))
        return natija


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
