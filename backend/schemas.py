"""Pydantic schema'lar."""

from datetime import date as date_type
from datetime import time as time_type
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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
