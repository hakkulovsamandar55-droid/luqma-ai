"""OpenAI GPT-4o-mini orqali ovqat rasmini / matnini tahlil qilish."""

from __future__ import annotations

import base64
import json
import logging
from typing import Any

from openai import APIError, AsyncOpenAI

from config import settings
from schemas import MealAnalysis

log = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Sen ovqatlanish bo'yicha mutaxassis nutritsiologsan. Senga taom rasmi yoki "
    "matnli tavsifi beriladi. Vazifang — taomni aniqlash va uning ozuqaviy "
    "qiymatini baholash.\n"
    "Qoidalar:\n"
    "1. Taom nomini O'ZBEK tilida yoz (masalan: 'Osh', 'Somsa', 'Tovuqli salat').\n"
    "2. Rasmda ko'ringan ULUSHNI baholab, shu ulush uchun qiymat ber "
    "(butun tovoq uchun, 100g uchun emas).\n"
    "3. O'zbek milliy taomlarini yaxshi bil: osh, manti, somsa, lag'mon, shashlik, "
    "chuchvara, norin, dimlama, shorva, non, sumalak.\n"
    "4. Agar rasmda bir nechta taom bo'lsa — barchasini bitta nom ostida jamla "
    "(masalan 'Osh va achichuk salat') va yig'indi qiymatni ber.\n"
    "5. Agar rasmda ovqat umuman bo'lmasa: taom_nomi='Aniqlanmadi', barcha "
    "raqamlar 0, ishonch=0.\n"
    "6. ishonch — 0 dan 1 gacha, baholashingga qanchalik ishonchli ekanliging.\n"
    "7. izoh — bitta qisqa jumla, o'zbek tilida (masalan 'Oqsilga boy, "
    "kechki ovqat uchun mos')."
)

RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": {
        "name": "taom_tahlili",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "taom_nomi": {"type": "string", "description": "Taom nomi o'zbek tilida"},
                "ulush": {"type": "string", "description": "Masalan '1 tovoq (~350g)'"},
                "kaloriya": {"type": "integer", "description": "Jami kcal"},
                "protein_g": {"type": "number"},
                "yog_g": {"type": "number"},
                "uglevod_g": {"type": "number"},
                "ishonch": {"type": "number"},
                "izoh": {"type": "string"},
            },
            "required": [
                "taom_nomi",
                "ulush",
                "kaloriya",
                "protein_g",
                "yog_g",
                "uglevod_g",
                "ishonch",
                "izoh",
            ],
        },
    },
}

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not settings.openai_api_key:
            raise VisionError("OPENAI_API_KEY sozlanmagan")
        _client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=60.0)
    return _client


class VisionError(RuntimeError):
    """AI tahlili bajarilmadi."""


def _clamp(analysis: dict[str, Any]) -> MealAnalysis:
    """AI javobini xavfsiz chegaralarga soladi."""

    def num(key: str, limit: float) -> float:
        try:
            return max(0.0, min(float(analysis.get(key) or 0), limit))
        except (TypeError, ValueError):
            return 0.0

    nomi = (analysis.get("taom_nomi") or "Aniqlanmadi").strip()[:160]
    return MealAnalysis(
        taom_nomi=nomi or "Aniqlanmadi",
        ulush=(analysis.get("ulush") or None),
        kaloriya=int(num("kaloriya", 20000)),
        protein_g=round(num("protein_g", 2000), 1),
        yog_g=round(num("yog_g", 2000), 1),
        uglevod_g=round(num("uglevod_g", 2000), 1),
        ishonch=round(max(0.0, min(num("ishonch", 1.0), 1.0)), 2),
        izoh=(analysis.get("izoh") or None),
    )


async def _so_rov(content: list[dict[str, Any]]) -> MealAnalysis:
    try:
        response = await get_client().chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
            response_format=RESPONSE_SCHEMA,
            max_tokens=500,
            temperature=0.2,
        )
        raw = response.choices[0].message.content or "{}"
        return _clamp(json.loads(raw))
    except (APIError, json.JSONDecodeError, IndexError, KeyError) as exc:
        log.exception("Vision tahlili bajarilmadi")
        raise VisionError(f"AI tahlili bajarilmadi: {exc}") from exc


async def rasmni_tahlil_qil(image_bytes: bytes, mime: str = "image/jpeg") -> MealAnalysis:
    """Rasmni base64 qilib vision so'rovga yuboradi."""
    b64 = base64.b64encode(image_bytes).decode()
    return await _so_rov(
        [
            {
                "type": "text",
                "text": "Ushbu rasmdagi taomni aniqla va ozuqaviy qiymatini hisobla.",
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64}", "detail": "low"},
            },
        ]
    )


async def matnni_tahlil_qil(matn: str) -> MealAnalysis:
    """Qo'lda kiritilgan tavsifni tahlil qiladi (masalan '150g osh')."""
    return await _so_rov(
        [
            {
                "type": "text",
                "text": (
                    "Quyidagi taom tavsifi bo'yicha ozuqaviy qiymatni hisobla: "
                    f"{matn}"
                ),
            }
        ]
    )


async def taom_tavsiya_qil(
    qolgan_kaloriya: int, qolgan_protein: float, maqsad: str
) -> tuple[str, list[str]]:
    """Qolgan limit asosida taom tavsiyasini so'raydi."""
    prompt = (
        f"Foydalanuvchining bugungi qolgan limiti: {qolgan_kaloriya} kcal, "
        f"{qolgan_protein:.0f}g oqsil. Maqsadi: {maqsad}. "
        "O'zbekistonda oson topiladigan 3 ta taom variantini tavsiya qil. "
        "JSON qaytar: {\"tavsiya\": \"bitta qisqa jumla\", "
        "\"variantlar\": [\"taom — ~kcal\", ...]}"
    )
    try:
        response = await get_client().chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "Sen o'zbek tilida javob beruvchi nutritsiologsan."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=300,
            temperature=0.6,
        )
        data = json.loads(response.choices[0].message.content or "{}")
        variantlar = [str(v) for v in (data.get("variantlar") or [])][:5]
        return str(data.get("tavsiya") or "Bugun uchun yaxshi tanlov qiling!"), variantlar
    except (APIError, json.JSONDecodeError, IndexError, KeyError) as exc:
        raise VisionError(f"Tavsiya olinmadi: {exc}") from exc
