"""Kunlik kaloriya va BJU limitlarini hisoblash (Mifflin-St Jeor)."""

from __future__ import annotations

from dataclasses import dataclass

ACTIVITY_FACTORS: dict[str, float] = {
    "sedentary": 1.200,  # deyarli harakatsiz
    "light": 1.375,  # haftada 1-3 kun
    "moderate": 1.550,  # haftada 3-5 kun
    "high": 1.725,  # haftada 6-7 kun
    "athlete": 1.900,  # kuniga 2 mashg'ulot / og'ir jismoniy mehnat
}

# maqsad -> (kaloriya koeffitsienti, protein %, yog' %, uglevod %)
GOAL_PROFILES: dict[str, tuple[float, float, float, float]] = {
    "yoqotish": (0.80, 0.35, 0.30, 0.35),
    "saqlash": (1.00, 0.30, 0.30, 0.40),
    "oshirish": (1.15, 0.30, 0.25, 0.45),
}

KCAL_PER_G = {"protein": 4.0, "yog": 9.0, "uglevod": 4.0}

MIN_CALORIES = {"erkak": 1500, "ayol": 1200}


@dataclass(slots=True)
class Limits:
    kaloriya: int
    protein_g: int
    yog_g: int
    uglevod_g: int
    suv_ml: int


def bmr_mifflin(jins: str, vazn_kg: float, boy_sm: float, yosh: int) -> float:
    """Bazal metabolizm tezligi (kcal/kun)."""
    base = 10 * vazn_kg + 6.25 * boy_sm - 5 * yosh
    return base + (5 if jins == "erkak" else -161)


def tdee(bmr: float, faollik: str) -> float:
    return bmr * ACTIVITY_FACTORS.get(faollik, ACTIVITY_FACTORS["light"])


def hisobla(
    *,
    jins: str,
    vazn_kg: float,
    boy_sm: float,
    yosh: int,
    faollik: str,
    maqsad: str,
) -> Limits:
    """Profil asosida kunlik limitlarni hisoblaydi."""
    total = tdee(bmr_mifflin(jins, vazn_kg, boy_sm, yosh), faollik)

    koef, p_pct, f_pct, c_pct = GOAL_PROFILES.get(maqsad, GOAL_PROFILES["saqlash"])
    kaloriya = max(total * koef, MIN_CALORIES.get(jins, 1200))
    kaloriya = round(kaloriya / 10) * 10  # chiroyli yaxlitlash

    return Limits(
        kaloriya=int(kaloriya),
        protein_g=round(kaloriya * p_pct / KCAL_PER_G["protein"]),
        yog_g=round(kaloriya * f_pct / KCAL_PER_G["yog"]),
        uglevod_g=round(kaloriya * c_pct / KCAL_PER_G["uglevod"]),
        suv_ml=int(round(vazn_kg * 33 / 100) * 100),
    )


def limitlarni_yangila(user) -> bool:  # noqa: ANN001 - models.User (aylanma importdan qochish)
    """Profil to'liq bo'lsa limitlarni qayta hisoblaydi. True = o'zgardi."""
    if user.limit_qolda:
        return False
    if not all((user.jins, user.yosh, user.boy_sm, user.joriy_vazn_kg)):
        return False

    lim = hisobla(
        jins=user.jins,
        vazn_kg=user.joriy_vazn_kg,
        boy_sm=user.boy_sm,
        yosh=user.yosh,
        faollik=user.faollik_darajasi,
        maqsad=user.maqsad_turi,
    )
    user.kunlik_kaloriya_limit = lim.kaloriya
    user.kunlik_protein_limit = lim.protein_g
    user.kunlik_yog_limit = lim.yog_g
    user.kunlik_uglevod_limit = lim.uglevod_g
    user.kunlik_suv_limit_ml = lim.suv_ml
    return True
