"""Admin huquqlari va foydalanuvchi holati tekshiruvi.

Ikki xil admin bor:
- `.env` dagi ADMIN_IDS — "asosiy" adminlar. Ular bazadan o'chirilmaydi va
  huquqini boshqa admin olib qo'ya olmaydi. Birinchi admin shu yerdan keladi,
  aks holda hech kim panelga kira olmasdi.
- Bazadagi `is_admin` — panel orqali tayinlanganlar.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status

from auth import current_user
from config import settings
from models import User


def asosiy_adminmi(user: User) -> bool:
    """.env dagi ro'yxatdan — bazadan o'zgartirib bo'lmaydi."""
    return user.telegram_id in settings.admin_id_list


def adminmi(user: User) -> bool:
    return bool(user.is_admin) or asosiy_adminmi(user)


async def current_admin(user: User = Depends(current_user)) -> User:
    """Faqat adminlarga ruxsat beruvchi dependency."""
    if not adminmi(user):
        # 403 emas, 404 — panel mavjudligini ham bildirmaymiz.
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Topilmadi")
    return user

