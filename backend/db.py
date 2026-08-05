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


async def init_db() -> None:
    """Jadvallarni yaratadi (MVP uchun migratsiya o'rniga).

    Keyinchalik PostgreSQL + Alembic ga o'tish uchun faqat shu joy o'zgaradi.
    """
    import models  # noqa: F401  (modellar Base.metadata ga ro'yxatdan o'tishi uchun)

    Path(settings.media_path).mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
