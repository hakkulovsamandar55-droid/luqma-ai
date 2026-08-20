"""Vaqt yordamchilari.

Butun loyihada "hozir" va "bugun" shu yerdan olinadi. Sabab: server UTC da
ishlaydi, foydalanuvchi esa boshqa zonada. To'g'ridan-to'g'ri datetime.now()
ishlatilsa, kun noto'g'ri vaqtda yangilanadi — O'zbekistonda ertalab soat
5 da, ya'ni yarim tundan keyin yegan ovqat kechagi kunga yoziladi.
"""

from __future__ import annotations

from datetime import date as date_type
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from config import settings

try:
    TZ = ZoneInfo(settings.timezone)
except ZoneInfoNotFoundError:  # noto'g'ri nom yozilgan bo'lsa ilova o'lmasin
    TZ = ZoneInfo("UTC")


def hozir() -> datetime:
    """Foydalanuvchi zonasidagi joriy vaqt (naive — DB shu ko'rinishda saqlaydi)."""
    return datetime.now(TZ).replace(tzinfo=None)


def bugun() -> date_type:
    """Foydalanuvchi zonasidagi bugungi sana."""
    return datetime.now(TZ).date()


def kun_boshi() -> datetime:
    """Mahalliy yarim tun, mahalliy zonada (naive).

    Faqat `hozir()` bilan yozilgan ustunlar bilan solishtiriladi
    (masalan `User.oxirgi_faollik`).
    """
    return hozir().replace(hour=0, minute=0, second=0, microsecond=0)


def kun_boshi_utc() -> datetime:
    """Mahalliy yarim tun, LEKIN UTC da ifodalangan (naive).

    Nega kerak: `created_at` ustunlari `models.utcnow()` bilan, ya'ni UTC da
    yoziladi. Ularni mahalliy yarim tun bilan solishtirsak, zona farqi
    (Toshkent uchun +5 soat) qadar oyna hosil bo'ladi va o'sha vaqtda
    hisob NOL chiqadi — ya'ni kunlik chegara har kecha 00:00 dan 05:00
    gacha umuman ishlamay qoladi.
    """
    mahalliy = datetime.now(TZ).replace(hour=0, minute=0, second=0, microsecond=0)
    return mahalliy.astimezone(timezone.utc).replace(tzinfo=None)
