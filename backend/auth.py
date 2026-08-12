"""Telegram Mini App `initData` HMAC-SHA256 validatsiyasi.

Telegram algoritmi:
  secret_key = HMAC_SHA256(key="WebAppData", data=bot_token)
  hash       = HMAC_SHA256(key=secret_key, data=data_check_string)
`data_check_string` — `hash` dan tashqari barcha maydonlar `key=value` ko'rinishida,
alifbo tartibida, `\n` bilan birlashtirilgan.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db import get_session
from models import User


class InitDataError(ValueError):
    """initData yaroqsiz."""


@dataclass(slots=True)
class TelegramUser:
    id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None

    @property
    def toliq_ism(self) -> str | None:
        parts = [p for p in (self.first_name, self.last_name) if p]
        return " ".join(parts) if parts else None


def _secret_key(bot_token: str) -> bytes:
    return hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()


def parse_init_data(init_data: str, bot_token: str, max_age: int = 0) -> TelegramUser:
    """initData ni tekshiradi va foydalanuvchi ma'lumotlarini qaytaradi."""
    if not init_data:
        raise InitDataError("initData bo'sh")
    if not bot_token:
        raise InitDataError("BOT_TOKEN sozlanmagan")

    try:
        pairs = dict(parse_qsl(init_data, strict_parsing=True, keep_blank_values=True))
    except ValueError as exc:  # noqa: PERF203
        raise InitDataError("initData formati noto'g'ri") from exc

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise InitDataError("hash topilmadi")

    data_check_string = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
    calculated = hmac.new(
        _secret_key(bot_token), data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated, received_hash):
        raise InitDataError("hash mos kelmadi")

    if max_age > 0:
        try:
            auth_date = int(pairs.get("auth_date", "0"))
        except ValueError as exc:
            raise InitDataError("auth_date noto'g'ri") from exc
        if auth_date <= 0 or time.time() - auth_date > max_age:
            raise InitDataError("initData muddati o'tgan")

    raw_user = pairs.get("user")
    if not raw_user:
        raise InitDataError("user maydoni yo'q")
    try:
        data = json.loads(raw_user)
        return TelegramUser(
            id=int(data["id"]),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            username=data.get("username"),
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise InitDataError("user ma'lumoti buzilgan") from exc


def _extract_init_data(authorization: str | None, x_init_data: str | None) -> str:
    if x_init_data:
        return x_init_data
    if authorization:
        scheme, _, value = authorization.partition(" ")
        if scheme.lower() == "tma" and value:
            return value
    return ""


async def get_or_create_user(session: AsyncSession, tg: TelegramUser) -> tuple[User, bool]:
    result = await session.execute(select(User).where(User.telegram_id == tg.id))
    user = result.scalar_one_or_none()
    if user:
        # Telegram profilidagi o'zgarishlarni sinxronlab qo'yamiz.
        changed = False
        if tg.toliq_ism and user.ism != tg.toliq_ism:
            user.ism, changed = tg.toliq_ism, True
        if tg.username and user.username != tg.username:
            user.username, changed = tg.username, True
        if changed:
            await session.commit()
        return user, False

    user = User(telegram_id=tg.id, ism=tg.toliq_ism, username=tg.username)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user, True


async def current_user(
    authorization: str | None = Header(default=None),
    x_init_data: str | None = Header(default=None, alias="X-Init-Data"),
    session: AsyncSession = Depends(get_session),
) -> User:
    """FastAPI dependency: har bir so'rovda initData tekshiriladi."""
    init_data = _extract_init_data(authorization, x_init_data)

    if settings.dev_mode and not init_data:
        tg = TelegramUser(id=settings.dev_telegram_id, first_name="Dev")
    else:
        try:
            tg = parse_init_data(init_data, settings.bot_token, settings.initdata_max_age)
        except InitDataError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
            ) from exc

    user, _ = await get_or_create_user(session, tg)

    # Bloklangan foydalanuvchi hech qaysi endpointdan foydalana olmaydi.
    # Tekshiruv shu yerda — shunda yangi endpoint qo'shilganda ham unutilmaydi.
    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=user.block_sabab or "Hisobingiz bloklangan. Yordam xizmatiga yozing.",
        )

    # Oxirgi faollik — admin panelidagi "faol foydalanuvchilar" uchun.
    # Har so'rovda emas, kuniga bir marta yoziladi (ortiqcha yozuvni oldini olish).
    import timeutil

    hozir = timeutil.hozir()
    if user.oxirgi_faollik is None or user.oxirgi_faollik.date() != hozir.date():
        user.oxirgi_faollik = hozir
        await session.commit()

    return user
