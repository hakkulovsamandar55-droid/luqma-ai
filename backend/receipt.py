"""Chek (to'lov kvitansiyasi) tekshiruvi.

Ikki bosqich:
1. AI rasmdagi BARCHA matnni o'qiydi va tuzilgan ma'lumotga ajratadi.
2. O'qilgan ma'lumot kutilgan qiymatlar bilan solishtiriladi.

MUHIM: bu haqiqiy to'lov tasdig'i EMAS. Chekni tahrirlash, boshqa odamning
chekini yuborish yoki umuman soxta rasm yasash mumkin. Avtomatik tekshiruv
faqat arizani tez qabul qilish uchun — oxirgi qaror adminda.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import date, timedelta

from openai import APIError

from config import settings
from vision import VisionError, get_client

log = logging.getLogger(__name__)

# Summani solishtirishda ruxsat etilgan farq (komissiya yoki yaxlitlash uchun).
SUMMA_TOLERANS = 1000

CHEK_SCHEMA = {
    "type": "object",
    "properties": {
        "barcha_matn": {
            "type": "string",
            "description": "Rasmdagi butun matn, qatorma-qator, o'zgartirmasdan",
        },
        "karta_raqamlari": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Rasmda ko'ringan barcha karta raqamlari, shu jumladan "
            "yashirilganlari (masalan 8600 **** **** 1234)",
        },
        "summalar": {
            "type": "array",
            "items": {"type": "number"},
            "description": "Rasmdagi barcha pul summalari (faqat raqam)",
        },
        "asosiy_summa": {
            "type": ["number", "null"],
            "description": "O'tkazma summasi — eng katta yoki 'summa' deb "
            "belgilangan qiymat",
        },
        "sana": {
            "type": ["string", "null"],
            "description": "To'lov sanasi, YYYY-MM-DD formatida",
        },
        "vaqt": {"type": ["string", "null"], "description": "To'lov vaqti HH:MM"},
        "tranzaksiya_id": {
            "type": ["string", "null"],
            "description": "Chek/tranzaksiya raqami yoki ID",
        },
        "qabul_qiluvchi": {
            "type": ["string", "null"],
            "description": "Pul o'tkazilgan shaxs ismi",
        },
        "bank": {"type": ["string", "null"], "description": "Bank yoki ilova nomi"},
        "muvaffaqiyatli": {
            "type": "boolean",
            "description": "Chekda to'lov muvaffaqiyatli bajarilgani ko'rsatilganmi",
        },
        "chekka_oxshaydi": {
            "type": "boolean",
            "description": "Bu rasm haqiqatan to'lov cheki yoki skrinshotimi",
        },
    },
    "required": [
        "barcha_matn",
        "karta_raqamlari",
        "summalar",
        "asosiy_summa",
        "sana",
        "vaqt",
        "tranzaksiya_id",
        "qabul_qiluvchi",
        "bank",
        "muvaffaqiyatli",
        "chekka_oxshaydi",
    ],
    "additionalProperties": False,
}

PROMPT = """Sen to'lov cheklarini o'qiysan. Rasmda O'zbekiston banklarining
(Click, Payme, Uzum, Humo, Uzcard, Kapital, Ipoteka va h.k.) chek yoki
skrinshoti bo'lishi mumkin.

Vazifang: rasmdagi BARCHA matnni o'qib, so'ralgan maydonlarga ajratish.

Qoidalar:
- "barcha_matn" ga rasmdagi hamma yozuvni qatorma-qator ko'chir. Hech narsani
  tashlab ketma va o'zingdan qo'shma.
- Karta raqamlarini ko'rinishicha yoz, yulduzchalari bilan birga.
- Summalarni faqat raqam qilib yoz (bo'sh joy va "so'm" so'zisiz).
- Sanani YYYY-MM-DD ga o'gir. Yilsiz yozilgan bo'lsa joriy yilni qo'y.
- Agar rasm chekka o'xshamasa (masalan oddiy suratl yoki boshqa narsa),
  "chekka_oxshaydi" ni false qil.
- Hech narsani taxmin qilma. Ko'rinmasa null qo'y."""


@dataclass
class ChekNatija:
    """AI o'qigan ma'lumot va solishtiruv natijasi."""

    xom: dict
    otdi: bool = False
    sabablar: list[str] = field(default_factory=list)

    @property
    def izoh(self) -> str:
        return "; ".join(self.sabablar) if self.sabablar else "Hammasi mos keldi"


def rasm_hash(data: bytes) -> str:
    """Bir xil rasmni qayta yuborishni aniqlash uchun."""
    return hashlib.sha256(data).hexdigest()


def _raqamlar(matn: str) -> str:
    return re.sub(r"\D", "", matn or "")


def oxirgi_tort(karta: str) -> str:
    raqam = _raqamlar(karta)
    return raqam[-4:] if len(raqam) >= 4 else ""


def _ism_normalize(ism: str) -> set[str]:
    """Ismni solishtirishga tayyorlaydi: kichik harf, faqat harflar, so'zlarga bo'linadi."""
    tozalangan = re.sub(r"[^\w\s]", " ", (ism or "").lower())
    # Lotin/kirill farqiga tegmaymiz — bank cheklarida odatda lotin.
    return {so for so in tozalangan.split() if len(so) > 2}


def ismlar_mos(kutilgan: str, topilgan: str) -> bool:
    """Ism qismi mos kelsa yetarli.

    Cheklarda ism turlicha yoziladi: "ALIYEV A.", "Aliyev Alisher",
    "A. ALIYEV". To'liq tenglikni talab qilsak, haqiqiy to'lovlar rad
    etilaveradi — shuning uchun bitta so'z mos kelishi kifoya.
    """
    a = _ism_normalize(kutilgan)
    b = _ism_normalize(topilgan)
    if not a or not b:
        return False
    return bool(a & b)


async def chekni_oqi(rasm_bytes: bytes, media_type: str = "image/jpeg") -> dict:
    """Rasmdagi matnni AI orqali o'qiydi."""
    b64 = base64.b64encode(rasm_bytes).decode()

    try:
        response = await get_client().chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{media_type};base64,{b64}"},
                        },
                        {"type": "text", "text": "Shu chekni o'qib ber."},
                    ],
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "chek",
                    "schema": CHEK_SCHEMA,
                    "strict": True,
                },
            },
            max_tokens=1500,
            temperature=0,
        )
        return json.loads(response.choices[0].message.content)
    except (APIError, json.JSONDecodeError, IndexError, KeyError) as exc:
        log.exception("Chekni o'qib bo'lmadi")
        raise VisionError("Chekni o'qib bo'lmadi") from exc


def tekshir(
    xom: dict,
    *,
    kutilgan_karta: str,
    kutilgan_ism: str,
    kutilgan_summa: int,
    amal_kuni: int,
    bugun: date,
) -> ChekNatija:
    """O'qilgan ma'lumotni kutilgan qiymatlar bilan solishtiradi.

    Hamma shart bajarilsagina otdi=True bo'ladi. Har bir muvaffaqiyatsiz
    shart sabablar ro'yxatiga yoziladi — admin nima bo'lganini ko'radi.
    """
    natija = ChekNatija(xom=xom)

    if not xom.get("chekka_oxshaydi"):
        natija.sabablar.append("Rasm to'lov chekiga o'xshamaydi")
        return natija

    if xom.get("muvaffaqiyatli") is False:
        natija.sabablar.append("Chekda to'lov bajarilmagani ko'rsatilgan")
        return natija

    # --- Karta ---
    kutilgan_4 = oxirgi_tort(kutilgan_karta)
    topilgan_kartalar = xom.get("karta_raqamlari") or []
    mos_karta = None

    for k in topilgan_kartalar:
        if kutilgan_4 and oxirgi_tort(k) == kutilgan_4:
            mos_karta = k
            break

    # Chekda karta ko'rinmasa, ism bo'yicha tekshiramiz — ba'zi ilovalar
    # (masalan Payme) qabul qiluvchi kartasini yashiradi.
    ism_mos = ismlar_mos(kutilgan_ism, xom.get("qabul_qiluvchi") or "")

    if mos_karta:
        natija.xom["_mos_karta"] = mos_karta
    elif ism_mos:
        natija.sabablar.append("Karta raqami ko'rinmadi, ism bo'yicha topildi")
    else:
        natija.sabablar.append(
            f"Karta mos kelmadi (kutilgan ...{kutilgan_4}, "
            f"topilgan: {', '.join(topilgan_kartalar) or 'yo‘q'})"
        )
        return natija

    # --- Summa ---
    summa = xom.get("asosiy_summa")
    summalar = [int(s) for s in (xom.get("summalar") or []) if isinstance(s, (int, float))]

    mos_summa = None
    if summa is not None and abs(int(summa) - kutilgan_summa) <= SUMMA_TOLERANS:
        mos_summa = int(summa)
    else:
        # Asosiy summa noto'g'ri aniqlangan bo'lishi mumkin — boshqalarini ham ko'ramiz.
        for s in summalar:
            if abs(s - kutilgan_summa) <= SUMMA_TOLERANS:
                mos_summa = s
                break

    if mos_summa is None:
        natija.sabablar.append(
            f"Summa mos kelmadi (kutilgan {kutilgan_summa:,}, "
            f"topilgan: {summa or 'yo‘q'})".replace(",", " ")
        )
        return natija

    # --- Sana ---
    sana_matn = xom.get("sana")
    if not sana_matn:
        natija.sabablar.append("Chekda sana topilmadi")
        return natija

    try:
        chek_sana = date.fromisoformat(str(sana_matn)[:10])
    except ValueError:
        natija.sabablar.append(f"Sana o'qilmadi: {sana_matn}")
        return natija

    if chek_sana > bugun + timedelta(days=1):
        natija.sabablar.append(f"Chek sanasi kelajakda: {chek_sana}")
        return natija

    if (bugun - chek_sana).days > amal_kuni:
        natija.sabablar.append(
            f"Chek eskirgan ({chek_sana}, {amal_kuni} kundan oshgan)"
        )
        return natija

    natija.otdi = True
    return natija
