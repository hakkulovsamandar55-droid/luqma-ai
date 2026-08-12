"""Vaqt yordamchilari.

Butun loyihada "hozir" va "bugun" shu yerdan olinadi. Sabab: server UTC da
ishlaydi, foydalanuvchi esa boshqa zonada. To'g'ridan-to'g'ri datetime.now()
ishlatilsa, kun noto'g'ri vaqtda yangilanadi — O'zbekistonda ertalab soat
5 da, ya'ni yarim tundan keyin yegan ovqat kechagi kunga yoziladi.
"""

from __future__ import annotations

from datetime import date as date_type
from datetime import datetime
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
    """Bugungi kunning boshlanishi (00:00) — kunlik chegaralarni sanash uchun."""
    return hozir().replace(hour=0, minute=0, second=0, microsecond=0)
