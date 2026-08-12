"""FastAPI ilovasi — Mini App uchun REST API."""

from __future__ import annotations

import logging
import uuid

import logging_setup
from contextlib import asynccontextmanager
from datetime import date as date_type
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

import admin
import chat as coach
import receipt
import limits
import timeutil
import vision
from auth import current_user, get_or_create_user, parse_init_data, InitDataError, TelegramUser
from config import settings
from db import get_session, init_db
from models import (
    AiUsage,
    Exercise,
    ExerciseLog,
    FoodItem,
    Reminder,
    ChatMessage,
    Favorite,
    Meal,
    Payment,
    Tarif,
    TolovSozlama,
    User,
    WaterLog,
    WeightLog,
)
from nutrition import limitlarni_yangila
from schemas import (
    AdminStats,
    ExerciseIn,
    ExerciseLogIn,
    ExerciseLogOut,
    ExerciseOut,
    FoodItemIn,
    FoodItemOut,
    ReminderIn,
    ReminderOut,
    PaymentAdminOut,
    PaymentOut,
    PaymentReview,
    TarifIn,
    TarifOut,
    TarifPatch,
    TolovSozlamaIn,
    TolovSozlamaOut,
    AdminUserList,
    AdminUserOut,
    AdminUserPatch,
    AuthOut,
    ChatIn,
    ChatMessageOut,
    CoachTipOut,
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

logging_setup.sozla()
log = logging.getLogger(__name__)

MAX_IMAGE_BYTES = 8 * 1024 * 1024

# MIME turi -> fayl kengaytmasi. HEIC/HEIF ataylab yo'q: OpenAI vision uni
# o'qiy olmaydi (chaqiruv xatoga uchraydi) va brauzerlarning ko'pi ko'rsata
# olmaydi — ya'ni qabul qilsak, rasm ham tahlil qilinmaydi, ham ochilmaydi.
# Foydalanuvchiga tushunarli xabar berish afzal.
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


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
    return sana or timeutil.bugun()


async def _rasmni_oqi(rasm: UploadFile) -> bytes:
    """Yuklangan faylni tekshiradi va baytlarini qaytaradi (diskka yozmaydi)."""
    ext = ALLOWED_IMAGE_TYPES.get(rasm.content_type or "")
    if ext is None:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Faqat JPEG, PNG yoki WebP rasm yuboring. iPhone'da rasm HEIC "
            "bo'lsa, Sozlamalar > Kamera > Formatlar > \"Eng mos\" ni tanlang.",
        )

    data = await rasm.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Rasm bo'sh")
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Rasm hajmi 8MB dan katta bo'lmasligi kerak",
        )
    return data


def _rasmni_yoz(data: bytes, content_type: str | None) -> str:
    """Baytlarni media papkasiga yozadi. -> nisbiy url"""
    ext = ALLOWED_IMAGE_TYPES.get(content_type or "", ".jpg")
    name = f"{uuid.uuid4().hex}{ext}"
    (settings.media_path / name).write_bytes(data)
    return f"{settings.media_url_prefix}/{name}"


async def _rasmni_saqla(rasm: UploadFile) -> tuple[bytes, str]:
    """Yuklangan rasmni tekshiradi va diskka saqlaydi. -> (baytlar, nisbiy url)"""
    data = await _rasmni_oqi(rasm)
    return data, _rasmni_yoz(data, rasm.content_type)


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
        bugun = timeutil.bugun()
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
    session: AsyncSession = Depends(get_session),
) -> MealAnalysis:
    """Rasmni AI bilan tahlil qiladi. Natija hali DB ga yozilmaydi (preview)."""
    await limits.premium_talab(session, user)
    await limits.tekshir_va_sana(session, user, "tahlil")
    data = await _rasmni_oqi(rasm)
    try:
        natija = await vision.rasmni_tahlil_qil(data, rasm.content_type or "image/jpeg")
    except vision.VisionError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    # Faqat kerak bo'lsa diskka yozamiz. Ilgari har bir tahlil fayl qoldirar,
    # keyin tozalash vazifasi ularni yig'ishtirib yurardi.
    natija.rasm_yoli = _rasmni_yoz(data, rasm.content_type) if saqlash else None
    return natija


@app.post("/api/meals/analyze-text", response_model=MealAnalysis)
async def meal_analyze_text(
    payload: TextAnalyzeIn,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> MealAnalysis:
    """Qo'lda kiritilgan matnni tahlil qiladi (masalan '150g osh')."""
    await limits.premium_talab(session, user)
    await limits.tekshir_va_sana(session, user, "tahlil")
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
    now = timeutil.hozir()
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


# --------------------------------------------------------------------------- #
# Murabbiy
# --------------------------------------------------------------------------- #
@app.get("/api/chat/history", response_model=list[ChatMessageOut])
async def chat_history(
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> list[ChatMessageOut]:
    """Suhbat tarixi — eskidan yangiga."""
    rows = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == user.id)
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
        .limit(limit)
    )
    return [ChatMessageOut.model_validate(m) for m in reversed(rows.scalars().all())]


@app.post("/api/chat", response_model=ChatMessageOut)
async def chat_send(
    payload: ChatIn,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> ChatMessageOut:
    """Murabbiyga savol yuboradi va javobini qaytaradi."""
    await limits.tekshir_va_sana(session, user, "chat")

    savol = payload.matn.strip()
    session.add(ChatMessage(user_id=user.id, rol="user", matn=savol))
    await session.commit()

    try:
        matn = await coach.javob_ol(session, user, savol)
    except vision.VisionError:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hozir javob bera olmadim, birozdan keyin urinib ko'ring",
        ) from None

    javob = ChatMessage(user_id=user.id, rol="murabbiy", matn=matn)
    session.add(javob)
    await session.commit()
    await session.refresh(javob)
    return ChatMessageOut.model_validate(javob)


@app.delete("/api/chat", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def chat_clear(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    await session.execute(delete(ChatMessage).where(ChatMessage.user_id == user.id))
    await session.commit()


@app.get("/api/chat/tip", response_model=CoachTipOut)
async def chat_tip(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> CoachTipOut:
    """Bosh sahifadagi kartochka uchun bir jumlalik maslahat."""
    return CoachTipOut(tavsiya=await coach.kunlik_maslahat(session, user))


# --------------------------------------------------------------------------- #
# Admin panel
# --------------------------------------------------------------------------- #
def _admin_user_out(u: User, ovqatlar: int = 0) -> AdminUserOut:
    """Model -> schema, hisoblanadigan maydonlar bilan."""
    return AdminUserOut(
        id=u.id,
        telegram_id=u.telegram_id,
        ism=u.ism,
        username=u.username,
        is_admin=bool(u.is_admin),
        is_premium=bool(u.is_premium),
        premium_faolmi=u.premium_faolmi,
        premium_tugash=u.premium_tugash,
        is_blocked=bool(u.is_blocked),
        block_sabab=u.block_sabab,
        created_at=u.created_at,
        oxirgi_faollik=u.oxirgi_faollik,
        asosiy_admin=admin.asosiy_adminmi(u),
        ovqatlar_soni=ovqatlar,
    )


@app.get("/api/admin/stats", response_model=AdminStats)
async def admin_stats(
    _: User = Depends(admin.current_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminStats:
    bugun = timeutil.bugun()
    # created_at ustunlari UTC da, oxirgi_faollik esa mahalliy zonada
    # yoziladi — shuning uchun ikki xil boshlanish nuqtasi kerak.
    kun_boshi_utc = timeutil.kun_boshi_utc()
    hafta_utc = kun_boshi_utc - timedelta(days=7)
    kun_boshi = timeutil.kun_boshi()
    hafta = kun_boshi - timedelta(days=7)

    async def son(q) -> int:
        return await session.scalar(q) or 0

    return AdminStats(
        jami_foydalanuvchi=await son(select(func.count(User.id))),
        yangi_bugun=await son(
            select(func.count(User.id)).where(User.created_at >= kun_boshi_utc)
        ),
        yangi_hafta=await son(
            select(func.count(User.id)).where(User.created_at >= hafta_utc)
        ),
        faol_bugun=await son(
            select(func.count(User.id)).where(User.oxirgi_faollik >= kun_boshi)
        ),
        faol_hafta=await son(
            select(func.count(User.id)).where(User.oxirgi_faollik >= hafta)
        ),
        premium_soni=await son(
            select(func.count(User.id)).where(User.is_premium.is_(True))
        ),
        bloklangan_soni=await son(
            select(func.count(User.id)).where(User.is_blocked.is_(True))
        ),
        admin_soni=await son(
            select(func.count(User.id)).where(User.is_admin.is_(True))
        ),
        bugun_ovqat=await son(select(func.count(Meal.id)).where(Meal.sana == bugun)),
        bugun_ai_chaqiruv=await limits.umumiy_hisob(session),
        umumiy_kunlik_limit=settings.umumiy_kunlik_limit,
    )


@app.get("/api/admin/users", response_model=AdminUserList)
async def admin_users(
    q: str | None = Query(default=None, max_length=64),
    filtr: str | None = Query(default=None, pattern="^(premium|bloklangan|admin)$"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=30, ge=1, le=100),
    _: User = Depends(admin.current_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminUserList:
    """Foydalanuvchilar ro'yxati — qidiruv va filtr bilan."""
    shart = select(User)

    if q:
        kalit = f"%{q.strip()}%"
        shartlar = [User.ism.ilike(kalit), User.username.ilike(kalit)]
        # Raqam kiritilgan bo'lsa Telegram ID bo'yicha ham qidiramiz.
        if q.strip().isdigit():
            shartlar.append(User.telegram_id == int(q.strip()))
        shart = shart.where(or_(*shartlar))

    if filtr == "premium":
        shart = shart.where(User.is_premium.is_(True))
    elif filtr == "bloklangan":
        shart = shart.where(User.is_blocked.is_(True))
    elif filtr == "admin":
        shart = shart.where(User.is_admin.is_(True))

    jami = await session.scalar(
        select(func.count()).select_from(shart.subquery())
    ) or 0

    rows = (
        await session.execute(
            shart.order_by(User.created_at.desc()).offset(offset).limit(limit)
        )
    ).scalars().all()

    # Har foydalanuvchi uchun ovqatlar sonini bitta so'rovda olamiz.
    idlar = [u.id for u in rows]
    sanoq: dict[int, int] = {}
    if idlar:
        natija = await session.execute(
            select(Meal.user_id, func.count(Meal.id))
            .where(Meal.user_id.in_(idlar))
            .group_by(Meal.user_id)
        )
        sanoq = dict(natija.all())

    return AdminUserList(
        jami=jami,
        foydalanuvchilar=[_admin_user_out(u, sanoq.get(u.id, 0)) for u in rows],
    )


@app.patch("/api/admin/users/{user_id}", response_model=AdminUserOut)
async def admin_user_update(
    user_id: int,
    payload: AdminUserPatch,
    aktor: User = Depends(admin.current_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminUserOut:
    """Admin/premium/blok holatini o'zgartiradi."""
    nishon = await session.get(User, user_id)
    if nishon is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Foydalanuvchi topilmadi")

    # .env dagi asosiy adminni panel orqali o'zgartirib bo'lmaydi — aks holda
    # adminlar bir-birini o'chirib, hech kim kira olmay qolishi mumkin.
    if admin.asosiy_adminmi(nishon) and (
        payload.is_admin is False or payload.is_blocked is True
    ):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Asosiy adminni o'zgartirib bo'lmaydi (.env dagi ADMIN_IDS)",
        )

    # O'zini o'zi bloklab yoki adminlikdan chiqarib qo'yishning oldini olamiz.
    if nishon.id == aktor.id and (
        payload.is_admin is False or payload.is_blocked is True
    ):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="O'zingizga bu amalni qo'llay olmaysiz"
        )

    if payload.is_admin is not None:
        nishon.is_admin = payload.is_admin

    if payload.is_premium is not None:
        nishon.is_premium = payload.is_premium
        if not payload.is_premium:
            nishon.premium_tugash = None
        elif payload.premium_kun:
            nishon.premium_tugash = timeutil.hozir() + timedelta(
                days=payload.premium_kun
            )
        elif payload.premium_kun == 0:
            nishon.premium_tugash = None  # muddatsiz

    if payload.is_blocked is not None:
        nishon.is_blocked = payload.is_blocked
        nishon.block_sabab = payload.block_sabab if payload.is_blocked else None

    await session.commit()
    await session.refresh(nishon)

    ovqatlar = (
        await session.scalar(
            select(func.count(Meal.id)).where(Meal.user_id == nishon.id)
        )
        or 0
    )
    return _admin_user_out(nishon, ovqatlar)


@app.get("/api/admin/me", response_model=dict)
async def admin_me(user: User = Depends(current_user)) -> dict:
    """Frontend admin tugmasini ko'rsatish-ko'rsatmaslikni shu orqali biladi."""
    return {"admin": admin.adminmi(user)}


@app.delete("/api/user/me", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def user_delete(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Foydalanuvchi o'z hisobini butunlay o'chiradi.

    Maxfiylik siyosatida "yordam xizmatiga yozing" deyilgan edi — bu ishlaydi,
    lekin odam o'z ma'lumotini o'zi o'chira olishi kerak.

    Bog'liq yozuvlar cascade bilan ketadi, lekin rasm fayllari diskda qoladi —
    ularni qo'lda o'chiramiz.
    """
    # Ovqat rasmlari va to'lov cheklari — ikkalasi ham shaxsiy ma'lumot.
    # Chekda ism, karta raqami va tranzaksiya ID bo'ladi, shuning uchun
    # hisob o'chirilganda ular ham diskdan ketishi kerak.
    rasmlar = list(
        (
            await session.execute(
                select(Meal.rasm_yoli).where(
                    Meal.user_id == user.id, Meal.rasm_yoli.is_not(None)
                )
            )
        ).scalars()
    ) + list(
        (
            await session.execute(
                select(Payment.chek_yoli).where(
                    Payment.user_id == user.id, Payment.chek_yoli.is_not(None)
                )
            )
        ).scalars()
    )

    for yol in rasmlar:
        try:
            (Path(settings.media_path) / Path(yol).name).unlink(missing_ok=True)
        except OSError:
            log.warning("Rasmni o'chirib bo'lmadi: %s", yol)

    # Cascade sozlanmagan jadvallarni aniq o'chiramiz. Ro'yxatga yangi jadval
    # qo'shishni unutmang — aks holda foydalanuvchi ma'lumoti bazada qoladi.
    for model in (
        ChatMessage,
        AiUsage,
        Favorite,
        WaterLog,
        WeightLog,
        ExerciseLog,
        Reminder,
        Payment,
        Meal,
    ):
        await session.execute(delete(model).where(model.user_id == user.id))

    await session.delete(user)
    await session.commit()


# --------------------------------------------------------------------------- #
# Tarif va to'lov — foydalanuvchi tomoni
# --------------------------------------------------------------------------- #
async def _tolov_sozlama(session: AsyncSession) -> TolovSozlama:
    """Sozlamalarni oladi, bo'lmasa bo'sh qator yaratadi."""
    s = await session.get(TolovSozlama, 1)
    if s is None:
        s = TolovSozlama(id=1)
        session.add(s)
        await session.commit()
        await session.refresh(s)
    return s


@app.get("/api/tariffs", response_model=list[TarifOut])
async def tariffs_list(
    _: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> list[TarifOut]:
    rows = (
        await session.execute(
            select(Tarif).where(Tarif.faol.is_(True)).order_by(Tarif.tartib, Tarif.narx)
        )
    ).scalars().all()
    return [TarifOut.model_validate(t) for t in rows]


@app.get("/api/payment-info", response_model=TolovSozlamaOut)
async def payment_info(
    _: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> TolovSozlamaOut:
    """Foydalanuvchiga ko'rsatiladigan karta rekvizitlari."""
    return TolovSozlamaOut.model_validate(await _tolov_sozlama(session))


@app.get("/api/payments/me", response_model=list[PaymentOut])
async def payments_me(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> list[PaymentOut]:
    rows = (
        await session.execute(
            select(Payment)
            .where(Payment.user_id == user.id)
            .order_by(Payment.created_at.desc())
            .limit(20)
        )
    ).scalars().all()
    return [PaymentOut.model_validate(p) for p in rows]


@app.post("/api/payments", response_model=PaymentOut)
async def payment_create(
    tarif_id: int = Form(...),
    chek: UploadFile = File(...),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> PaymentOut:
    """Chek yuborish va avtomatik tekshiruv.

    Mos kelsa premium DARHOL beriladi va admin tasdig'igacha amal qiladi.
    """
    # Spamdan himoya: kuniga cheklangan urinish.
    bugun_soni = (
        await session.scalar(
            select(func.count(Payment.id)).where(
                Payment.user_id == user.id,
                Payment.created_at >= timeutil.kun_boshi_utc(),
            )
        )
        or 0
    )
    if bugun_soni >= settings.chek_kunlik_limit:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Bugunga chek yuborish chegarasiga yetdingiz. Yordam xizmatiga yozing.",
        )

    tarif = await session.get(Tarif, tarif_id)
    if tarif is None or not tarif.faol:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tarif topilmadi")

    sozlama = await _tolov_sozlama(session)
    if not sozlama.karta_raqam:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="To'lov hozircha sozlanmagan. Keyinroq urinib ko'ring.",
        )

    data, url = await _rasmni_saqla(chek)
    hash_ = receipt.rasm_hash(data)

    payment = Payment(
        user_id=user.id,
        tarif_id=tarif.id,
        tarif_nom=tarif.nom,
        tarif_kun=tarif.kun,
        kutilgan_summa=tarif.narx,
        chek_yoli=url,
        chek_hash=hash_,
    )

    # Bir xil chek ilgari yuborilganmi.
    takror = await session.scalar(
        select(Payment).where(Payment.chek_hash == hash_).limit(1)
    )
    if takror is not None:
        payment.holat = "kutilmoqda"
        payment.tekshiruv_izoh = "Bu chek ilgari yuborilgan"
        session.add(payment)
        await session.commit()
        await session.refresh(payment)
        return PaymentOut.model_validate(payment)

    try:
        xom = await receipt.chekni_oqi(data, chek.content_type or "image/jpeg")
    except vision.VisionError:
        payment.tekshiruv_izoh = "Chekni o'qib bo'lmadi — admin ko'rib chiqadi"
        session.add(payment)
        await session.commit()
        await session.refresh(payment)
        return PaymentOut.model_validate(payment)

    natija = receipt.tekshir(
        xom,
        kutilgan_karta=sozlama.karta_raqam,
        kutilgan_ism=sozlama.karta_egasi,
        kutilgan_summa=tarif.narx,
        amal_kuni=sozlama.chek_amal_kuni,
        bugun=timeutil.bugun(),
    )

    payment.ai_matn = (xom.get("barcha_matn") or "")[:4000]
    payment.aniqlangan_karta = ", ".join(xom.get("karta_raqamlari") or [])[:32] or None
    payment.aniqlangan_summa = (
        int(xom["asosiy_summa"]) if xom.get("asosiy_summa") is not None else None
    )
    payment.aniqlangan_sana = xom.get("sana")
    payment.tranzaksiya_id = (xom.get("tranzaksiya_id") or None)
    payment.tekshiruv_izoh = natija.izoh[:500]
    payment.avto_otdi = natija.otdi

    # Bir xil tranzaksiya ID bilan tasdiqlangan to'lov bormi.
    if payment.tranzaksiya_id:
        eski = await session.scalar(
            select(Payment).where(
                Payment.tranzaksiya_id == payment.tranzaksiya_id,
                Payment.id != payment.id,
            )
        )
        if eski is not None:
            payment.avto_otdi = False
            payment.tekshiruv_izoh = "Bu tranzaksiya ilgari ishlatilgan"

    if payment.avto_otdi:
        # Premium darhol beriladi. Muddat admin tasdiqlaganda qo'yiladi —
        # shu paytgacha muddatsiz, ya'ni amal qiladi.
        user.is_premium = True
        user.premium_tugash = None
        user.premium_tasdiq_kutilmoqda = True

    session.add(payment)
    await session.commit()
    await session.refresh(payment)
    return PaymentOut.model_validate(payment)


# --------------------------------------------------------------------------- #
# Tarif va to'lov — admin tomoni
# --------------------------------------------------------------------------- #
@app.get("/api/admin/tariffs", response_model=list[TarifOut])
async def admin_tariffs(
    _: User = Depends(admin.current_admin),
    session: AsyncSession = Depends(get_session),
) -> list[TarifOut]:
    rows = (
        await session.execute(select(Tarif).order_by(Tarif.tartib, Tarif.narx))
    ).scalars().all()
    return [TarifOut.model_validate(t) for t in rows]


@app.post("/api/admin/tariffs", response_model=TarifOut)
async def admin_tarif_create(
    payload: TarifIn,
    _: User = Depends(admin.current_admin),
    session: AsyncSession = Depends(get_session),
) -> TarifOut:
    t = Tarif(**payload.model_dump())
    session.add(t)
    await session.commit()
    await session.refresh(t)
    return TarifOut.model_validate(t)


@app.patch("/api/admin/tariffs/{tarif_id}", response_model=TarifOut)
async def admin_tarif_update(
    tarif_id: int,
    payload: TarifPatch,
    _: User = Depends(admin.current_admin),
    session: AsyncSession = Depends(get_session),
) -> TarifOut:
    t = await session.get(Tarif, tarif_id)
    if t is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tarif topilmadi")

    for maydon, qiymat in payload.model_dump(exclude_unset=True).items():
        setattr(t, maydon, qiymat)

    await session.commit()
    await session.refresh(t)
    return TarifOut.model_validate(t)


@app.delete(
    "/api/admin/tariffs/{tarif_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def admin_tarif_delete(
    tarif_id: int,
    _: User = Depends(admin.current_admin),
    session: AsyncSession = Depends(get_session),
) -> None:
    t = await session.get(Tarif, tarif_id)
    if t is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tarif topilmadi")
    await session.delete(t)
    await session.commit()


@app.get("/api/admin/payment-settings", response_model=TolovSozlamaOut)
async def admin_payment_settings(
    _: User = Depends(admin.current_admin),
    session: AsyncSession = Depends(get_session),
) -> TolovSozlamaOut:
    return TolovSozlamaOut.model_validate(await _tolov_sozlama(session))


@app.put("/api/admin/payment-settings", response_model=TolovSozlamaOut)
async def admin_payment_settings_update(
    payload: TolovSozlamaIn,
    _: User = Depends(admin.current_admin),
    session: AsyncSession = Depends(get_session),
) -> TolovSozlamaOut:
    s = await _tolov_sozlama(session)
    for maydon, qiymat in payload.model_dump().items():
        setattr(s, maydon, qiymat)
    await session.commit()
    await session.refresh(s)
    return TolovSozlamaOut.model_validate(s)


@app.get("/api/admin/payments", response_model=list[PaymentAdminOut])
async def admin_payments(
    holat: str | None = Query(
        default=None, pattern="^(kutilmoqda|tasdiqlangan|rad_etilgan)$"
    ),
    limit: int = Query(default=50, ge=1, le=200),
    _: User = Depends(admin.current_admin),
    session: AsyncSession = Depends(get_session),
) -> list[PaymentAdminOut]:
    shart = select(Payment, User).join(User, Payment.user_id == User.id)
    if holat:
        shart = shart.where(Payment.holat == holat)

    rows = (
        await session.execute(shart.order_by(Payment.created_at.desc()).limit(limit))
    ).all()

    natija = []
    for p, u in rows:
        d = PaymentAdminOut.model_validate(p)
        d.user_ism = u.ism
        d.user_telegram_id = u.telegram_id
        natija.append(d)
    return natija


@app.patch("/api/admin/payments/{payment_id}", response_model=PaymentAdminOut)
async def admin_payment_review(
    payment_id: int,
    payload: PaymentReview,
    aktor: User = Depends(admin.current_admin),
    session: AsyncSession = Depends(get_session),
) -> PaymentAdminOut:
    """Admin arizani tasdiqlaydi yoki rad etadi."""
    p = await session.get(Payment, payment_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ariza topilmadi")

    egasi = await session.get(User, p.user_id)

    if payload.tasdiq:
        p.holat = "tasdiqlangan"
        if egasi:
            # Muddat shu paytdan boshlanadi. Agar premium allaqachon bo'lsa
            # (masalan avtomatik berilgan), qolgan muddat ustiga qo'shiladi.
            boshlanish = timeutil.hozir()
            if egasi.premium_tugash and egasi.premium_tugash.replace(
                tzinfo=None
            ) > boshlanish:
                boshlanish = egasi.premium_tugash.replace(tzinfo=None)
            egasi.is_premium = True
            egasi.premium_tugash = boshlanish + timedelta(days=p.tarif_kun)
            egasi.premium_tasdiq_kutilmoqda = False
    else:
        p.holat = "rad_etilgan"
        # Premiumni faqat AYNAN shu ariza tufayli berilgan bo'lsa olib qo'yamiz.
        # Foydalanuvchi ketma-ket bir nechta chek yuborgan bo'lishi mumkin: agar
        # boshqa avtomatik o'tgan, hali ko'rilmagan ariza bo'lsa, premium unga
        # tegishli — bittasini rad etganda hammasini o'chirib yubormaymiz.
        if egasi and egasi.premium_tasdiq_kutilmoqda and p.avto_otdi:
            boshqa_kutilayotgan = await session.scalar(
                select(func.count(Payment.id)).where(
                    Payment.user_id == p.user_id,
                    Payment.id != p.id,
                    Payment.avto_otdi.is_(True),
                    Payment.holat == "kutilmoqda",
                )
            )
            if not boshqa_kutilayotgan:
                egasi.is_premium = False
                egasi.premium_tugash = None
                egasi.premium_tasdiq_kutilmoqda = False

    p.admin_izoh = payload.izoh
    p.admin_id = aktor.id
    p.korilgan_at = timeutil.hozir()

    await session.commit()
    await session.refresh(p)

    d = PaymentAdminOut.model_validate(p)
    if egasi:
        d.user_ism = egasi.ism
        d.user_telegram_id = egasi.telegram_id
    return d


# --------------------------------------------------------------------------- #
# Ovqat bazasi — qidiruv
# --------------------------------------------------------------------------- #
@app.get("/api/foods", response_model=list[FoodItemOut])
async def foods_search(
    q: str | None = Query(default=None, max_length=64),
    limit: int = Query(default=40, ge=1, le=200),
    _: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> list[FoodItemOut]:
    """Mahalliy bazadan ovqat qidiradi.

    AI chaqirilmaydi — shuning uchun tez, bepul va premium talab qilmaydi.
    Foydalanuvchi ko'p yeydigan taomlarni shu yerdan topadi, AI faqat
    notanish taomlar uchun kerak bo'ladi.
    """
    shart = select(FoodItem).where(FoodItem.faol.is_(True))

    if q and q.strip():
        kalit = f"%{q.strip().lower()}%"
        shart = shart.where(
            or_(
                func.lower(FoodItem.nom).like(kalit),
                func.lower(FoodItem.kalit_sozlar).like(kalit),
            )
        )

    rows = (
        await session.execute(shart.order_by(FoodItem.nom).limit(limit))
    ).scalars().all()
    return [FoodItemOut.model_validate(f) for f in rows]


# --------------------------------------------------------------------------- #
# Mashqlar
# --------------------------------------------------------------------------- #
@app.get("/api/exercises", response_model=list[ExerciseOut])
async def exercises_list(
    daraja: str | None = Query(default=None),
    turkum: str | None = Query(default=None),
    _: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> list[ExerciseOut]:
    shart = select(Exercise).where(Exercise.faol.is_(True))
    if daraja:
        shart = shart.where(Exercise.daraja == daraja)
    if turkum:
        shart = shart.where(Exercise.turkum == turkum)

    rows = (
        await session.execute(shart.order_by(Exercise.tartib, Exercise.id))
    ).scalars().all()
    return [ExerciseOut.model_validate(e) for e in rows]


@app.post("/api/exercise-logs", response_model=ExerciseLogOut)
async def exercise_log_create(
    payload: ExerciseLogIn,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> ExerciseLogOut:
    nom = payload.nom
    kaloriya = payload.kaloriya
    davomiylik = payload.davomiylik_sek

    # Mashq bazadan tanlangan bo'lsa, qiymatlarni undan olamiz —
    # mijozdan kelgan raqamlarga ishonmaymiz.
    if payload.exercise_id:
        ex = await session.get(Exercise, payload.exercise_id)
        if ex is not None:
            nom = ex.nom
            kaloriya = ex.kaloriya
            davomiylik = ex.davomiylik_sek

    log = ExerciseLog(
        user_id=user.id,
        exercise_id=payload.exercise_id,
        nom=nom or "Mashq",
        davomiylik_sek=davomiylik,
        kaloriya=kaloriya,
        sana=payload.sana or timeutil.bugun(),
    )
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return ExerciseLogOut.model_validate(log)


@app.get("/api/exercise-logs", response_model=list[ExerciseLogOut])
async def exercise_logs_list(
    sana: date_type | None = None,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> list[ExerciseLogOut]:
    kun = sana or timeutil.bugun()
    rows = (
        await session.execute(
            select(ExerciseLog)
            .where(ExerciseLog.user_id == user.id, ExerciseLog.sana == kun)
            .order_by(ExerciseLog.created_at.desc())
        )
    ).scalars().all()
    return [ExerciseLogOut.model_validate(x) for x in rows]


# --------------------------------------------------------------------------- #
# Eslatmalar
# --------------------------------------------------------------------------- #
@app.get("/api/reminders", response_model=list[ReminderOut])
async def reminders_list(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> list[ReminderOut]:
    rows = (
        await session.execute(
            select(Reminder)
            .where(Reminder.user_id == user.id)
            .order_by(Reminder.soat, Reminder.daqiqa)
        )
    ).scalars().all()
    return [ReminderOut.model_validate(r) for r in rows]


@app.post("/api/reminders", response_model=ReminderOut)
async def reminder_create(
    payload: ReminderIn,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> ReminderOut:
    r = Reminder(user_id=user.id, **payload.model_dump())
    session.add(r)
    await session.commit()
    await session.refresh(r)
    return ReminderOut.model_validate(r)


@app.patch("/api/reminders/{reminder_id}", response_model=ReminderOut)
async def reminder_update(
    reminder_id: int,
    payload: ReminderIn,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> ReminderOut:
    r = await session.scalar(
        select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == user.id)
    )
    if r is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Eslatma topilmadi")

    for maydon, qiymat in payload.model_dump().items():
        setattr(r, maydon, qiymat)
    await session.commit()
    await session.refresh(r)
    return ReminderOut.model_validate(r)


@app.delete(
    "/api/reminders/{reminder_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def reminder_delete(
    reminder_id: int,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    r = await session.scalar(
        select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == user.id)
    )
    if r is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Eslatma topilmadi")
    await session.delete(r)
    await session.commit()


# --------------------------------------------------------------------------- #
# Admin: mashq va ovqat bazasi
# --------------------------------------------------------------------------- #
@app.get("/api/admin/exercises", response_model=list[ExerciseOut])
async def admin_exercises(
    _: User = Depends(admin.current_admin),
    session: AsyncSession = Depends(get_session),
) -> list[ExerciseOut]:
    rows = (
        await session.execute(select(Exercise).order_by(Exercise.tartib, Exercise.id))
    ).scalars().all()
    return [ExerciseOut.model_validate(e) for e in rows]


@app.post("/api/admin/exercises", response_model=ExerciseOut)
async def admin_exercise_create(
    payload: ExerciseIn,
    _: User = Depends(admin.current_admin),
    session: AsyncSession = Depends(get_session),
) -> ExerciseOut:
    e = Exercise(**payload.model_dump())
    session.add(e)
    await session.commit()
    await session.refresh(e)
    return ExerciseOut.model_validate(e)


@app.patch("/api/admin/exercises/{exercise_id}", response_model=ExerciseOut)
async def admin_exercise_update(
    exercise_id: int,
    payload: ExerciseIn,
    _: User = Depends(admin.current_admin),
    session: AsyncSession = Depends(get_session),
) -> ExerciseOut:
    e = await session.get(Exercise, exercise_id)
    if e is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Mashq topilmadi")
    for maydon, qiymat in payload.model_dump().items():
        setattr(e, maydon, qiymat)
    await session.commit()
    await session.refresh(e)
    return ExerciseOut.model_validate(e)


@app.delete(
    "/api/admin/exercises/{exercise_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def admin_exercise_delete(
    exercise_id: int,
    _: User = Depends(admin.current_admin),
    session: AsyncSession = Depends(get_session),
) -> None:
    e = await session.get(Exercise, exercise_id)
    if e is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Mashq topilmadi")
    await session.delete(e)
    await session.commit()


@app.post("/api/admin/foods", response_model=FoodItemOut)
async def admin_food_create(
    payload: FoodItemIn,
    _: User = Depends(admin.current_admin),
    session: AsyncSession = Depends(get_session),
) -> FoodItemOut:
    f = FoodItem(**payload.model_dump())
    session.add(f)
    await session.commit()
    await session.refresh(f)
    return FoodItemOut.model_validate(f)


@app.patch("/api/admin/foods/{food_id}", response_model=FoodItemOut)
async def admin_food_update(
    food_id: int,
    payload: FoodItemIn,
    _: User = Depends(admin.current_admin),
    session: AsyncSession = Depends(get_session),
) -> FoodItemOut:
    f = await session.get(FoodItem, food_id)
    if f is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ovqat topilmadi")
    for maydon, qiymat in payload.model_dump().items():
        setattr(f, maydon, qiymat)
    await session.commit()
    await session.refresh(f)
    return FoodItemOut.model_validate(f)
