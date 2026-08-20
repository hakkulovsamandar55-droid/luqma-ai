"""Pydantic schema'lar."""

from datetime import date as date_type
from datetime import datetime as datetime_type
from datetime import time as time_type
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Jins = Literal["erkak", "ayol"]
Faollik = Literal["sedentary", "light", "moderate", "high", "athlete"]
Maqsad = Literal["yoqotish", "saqlash", "oshirish"]


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    ism: str | None = None
    username: str | None = None
    telefon: str | None = None
    yosh: int | None = None
    jins: Jins | None = None
    boy_sm: float | None = None
    joriy_vazn_kg: float | None = None
    istalgan_vazn_kg: float | None = None
    faollik_darajasi: Faollik
    maqsad_turi: Maqsad
    kunlik_kaloriya_limit: int
    kunlik_protein_limit: int
    kunlik_yog_limit: int
    kunlik_uglevod_limit: int
    kunlik_suv_limit_ml: int
    limit_qolda: bool
    eslatmalar_yoqilgan: bool
    profil_toliq: bool

    # Premium holati — ilova cheklovlarni va statusni shu bo'yicha ko'rsatadi.
    is_premium: bool = False
    premium_faolmi: bool = False
    premium_tugash: datetime_type | None = None
    premium_tasdiq_kutilmoqda: bool = False


class UserUpdate(BaseModel):
    ism: str | None = Field(default=None, max_length=128)
    telefon: str | None = Field(default=None, max_length=32)
    yosh: int | None = Field(default=None, ge=5, le=120)
    jins: Jins | None = None
    boy_sm: float | None = Field(default=None, ge=80, le=250)
    joriy_vazn_kg: float | None = Field(default=None, ge=20, le=400)
    istalgan_vazn_kg: float | None = Field(default=None, ge=20, le=400)
    faollik_darajasi: Faollik | None = None
    maqsad_turi: Maqsad | None = None
    kunlik_kaloriya_limit: int | None = Field(default=None, ge=800, le=10000)
    kunlik_protein_limit: int | None = Field(default=None, ge=0, le=1000)
    kunlik_yog_limit: int | None = Field(default=None, ge=0, le=1000)
    kunlik_uglevod_limit: int | None = Field(default=None, ge=0, le=2000)
    kunlik_suv_limit_ml: int | None = Field(default=None, ge=0, le=10000)
    eslatmalar_yoqilgan: bool | None = None


class AuthOut(BaseModel):
    user: UserOut
    yangi: bool


class MealAnalysis(BaseModel):
    """AI tahlili natijasi — hali saqlanmagan preview."""

    taom_nomi: str
    ulush: str | None = None
    kaloriya: int
    protein_g: float
    yog_g: float
    uglevod_g: float
    ishonch: float = Field(default=0.0, ge=0, le=1)
    izoh: str | None = None
    rasm_yoli: str | None = None


class MealCreate(BaseModel):
    taom_nomi: str = Field(min_length=1, max_length=160)
    ulush: str | None = Field(default=None, max_length=80)
    kaloriya: int = Field(ge=0, le=20000)
    protein_g: float = Field(default=0, ge=0, le=2000)
    yog_g: float = Field(default=0, ge=0, le=2000)
    uglevod_g: float = Field(default=0, ge=0, le=2000)
    rasm_yoli: str | None = None
    manba: Literal["ai", "qolda", "favorite"] = "ai"
    sana: date_type | None = None
    vaqt: time_type | None = None


class MealOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    taom_nomi: str
    ulush: str | None
    kaloriya: int
    protein_g: float
    yog_g: float
    uglevod_g: float
    rasm_yoli: str | None
    manba: str
    sana: date_type
    vaqt: time_type


class MacroProgress(BaseModel):
    istemol: float
    limit: float
    qolgan: float


class DaySummary(BaseModel):
    sana: date_type
    kaloriya: MacroProgress
    protein: MacroProgress
    yog: MacroProgress
    uglevod: MacroProgress
    suv_ml: int
    suv_limit_ml: int
    ovqatlar_soni: int
    streak: int


class DayPoint(BaseModel):
    sana: date_type
    kaloriya: int
    protein_g: float
    yog_g: float
    uglevod_g: float


class WeeklyStats(BaseModel):
    kunlar: list[DayPoint]
    ortacha_kaloriya: int
    limit: int


class TextAnalyzeIn(BaseModel):
    matn: str = Field(min_length=2, max_length=300)


class WeightIn(BaseModel):
    vazn_kg: float = Field(ge=20, le=400)
    sana: date_type | None = None


class WeightOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vazn_kg: float
    sana: date_type


class WaterIn(BaseModel):
    miqdor_ml: int = Field(ge=-5000, le=5000)
    sana: date_type | None = None


class FavoriteIn(BaseModel):
    taom_nomi: str = Field(min_length=1, max_length=160)
    ulush: str | None = None
    kaloriya: int = Field(ge=0, le=20000)
    protein_g: float = 0
    yog_g: float = 0
    uglevod_g: float = 0


class FavoriteOut(FavoriteIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class SuggestionOut(BaseModel):
    tavsiya: str
    variantlar: list[str] = []


# --------------------------------------------------------------------------- #
# Murabbiy
# --------------------------------------------------------------------------- #
class ChatIn(BaseModel):
    matn: str = Field(min_length=1, max_length=1000)

    @field_validator("matn")
    @classmethod
    def _bosh_emas(cls, v: str) -> str:
        """Faqat probeldan iborat savol AI ga yuborilmasin."""
        v = v.strip()
        if not v:
            raise ValueError("Savol bo'sh bo'lmasligi kerak")
        return v


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rol: str
    matn: str


class CoachTipOut(BaseModel):
    tavsiya: str


# --------------------------------------------------------------------------- #
# Admin
# --------------------------------------------------------------------------- #
class AdminStats(BaseModel):
    jami_foydalanuvchi: int
    yangi_bugun: int
    yangi_hafta: int
    faol_bugun: int
    faol_hafta: int
    premium_soni: int
    bloklangan_soni: int
    admin_soni: int
    bugun_ovqat: int
    bugun_ai_chaqiruv: int
    umumiy_kunlik_limit: int


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    ism: str | None
    username: str | None
    is_admin: bool
    is_premium: bool
    premium_faolmi: bool
    premium_tugash: datetime_type | None
    is_blocked: bool
    block_sabab: str | None
    created_at: datetime_type
    oxirgi_faollik: datetime_type | None
    asosiy_admin: bool = False
    ovqatlar_soni: int = 0


class AdminUserList(BaseModel):
    jami: int
    foydalanuvchilar: list[AdminUserOut]


class AdminUserPatch(BaseModel):
    """Faqat yuborilgan maydonlar o'zgaradi."""

    is_admin: bool | None = None
    is_premium: bool | None = None
    premium_kun: int | None = Field(default=None, ge=0, le=3650)
    is_blocked: bool | None = None
    block_sabab: str | None = Field(default=None, max_length=256)


# --------------------------------------------------------------------------- #
# Tarif va to'lov
# --------------------------------------------------------------------------- #
class TarifOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    kun: int
    narx: int
    tavsif: str | None
    faol: bool
    tartib: int


class TarifIn(BaseModel):
    nom: str = Field(min_length=1, max_length=64)
    kun: int = Field(ge=1, le=3650)
    narx: int = Field(ge=0, le=1_000_000_000)
    tavsif: str | None = Field(default=None, max_length=200)
    faol: bool = True
    tartib: int = 0


class TarifPatch(BaseModel):
    nom: str | None = Field(default=None, min_length=1, max_length=64)
    kun: int | None = Field(default=None, ge=1, le=3650)
    narx: int | None = Field(default=None, ge=0, le=1_000_000_000)
    tavsif: str | None = Field(default=None, max_length=200)
    faol: bool | None = None
    tartib: int | None = None


class TolovSozlamaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    karta_raqam: str
    karta_egasi: str
    izoh: str | None
    chek_amal_kuni: int
    yordam_username: str = ""
    premium_sarlavha: str = ""
    premium_afzalliklar: str = ""


class TolovSozlamaIn(BaseModel):
    karta_raqam: str = Field(max_length=32)
    karta_egasi: str = Field(max_length=128)
    izoh: str | None = Field(default=None, max_length=300)
    chek_amal_kuni: int = Field(default=3, ge=1, le=90)
    yordam_username: str = Field(default="", max_length=64)
    premium_sarlavha: str = Field(default="", max_length=120)
    premium_afzalliklar: str = Field(default="", max_length=2000)


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tarif_nom: str
    tarif_kun: int
    kutilgan_summa: int
    holat: str
    avto_otdi: bool
    tekshiruv_izoh: str | None
    admin_izoh: str | None
    chek_yoli: str | None
    aniqlangan_summa: int | None
    aniqlangan_sana: str | None
    created_at: datetime_type


class PaymentAdminOut(PaymentOut):
    user_id: int
    user_ism: str | None = None
    user_telegram_id: int = 0
    ai_matn: str | None = None
    aniqlangan_karta: str | None = None
    tranzaksiya_id: str | None = None


class PaymentReview(BaseModel):
    tasdiq: bool
    izoh: str | None = Field(default=None, max_length=300)


# --------------------------------------------------------------------------- #
# Ovqat bazasi
# --------------------------------------------------------------------------- #
class FoodItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    ulush: str
    ulush_gramm: int
    kaloriya: int
    protein_g: float
    yog_g: float
    uglevod_g: float
    turkum: str


class FoodItemIn(BaseModel):
    nom: str = Field(min_length=1, max_length=120)
    kalit_sozlar: str = Field(default="", max_length=300)
    ulush: str = Field(default="100 g", max_length=64)
    ulush_gramm: int = Field(default=100, ge=1, le=5000)
    kaloriya: int = Field(default=0, ge=0, le=10000)
    protein_g: float = Field(default=0, ge=0, le=1000)
    yog_g: float = Field(default=0, ge=0, le=1000)
    uglevod_g: float = Field(default=0, ge=0, le=1000)
    turkum: str = Field(default="umumiy", max_length=32)
    faol: bool = True


# --------------------------------------------------------------------------- #
# Mashq
# --------------------------------------------------------------------------- #
class ExerciseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    tavsif: str | None
    daraja: str
    turkum: str
    davomiylik_sek: int
    takror: str | None
    kaloriya: int
    video_url: str | None
    rasm_url: str | None
    faol: bool
    tartib: int


class ExerciseIn(BaseModel):
    nom: str = Field(min_length=1, max_length=120)
    tavsif: str | None = Field(default=None, max_length=2000)
    daraja: Literal["boshlangich", "orta", "yuqori"] = "boshlangich"
    turkum: Literal["kuch", "chozilish", "harakatchanlik", "umumiy"] = "umumiy"
    davomiylik_sek: int = Field(default=60, ge=5, le=7200)
    takror: str | None = Field(default=None, max_length=64)
    kaloriya: int = Field(default=0, ge=0, le=5000)
    video_url: str | None = Field(default=None, max_length=500)
    rasm_url: str | None = Field(default=None, max_length=500)
    faol: bool = True
    tartib: int = 0


class ExerciseLogIn(BaseModel):
    exercise_id: int | None = None
    nom: str = Field(default="", max_length=120)
    davomiylik_sek: int = Field(default=0, ge=0, le=7200)
    kaloriya: int = Field(default=0, ge=0, le=5000)
    sana: date_type | None = None


class ExerciseLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    davomiylik_sek: int
    kaloriya: int
    sana: date_type


# --------------------------------------------------------------------------- #
# Eslatmalar
# --------------------------------------------------------------------------- #
class ReminderIn(BaseModel):
    tur: Literal["ovqat", "suv", "harakat", "uyqu"]
    matn: str = Field(default="", max_length=200)
    soat: int = Field(ge=0, le=23)
    daqiqa: int = Field(default=0, ge=0, le=59)
    yoqilgan: bool = True


class ReminderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tur: str
    matn: str
    soat: int
    daqiqa: int
    yoqilgan: bool
