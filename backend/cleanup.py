"""Eski rasmlarni diskdan tozalash.

Har ovqat rasmi serverda saqlanadi. Tozalanmasa media papkasi cheksiz
o'sadi va bir necha oyda diskni to'ldiradi. Bu yerda ikki ish qilinadi:

1. Belgilangan muddatdan eski rasmlar o'chiriladi va DB dagi havola
   bo'shatiladi (ovqat yozuvi qoladi — faqat rasmi yo'qoladi).
2. DB da eslatilmagan "yetim" fayllar ham o'chiriladi — masalan tahlil
   qilingan, lekin foydalanuvchi saqlamagan rasmlar.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from pathlib import Path

from sqlalchemy import select, update

import timeutil
from config import settings
from db import SessionLocal as async_session
from models import Meal, Payment

log = logging.getLogger(__name__)

# Sikl kuniga bir marta ishlasa yetarli.
INTERVAL_SEKUND = 24 * 60 * 60

# Yetim fayl shuncha soatdan keyin o'chiriladi. Darhol emas, chunki
# foydalanuvchi tahlil natijasini ko'rib turgan bo'lishi mumkin.
YETIM_SOAT = 6


def _nomlar(yollar) -> set[str]:
    return {Path(y).name for y in yollar if y}


def _media_dir() -> Path:
    # `settings.media_path` — API rasmlarni AYNAN shu yerga yozadi (nisbiy yo'l
    # loyiha ildiziga nisbatan hisoblanadi). Bu yerda `Path(settings.media_dir)`
    # ishlatilsa, process boshqa katalogdan ishga tushirilganda tozalash butunlay
    # boshqa papkaga qarab qolardi.
    return settings.media_path


async def eski_rasmlarni_ochir() -> int:
    """Muddati o'tgan rasmlarni o'chiradi. O'chirilgan fayllar sonini qaytaradi."""
    kun = settings.rasm_saqlash_kuni
    if kun <= 0:
        return 0

    chegara = timeutil.bugun() - timedelta(days=kun)
    ochirildi = 0

    async with async_session() as session:
        rows = (
            await session.execute(
                select(Meal.id, Meal.rasm_yoli).where(
                    Meal.sana < chegara, Meal.rasm_yoli.is_not(None)
                )
            )
        ).all()

        for meal_id, yol in rows:
            fayl = _media_dir() / Path(yol).name
            try:
                fayl.unlink(missing_ok=True)
                ochirildi += 1
            except OSError:
                log.warning("Rasmni o'chirib bo'lmadi: %s", fayl)
                continue
            await session.execute(
                update(Meal).where(Meal.id == meal_id).values(rasm_yoli=None)
            )

        await session.commit()

    return ochirildi


async def yetim_fayllarni_ochir() -> int:
    """DB da eslatilmagan fayllarni o'chiradi (saqlanmagan tahlillar)."""
    media = _media_dir()
    if not media.exists():
        return 0

    async with async_session() as session:
        # DIQQAT: to'lov cheklari ham SHU papkaga tushadi. Ular ro'yxatga
        # qo'shilmasa, chek yuborilgandan 6 soat keyin o'chib ketadi va admin
        # arizani ko'rganda rasm topilmaydi.
        band = _nomlar(
            (
                await session.execute(
                    select(Meal.rasm_yoli).where(Meal.rasm_yoli.is_not(None))
                )
            ).scalars()
        ) | _nomlar(
            (
                await session.execute(
                    select(Payment.chek_yoli).where(Payment.chek_yoli.is_not(None))
                )
            ).scalars()
        )

    chegara = timeutil.hozir() - timedelta(hours=YETIM_SOAT)
    chegara_ts = chegara.timestamp()
    ochirildi = 0

    for fayl in media.iterdir():
        if not fayl.is_file() or fayl.name in band:
            continue
        try:
            if fayl.stat().st_mtime < chegara_ts:
                fayl.unlink()
                ochirildi += 1
        except OSError:
            log.warning("Yetim faylni o'chirib bo'lmadi: %s", fayl)

    return ochirildi


async def tozalash_sikli() -> None:
    """Fon vazifasi — kuniga bir marta tozalaydi. Xato bo'lsa ham to'xtamaydi."""
    while True:
        try:
            eski = await eski_rasmlarni_ochir()
            yetim = await yetim_fayllarni_ochir()
            if eski or yetim:
                log.info("Tozalandi: %s eski, %s yetim rasm", eski, yetim)
        except Exception:  # noqa: BLE001 — sikl to'xtamasligi kerak
            log.exception("Rasm tozalash siklida xato")

        await asyncio.sleep(INTERVAL_SEKUND)
