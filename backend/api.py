"""FastAPI ilovasi — Mini App uchun REST API."""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from datetime import date as date_type
from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

import vision
from auth import current_user, get_or_create_user, parse_init_data, InitDataError, TelegramUser
from config import settings
from db import get_session, init_db
from models import Favorite, Meal, User, WaterLog, WeightLog
from nutrition import limitlarni_yangila
from schemas import (
    AuthOut,
    DayPoint,
    DaySummary,
    FavoriteIn,
    FavoriteOut,
    MacroProgress,
    MealAnalysis,
    MealCreate,
    MealOut,
    SuggestionOut,
    TextAnalyzeIn,
    UserOut,
    UserUpdate,
    WaterIn,
    WeeklyStats,
    WeightIn,
    WeightOut,
)

log = logging.getLogger(__name__)

MAX_IMAGE_BYTES = 8 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    log.info("Luqma AI API ishga tushdi (dev_mode=%s)", settings.dev_mode)
    yield


app = FastAPI(title="Luqma AI API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings.media_path.mkdir(parents=True, exist_ok=True)
app.mount(
    settings.media_url_prefix,
    StaticFiles(directory=settings.media_path),
    name="media",
)


# --------------------------------------------------------------------------- #
# Yordamchilar
# --------------------------------------------------------------------------- #
def _bugun(sana: date_type | None) -> date_type:
    return sana or datetime.now().date()


async def _rasmni_saqla(rasm: UploadFile) -> tuple[bytes, str]:
    """Yuklangan rasmni tekshiradi va diskka saqlaydi. -> (baytlar, nisbiy url)"""
    if rasm.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Faqat rasm fayllari qabul qilinadi (JPEG/PNG/WebP)",
        )

    data = await rasm.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Rasm bo'sh")
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Rasm hajmi 8MB dan katta bo'lmasligi kerak",
        )

    ext = {"image/png": ".png", "image/webp": ".webp"}.get(rasm.content_type, ".jpg")
    name = f"{uuid.uuid4().hex}{ext}"
    (settings.media_path / name).write_bytes(data)
    return data, f"{settings.media_url_prefix}/{name}"


async def _streak(session: AsyncSession, user_id: int, sana: date_type) -> int:
    """Ketma-ket necha kun ovqat kiritilgani (berilgan sanadan orqaga)."""
    rows = await session.execute(
        select(Meal.sana)
        .where(Meal.user_id == user_id, Meal.sana <= sana)
        .distinct()
        .order_by(Meal.sana.desc())
        .limit(400)
    )
    kunlar = [r[0] for r in rows]
    if not kunlar:
        return 0

    # Bugun hali kiritilmagan bo'lsa, kechadan boshlab sanaymiz.
    kutilgan = sana if kunlar[0] == sana else sana - timedelta(days=1)
    if kunlar[0] != kutilgan:
        return 0

    streak = 0
    for kun in kunlar:
        if kun == kutilgan:
            streak += 1
            kutilgan -= timedelta(days=1)
        elif kun < kutilgan:
            break
    return streak


async def _kunlik_yigindi(session: AsyncSession, user_id: int, sana: date_type):
    return (
        await session.execute(
            select(
                func.coalesce(func.sum(Meal.kaloriya), 0),
                func.coalesce(func.sum(Meal.protein_g), 0.0),
                func.coalesce(func.sum(Meal.yog_g), 0.0),
                func.coalesce(func.sum(Meal.uglevod_g), 0.0),
                func.count(Meal.id),
            ).where(Meal.user_id == user_id, Meal.sana == sana)
        )
    ).one()


def _progress(istemol: float, limit: float) -> MacroProgress:
    return MacroProgress(
        istemol=round(istemol, 1),
        limit=round(limit, 1),
        qolgan=round(limit - istemol, 1),
    )


# --------------------------------------------------------------------------- #
# Auth va profil
# --------------------------------------------------------------------------- #
@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "app": "luqma-ai"}


@app.post("/api/auth", response_model=AuthOut)
async def auth(
    payload: dict,
    session: AsyncSession = Depends(get_session),
) -> AuthOut:
    """initData ni tekshiradi, foydalanuvchini yaratadi yoki topadi."""
    init_data = str(payload.get("init_data") or "")

    if settings.dev_mode and not init_data:
        tg = TelegramUser(id=settings.dev_telegram_id, first_name="Dev")
    else:
        try:
            tg = parse_init_data(init_data, settings.bot_token, settings.initdata_max_age)
        except InitDataError as exc:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user, yangi = await get_or_create_user(session, tg)
    return AuthOut(user=UserOut.model_validate(user), yangi=yangi)


@app.get("/api/user/me", response_model=UserOut)
async def user_me(user: User = Depends(current_user)) -> UserOut:
    return UserOut.model_validate(user)


@app.put("/api/user/me", response_model=UserOut)
async def user_update(
    payload: UserUpdate,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> UserOut:
    """Profilni yangilaydi va limitlarni qayta hisoblaydi."""
    data = payload.model_dump(exclude_unset=True)

    limit_maydonlari = {
        "kunlik_kaloriya_limit",
        "kunlik_protein_limit",
        "kunlik_yog_limit",
        "kunlik_uglevod_limit",
        "kunlik_suv_limit_ml",
    }
    qolda_kiritildi = bool(limit_maydonlari & data.keys())

    for key, value in data.items():
        setattr(user, key, value)

    if qolda_kiritildi:
        user.limit_qolda = True
    else:
        limitlarni_yangila(user)

    # Vazn o'zgarsa — vazn tarixiga ham yozamiz.
    if "joriy_vazn_kg" in data and data["joriy_vazn_kg"]:
        bugun = datetime.now().date()
        mavjud = await session.scalar(
            select(WeightLog).where(WeightLog.user_id == user.id, WeightLog.sana == bugun)
        )
        if mavjud:
            mavjud.vazn_kg = data["joriy_vazn_kg"]
        else:
            session.add(
                WeightLog(user_id=user.id, vazn_kg=data["joriy_vazn_kg"], sana=bugun)
            )

    await session.commit()
    await session.refresh(user)
    return UserOut.model_validate(user)


@app.post("/api/user/limits/reset", response_model=UserOut)
async def limitlarni_tikla(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> UserOut:
    """Qo'lda kiritilgan limitlarni bekor qilib, formula bo'yicha qayta hisoblaydi."""
    user.limit_qolda = False
    limitlarni_yangila(user)
    await session.commit()
    await session.refresh(user)
    return UserOut.model_validate(user)


# --------------------------------------------------------------------------- #
# Ovqatlar
# --------------------------------------------------------------------------- #
@app.post("/api/meals/analyze", response_model=MealAnalysis)
async def meal_analyze(
    rasm: UploadFile = File(...),
    saqlash: bool = Form(default=True),
    user: User = Depends(current_user),
) -> MealAnalysis:
    """Rasmni AI bilan tahlil qiladi. Natija hali DB ga yozilmaydi (preview)."""
    data, url = await _rasmni_saqla(rasm)
    try:
        natija = await vision.rasmni_tahlil_qil(data, rasm.content_type or "image/jpeg")
    except vision.VisionError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    natija.rasm_yoli = url if saqlash else None
    return natija


@app.post("/api/meals/analyze-text", response_model=MealAnalysis)
async def meal_analyze_text(
    payload: TextAnalyzeIn,
    user: User = Depends(current_user),
) -> MealAnalysis:
    """Qo'lda kiritilgan matnni tahlil qiladi (masalan '150g osh')."""
    try:
        return await vision.matnni_tahlil_qil(payload.matn)
    except vision.VisionError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@app.post("/api/meals", response_model=MealOut, status_code=status.HTTP_201_CREATED)
async def meal_create(
    payload: MealCreate,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> MealOut:
    """Tasdiqlangan ovqatni saqlaydi."""
    now = datetime.now()
    meal = Meal(
        user_id=user.id,
        taom_nomi=payload.taom_nomi.strip(),
        ulush=payload.ulush,
        kaloriya=payload.kaloriya,
        protein_g=payload.protein_g,
        yog_g=payload.yog_g,
        uglevod_g=payload.uglevod_g,
        rasm_yoli=payload.rasm_yoli,
        manba=payload.manba,
        sana=payload.sana or now.date(),
        vaqt=payload.vaqt or now.time().replace(microsecond=0),
    )
    session.add(meal)
    await session.commit()
    await session.refresh(meal)
    return MealOut.model_validate(meal)


@app.get("/api/meals", response_model=list[MealOut])
async def meals_list(
    date: date_type | None = Query(default=None),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> list[MealOut]:
    sana = _bugun(date)
    rows = await session.execute(
        select(Meal)
        .where(Meal.user_id == user.id, Meal.sana == sana)
        .order_by(Meal.vaqt.desc(), Meal.id.desc())
    )
    return [MealOut.model_validate(m) for m in rows.scalars()]


@app.get("/api/meals/recent", response_model=list[MealOut])
async def meals_recent(
    limit: int = Query(default=10, ge=1, le=50),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> list[MealOut]:
    rows = await session.execute(
        select(Meal)
        .where(Meal.user_id == user.id)
        .order_by(Meal.sana.desc(), Meal.vaqt.desc(), Meal.id.desc())
        .limit(limit)
    )
    return [MealOut.model_validate(m) for m in rows.scalars()]


@app.delete("/api/meals/{meal_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def meal_delete(
    meal_id: int,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    meal = await session.scalar(
        select(Meal).where(Meal.id == meal_id, Meal.user_id == user.id)
    )
    if not meal:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ovqat topilmadi")
    await session.delete(meal)
    await session.commit()


@app.put("/api/meals/{meal_id}", response_model=MealOut)
async def meal_update(
    meal_id: int,
    payload: MealCreate,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> MealOut:
    meal = await session.scalar(
        select(Meal).where(Meal.id == meal_id, Meal.user_id == user.id)
    )
    if not meal:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ovqat topilmadi")

    for key, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(meal, key, value)
    await session.commit()
    await session.refresh(meal)
    return MealOut.model_validate(meal)


# --------------------------------------------------------------------------- #
# Statistika
# --------------------------------------------------------------------------- #
@app.get("/api/stats/summary", response_model=DaySummary)
async def stats_summary(
    date: date_type | None = Query(default=None),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> DaySummary:
    sana = _bugun(date)
    kcal, protein, yog, uglevod, soni = await _kunlik_yigindi(session, user.id, sana)

    suv = await session.scalar(
        select(WaterLog.miqdor_ml).where(
            WaterLog.user_id == user.id, WaterLog.sana == sana
        )
    )

    return DaySummary(
        sana=sana,
        kaloriya=_progress(kcal, user.kunlik_kaloriya_limit),
        protein=_progress(protein, user.kunlik_protein_limit),
        yog=_progress(yog, user.kunlik_yog_limit),
        uglevod=_progress(uglevod, user.kunlik_uglevod_limit),
        suv_ml=suv or 0,
        suv_limit_ml=user.kunlik_suv_limit_ml,
        ovqatlar_soni=soni,
        streak=await _streak(session, user.id, sana),
    )


@app.get("/api/stats/weekly", response_model=WeeklyStats)
async def stats_weekly(
    date: date_type | None = Query(default=None),
    kunlar: int = Query(default=7, ge=2, le=90),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> WeeklyStats:
    oxiri = _bugun(date)
    boshi = oxiri - timedelta(days=kunlar - 1)

    rows = await session.execute(
        select(
            Meal.sana,
            func.coalesce(func.sum(Meal.kaloriya), 0),
            func.coalesce(func.sum(Meal.protein_g), 0.0),
            func.coalesce(func.sum(Meal.yog_g), 0.0),
            func.coalesce(func.sum(Meal.uglevod_g), 0.0),
        )
        .where(Meal.user_id == user.id, Meal.sana.between(boshi, oxiri))
        .group_by(Meal.sana)
    )
    xarita = {r[0]: r for r in rows}

    natija: list[DayPoint] = []
    for i in range(kunlar):
        kun = boshi + timedelta(days=i)
        r = xarita.get(kun)
        natija.append(
            DayPoint(
                sana=kun,
                kaloriya=int(r[1]) if r else 0,
                protein_g=round(r[2], 1) if r else 0.0,
                yog_g=round(r[3], 1) if r else 0.0,
                uglevod_g=round(r[4], 1) if r else 0.0,
            )
        )

    faol = [p.kaloriya for p in natija if p.kaloriya > 0]
    return WeeklyStats(
        kunlar=natija,
        ortacha_kaloriya=int(sum(faol) / len(faol)) if faol else 0,
        limit=user.kunlik_kaloriya_limit,
    )


@app.get("/api/stats/suggestion", response_model=SuggestionOut)
async def stats_suggestion(
    date: date_type | None = Query(default=None),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> SuggestionOut:
    """Qolgan limit asosida AI dan taom tavsiyasini so'raydi."""
    sana = _bugun(date)
    kcal, protein, *_ = await _kunlik_yigindi(session, user.id, sana)
    try:
        tavsiya, variantlar = await vision.taom_tavsiya_qil(
            max(0, user.kunlik_kaloriya_limit - int(kcal)),
            max(0.0, user.kunlik_protein_limit - float(protein)),
            user.maqsad_turi,
        )
    except vision.VisionError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return SuggestionOut(tavsiya=tavsiya, variantlar=variantlar)


# --------------------------------------------------------------------------- #
# Suv
# --------------------------------------------------------------------------- #
@app.post("/api/water")
async def water_add(
    payload: WaterIn,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, int]:
    sana = _bugun(payload.sana)
    row = await session.scalar(
        select(WaterLog).where(WaterLog.user_id == user.id, WaterLog.sana == sana)
    )
    if row is None:
        row = WaterLog(user_id=user.id, sana=sana, miqdor_ml=0)
        session.add(row)
    row.miqdor_ml = max(0, row.miqdor_ml + payload.miqdor_ml)
    await session.commit()
    return {"miqdor_ml": row.miqdor_ml, "limit_ml": user.kunlik_suv_limit_ml}


# --------------------------------------------------------------------------- #
# Vazn
# --------------------------------------------------------------------------- #
@app.post("/api/weight", response_model=WeightOut)
async def weight_add(
    payload: WeightIn,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> WeightOut:
    sana = _bugun(payload.sana)
    row = await session.scalar(
        select(WeightLog).where(WeightLog.user_id == user.id, WeightLog.sana == sana)
    )
    if row:
        row.vazn_kg = payload.vazn_kg
    else:
        row = WeightLog(user_id=user.id, vazn_kg=payload.vazn_kg, sana=sana)
        session.add(row)

    user.joriy_vazn_kg = payload.vazn_kg
    limitlarni_yangila(user)
    await session.commit()
    await session.refresh(row)
    return WeightOut.model_validate(row)


@app.get("/api/weight", response_model=list[WeightOut])
async def weight_list(
    limit: int = Query(default=30, ge=1, le=365),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> list[WeightOut]:
    rows = await session.execute(
        select(WeightLog)
        .where(WeightLog.user_id == user.id)
        .order_by(WeightLog.sana.desc())
        .limit(limit)
    )
    return [WeightOut.model_validate(r) for r in reversed(rows.scalars().all())]


# --------------------------------------------------------------------------- #
# Sevimli taomlar
# --------------------------------------------------------------------------- #
@app.get("/api/favorites", response_model=list[FavoriteOut])
async def favorites_list(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> list[FavoriteOut]:
    rows = await session.execute(
        select(Favorite)
        .where(Favorite.user_id == user.id)
        .order_by(Favorite.created_at.desc())
    )
    return [FavoriteOut.model_validate(f) for f in rows.scalars()]


@app.post("/api/favorites", response_model=FavoriteOut, status_code=status.HTTP_201_CREATED)
async def favorite_add(
    payload: FavoriteIn,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> FavoriteOut:
    fav = Favorite(user_id=user.id, **payload.model_dump())
    session.add(fav)
    await session.commit()
    await session.refresh(fav)
    return FavoriteOut.model_validate(fav)


@app.delete("/api/favorites/{fav_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def favorite_delete(
    fav_id: int,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    result = await session.execute(
        delete(Favorite).where(Favorite.id == fav_id, Favorite.user_id == user.id)
    )
    if result.rowcount == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Topilmadi")
    await session.commit()
