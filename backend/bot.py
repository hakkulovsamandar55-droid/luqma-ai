"""aiogram bot: /start, Mini App tugmasi, ovqatlanish eslatmalari."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    MenuButtonWebApp,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from sqlalchemy import select

from config import settings
from db import SessionLocal, init_db
from models import Meal, User

log = logging.getLogger(__name__)

dp = Dispatcher()

WELCOME = (
    "🥗 <b>Luqma AI</b> ga xush kelibsiz!\n\n"
    "Men sizning shaxsiy kaloriya hisoblovchingizman. Ovqatingizni suratga oling — "
    "men uni tanib, kaloriya va BJU (oqsil / yog' / uglevod) miqdorini hisoblab beraman.\n\n"
    "Boshlash uchun pastdagi tugmani bosing 👇"
)

HELP = (
    "<b>Luqma AI qanday ishlaydi?</b>\n\n"
    "1️⃣ Ilovani oching va profilingizni to'ldiring (yosh, bo'y, vazn, maqsad)\n"
    "2️⃣ Sizga shaxsiy kunlik kaloriya limiti hisoblanadi\n"
    "3️⃣ Har ovqatdan oldin uni suratga oling yoki qo'lda kiriting\n"
    "4️⃣ Kun davomida qolgan kaloriyangizni kuzatib boring\n\n"
    "<b>Buyruqlar:</b>\n"
    "/start — ilovani ochish\n"
    "/bugun — bugungi natijangiz\n"
    "/eslatma — eslatmalarni yoqish/o'chirish\n"
    "/yordam — shu xabar"
)

ESLATMALAR: list[tuple[int, int, str]] = [
    (9, 0, "🌅 Xayrli tong! Nonushtangizni suratga olishni unutmang."),
    (13, 30, "🍽 Tushlik vaqti! Ovqatingizni Luqma AI ga qo'shing."),
    (19, 30, "🌙 Kechki ovqat vaqti. Bugungi limitingizni tekshiring."),
    (22, 0, "📊 Kun yakuni — bugungi natijangizni ilovada ko'ring."),
]


def _webapp_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🥗 Luqma AI ni ochish",
                    web_app=WebAppInfo(url=settings.webapp_url),
                )
            ]
        ]
    )


def _reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🥗 Ilovani ochish", web_app=WebAppInfo(url=settings.webapp_url))]
        ],
        resize_keyboard=True,
    )


async def _foydalanuvchini_royxatga_ol(message: Message) -> User:
    async with SessionLocal() as session:
        user = await session.scalar(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        if user is None:
            user = User(
                telegram_id=message.from_user.id,
                ism=message.from_user.full_name,
                username=message.from_user.username,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await _foydalanuvchini_royxatga_ol(message)
    await message.answer(WELCOME, reply_markup=_webapp_keyboard())
    await message.answer("Tugma pastda ham doim mavjud 👇", reply_markup=_reply_keyboard())


@dp.message(Command("yordam", "help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP, reply_markup=_webapp_keyboard())


@dp.message(Command("bugun"))
async def cmd_bugun(message: Message) -> None:
    from sqlalchemy import func

    bugun = datetime.now().date()
    async with SessionLocal() as session:
        user = await session.scalar(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        if user is None:
            await message.answer("Avval /start ni bosing.")
            return

        kcal, protein, yog, uglevod, soni = (
            await session.execute(
                select(
                    func.coalesce(func.sum(Meal.kaloriya), 0),
                    func.coalesce(func.sum(Meal.protein_g), 0.0),
                    func.coalesce(func.sum(Meal.yog_g), 0.0),
                    func.coalesce(func.sum(Meal.uglevod_g), 0.0),
                    func.count(Meal.id),
                ).where(Meal.user_id == user.id, Meal.sana == bugun)
            )
        ).one()

    qolgan = user.kunlik_kaloriya_limit - int(kcal)
    holat = "✅ Limit ichidasiz" if qolgan >= 0 else "⚠️ Limitdan oshdingiz"
    await message.answer(
        f"📊 <b>Bugungi natija</b>\n\n"
        f"🔥 Kaloriya: <b>{int(kcal)}</b> / {user.kunlik_kaloriya_limit} kcal\n"
        f"💪 Oqsil: {protein:.0f}g  •  🥑 Yog': {yog:.0f}g  •  🌾 Uglevod: {uglevod:.0f}g\n"
        f"🍽 Ovqatlar: {soni} ta\n\n"
        f"{holat} — qolgan: <b>{qolgan}</b> kcal",
        reply_markup=_webapp_keyboard(),
    )


@dp.message(Command("eslatma"))
async def cmd_eslatma(message: Message) -> None:
    async with SessionLocal() as session:
        user = await session.scalar(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        if user is None:
            await message.answer("Avval /start ni bosing.")
            return
        user.eslatmalar_yoqilgan = not user.eslatmalar_yoqilgan
        holat = user.eslatmalar_yoqilgan
        await session.commit()

    await message.answer(
        "🔔 Eslatmalar yoqildi." if holat else "🔕 Eslatmalar o'chirildi."
    )


@dp.message(F.photo)
async def photo_handler(message: Message) -> None:
    """Botga to'g'ridan-to'g'ri rasm yuborilsa — Mini App ga yo'naltiramiz."""
    await message.answer(
        "📸 Rasm tahlili Mini App ichida ishlaydi — u yerda natijani tahrirlash "
        "va saqlash imkoni bor. Tugmani bosing 👇",
        reply_markup=_webapp_keyboard(),
    )


async def eslatmalar_sikli(bot: Bot) -> None:
    """Har daqiqada tekshirib, belgilangan vaqtlarda eslatma yuboradi."""
    yuborilgan: set[tuple[str, int, int]] = set()

    while True:
        try:
            now = datetime.now()
            kalit_kun = now.strftime("%Y-%m-%d")

            for soat, daqiqa, matn in ESLATMALAR:
                kalit = (kalit_kun, soat, daqiqa)
                if now.hour == soat and now.minute == daqiqa and kalit not in yuborilgan:
                    yuborilgan.add(kalit)
                    await _eslatma_yubor(bot, matn)

            # Eskirgan kalitlarni tozalaymiz.
            kecha = (now - timedelta(days=1)).strftime("%Y-%m-%d")
            yuborilgan = {k for k in yuborilgan if k[0] >= kecha}
        except Exception:  # noqa: BLE001 - sikl to'xtamasligi kerak
            log.exception("Eslatma siklida xato")

        await asyncio.sleep(60)


async def _eslatma_yubor(bot: Bot, matn: str) -> None:
    async with SessionLocal() as session:
        rows = await session.execute(
            select(User.telegram_id).where(User.eslatmalar_yoqilgan == True)  # noqa: E712
        )
        ids = [r[0] for r in rows]

    for tg_id in ids:
        try:
            await bot.send_message(tg_id, matn, reply_markup=_webapp_keyboard())
        except Exception as exc:  # noqa: BLE001 - bloklangan foydalanuvchilar
            log.warning("Eslatma yuborilmadi (%s): %s", tg_id, exc)
        await asyncio.sleep(0.05)  # Telegram rate-limit


async def run_bot() -> None:
    if not settings.bot_token:
        log.warning("BOT_TOKEN yo'q — bot ishga tushmaydi")
        return

    await init_db()
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Luqma AI", web_app=WebAppInfo(url=settings.webapp_url)
            )
        )
    except Exception:  # noqa: BLE001
        log.exception("Menu tugmasini o'rnatib bo'lmadi")

    asyncio.create_task(eslatmalar_sikli(bot))
    log.info("Bot polling boshlandi")
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    asyncio.run(run_bot())
