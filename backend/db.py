"""DB engine va session sozlamalari (async SQLAlchemy)."""

from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import BASE_DIR, settings


class Base(DeclarativeBase):
    pass


def _resolve_url(url: str) -> str:
    """SQLite uchun nisbiy yo'lni loyiha ildiziga nisbatan absolyut qiladi."""
    prefix = "sqlite+aiosqlite:///"
    if url.startswith(prefix):
        raw = url[len(prefix) :]
        if raw != ":memory:" and not raw.startswith("/"):
            path = (BASE_DIR / raw).resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            return f"{prefix}{path}"
    return url


engine = create_async_engine(_resolve_url(settings.database_url), echo=False, future=True)

SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _yetishmagan_ustunlarni_qosh(conn) -> None:
    """Mavjud jadvallarga yangi ustunlarni qo'shadi.

    create_all faqat YO'Q jadvalni yaratadi — mavjud jadvalga ustun qo'shmaydi.
    Ishlab turgan bazada yangi maydon paydo bo'lsa, ilova "no such column"
    bilan yiqiladi. Alembic o'rnatilgunga qadar shu yengil yechim ishlatiladi:
    har ustun uchun bor-yo'qligini tekshirib, kerak bo'lsa ALTER qilamiz.
    """
    from sqlalchemy import text

    # jadval -> {ustun nomi: SQL turi (DEFAULT bilan)}
    KUTILGAN = {
        "users": {
            "is_admin": "BOOLEAN DEFAULT 0",
            "is_premium": "BOOLEAN DEFAULT 0",
            "premium_tugash": "DATETIME",
            "is_blocked": "BOOLEAN DEFAULT 0",
            "block_sabab": "VARCHAR(256)",
            "oxirgi_faollik": "DATETIME",
            "premium_tasdiq_kutilmoqda": "BOOLEAN DEFAULT 0",
        },
        "tolov_sozlama": {
            "yordam_username": "VARCHAR(64) DEFAULT ''",
            "premium_sarlavha": "VARCHAR(120) DEFAULT ''",
            "premium_afzalliklar": "TEXT DEFAULT ''",
        },
    }

    for jadval, ustunlar in KUTILGAN.items():
        mavjud_jadval = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"),
            {"n": jadval},
        )
        if not mavjud_jadval.first():
            continue  # create_all yangi yaratadi, ALTER kerak emas

        natija = await conn.execute(text(f"PRAGMA table_info({jadval})"))
        bor = {qator[1] for qator in natija.fetchall()}

        for ustun, tur in ustunlar.items():
            if ustun not in bor:
                await conn.execute(
                    text(f"ALTER TABLE {jadval} ADD COLUMN {ustun} {tur}")
                )


async def init_db() -> None:
    """Jadvallarni yaratadi va yetishmagan ustunlarni qo'shadi.

    Keyinchalik PostgreSQL + Alembic ga o'tish uchun faqat shu joy o'zgaradi.
    """
    import models  # noqa: F401  (modellar Base.metadata ga ro'yxatdan o'tishi uchun)

    Path(settings.media_path).mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        # Tartib muhim: avval eski jadvalga ustun qo'shamiz, keyin yangi
        # jadvallarni yaratamiz.
        await _yetishmagan_ustunlarni_qosh(conn)
        await conn.run_sync(Base.metadata.create_all)

    # Ovqat bazasi bo'sh bo'lsa boshlang'ich taomlarni qo'shamiz.
    # Admin o'zgartirganlari ustidan yozilmaydi — faqat bo'sh bazaga.
    import food_seed

    async with SessionLocal() as session:
        qoshildi = await food_seed.bazani_toldir(session)
        if qoshildi:
            import logging

            logging.getLogger(__name__).info(
                "Ovqat bazasiga %s ta taom qo'shildi", qoshildi
            )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
