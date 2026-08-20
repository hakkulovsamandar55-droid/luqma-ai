"""Log sozlamalari.

Nima uchun kerak: default holatda loglar faqat stdout ga chiqadi va Docker
konteyneri qayta ishga tushsa yo'qoladi. Xato bo'lganda nima bo'lganini
bilish uchun ular diskda qolishi kerak.

Fayl aylanma (rotating): bitta fayl 5 MB ga yetganda yangisiga o'tiladi,
5 tagacha eski nusxa saqlanadi. Ya'ni loglar diskni to'ldirmaydi.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import settings

FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"

# Bu kutubxonalar juda ko'p gapiradi — faqat ogohlantirishlarini olamiz.
SHOVQINLI = ("httpx", "httpcore", "openai", "aiogram.event", "sqlalchemy.engine")


def sozla() -> None:
    """Loglarni stdout ga va (sozlangan bo'lsa) faylga yo'naltiradi."""
    daraja = getattr(logging, settings.log_level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(daraja)

    # Qayta chaqirilsa handler ikkilanmasin.
    for h in list(root.handlers):
        root.removeHandler(h)

    formatter = logging.Formatter(FORMAT)

    konsol = logging.StreamHandler(sys.stdout)
    konsol.setFormatter(formatter)
    root.addHandler(konsol)

    if settings.log_file:
        yol = Path(settings.log_file)
        try:
            yol.parent.mkdir(parents=True, exist_ok=True)
            fayl = RotatingFileHandler(
                yol,
                maxBytes=5 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
            fayl.setFormatter(formatter)
            root.addHandler(fayl)
        except OSError as exc:
            # Faylga yozib bo'lmasa ilova to'xtamasin — konsol baribir ishlaydi.
            root.warning("Log faylini ochib bo'lmadi (%s): %s", yol, exc)

    for nom in SHOVQINLI:
        logging.getLogger(nom).setLevel(max(daraja, logging.WARNING))
