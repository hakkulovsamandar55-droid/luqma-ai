"""AI chaqiruvlari uchun kunlik chegaralar.

Nima uchun kerak: har rasm tahlili va har murabbiy javobi OpenAI hisobidan
pul yechadi. Chegarasiz bitta foydalanuvchi (yoki o'g'irlangan initData)
hisobni bo'shatib qo'yishi mumkin.
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import timeutil
from config import settings
from models import AiUsage, User

def chegara(tur: str, premium: bool) -> int:
    """Foydalanuvchi turiga qarab kunlik chegara."""
    if tur == "tahlil":
        return (
            settings.premium_tahlil_kunlik_limit
            if premium
            else settings.tahlil_kunlik_limit
        )
    return settings.premium_chat_kunlik_limit if premium else settings.chat_kunlik_limit

XABAR = {
    "tahlil": "Bugunga tahlil chegarasiga yetdingiz. Ertaga davom etamiz.",
    "chat": "Bugunga savollar chegarasiga yetdingiz. Ertaga davom etamiz.",
}


async def hisobla(session: AsyncSession, user_id: int, tur: str) -> int:
    """Bugungi ishlatilgan soni."""
    row = await session.scalar(
        select(AiUsage).where(
            AiUsage.user_id == user_id,
            AiUsage.sana == timeutil.bugun(),
            AiUsage.tur == tur,
        )
    )
    return row.soni if row else 0


async def umumiy_hisob(session: AsyncSession) -> int:
    """Bugun butun ilova bo'yicha nechta AI chaqiruvi bo'lgani."""
    return (
        await session.scalar(
            select(func.coalesce(func.sum(AiUsage.soni), 0)).where(
                AiUsage.sana == timeutil.bugun()
            )
        )
    ) or 0


async def premium_talab(session: AsyncSession, user: "User") -> None:
    """Rasm/matn tahlili premium talab qiladi.

    Faqat frontendda to'sish yetarli emas — API to'g'ridan-to'g'ri
    chaqirilishi mumkin. Shuning uchun asosiy to'siq shu yerda.

    `bepul_tahlil_soni` sozlamasi yangi foydalanuvchiga sotib olishdan
    oldin sinab ko'rish imkonini beradi. Default 0 — ya'ni tahlil
    butunlay premium uchun.
    """
    if user.premium_faolmi:
        return

    bepul = settings.bepul_tahlil_soni
    if bepul > 0:
        ishlatilgan = (
            await session.scalar(
                select(func.coalesce(func.sum(AiUsage.soni), 0)).where(
                    AiUsage.user_id == user.id, AiUsage.tur == "tahlil"
                )
            )
        ) or 0
        if ishlatilgan < bepul:
            return

    raise HTTPException(
        status.HTTP_402_PAYMENT_REQUIRED,
        detail="Ovqat tahlili premium obuna bilan ishlaydi.",
    )


async def tekshir_va_sana(session: AsyncSession, user: "User", tur: str) -> None:
    """Chegaradan oshmaganini tekshiradi va hisobni bittaga oshiradi.

    Chegaraga yetgan bo'lsa 429 qaytaradi. Hisob AI chaqirilishidan OLDIN
    oshiriladi — aks holda xato bo'lgan chaqiruvlar bepul bo'lib qolardi,
    holbuki ular ham pul turishi mumkin.
    """
    sana = timeutil.bugun()

    # Avval umumiy budjet: hisobni himoya qiladi.
    if settings.umumiy_kunlik_limit > 0:
        jami = await umumiy_hisob(session)
        if jami >= settings.umumiy_kunlik_limit:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Xizmat bugunga juda band. Ertaga urinib ko'ring.",
            )

    row = await session.scalar(
        select(AiUsage).where(
            AiUsage.user_id == user.id, AiUsage.sana == sana, AiUsage.tur == tur
        )
    )

    shaxsiy_chegara = chegara(tur, user.premium_faolmi)
    joriy = row.soni if row else 0
    if joriy >= shaxsiy_chegara:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail=XABAR.get(tur, "Kunlik chegaraga yetdingiz."),
        )

    if row:
        row.soni += 1
    else:
        session.add(AiUsage(user_id=user.id, sana=sana, tur=tur, soni=1))
    await session.commit()
