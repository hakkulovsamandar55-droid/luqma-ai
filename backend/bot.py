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

import cleanup
import logging_setup
import timeutil
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

    bugun = timeutil.bugun()
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


ESLATMA_MATNI = {
    "ovqat": "Ovqatlanish vaqti — nima yeganingizni qo'shib qo'ying.",
    "suv": "Suv ichishni unutmang.",
    "harakat": "Biroz harakatlaning — qisqa mashq ham foyda beradi.",
    "uyqu": "Uxlash vaqti yaqinlashdi. Kunni yakunlang.",
}


async def _shaxsiy_eslatmalar(bot: Bot, now) -> None:
    """Foydalanuvchi o'zi sozlagan eslatmalarni yuboradi.

    Umumiy eslatmalardan farqi: har kimning o'z vaqti bor va u ilovada
    sozlanadi. Eslatmalar serverda ishlaydi, shuning uchun foydalanuvchi
    ilovani ochmasa ham keladi.
    """
    from models import Reminder

    async with SessionLocal() as session:
        rows = (
            await session.execute(
                select(Reminder, User)
                .join(User, Reminder.user_id == User.id)
                .where(
                    Reminder.yoqilgan.is_(True),
                    Reminder.soat == now.hour,
                    Reminder.daqiqa == now.minute,
                    User.is_blocked.is_(False),
                )
            )
        ).all()

    for r, u in rows:
        matn = r.matn or ESLATMA_MATNI.get(r.tur, "Eslatma")
        try:
            await bot.send_message(u.telegram_id, matn)
        except Exception:  # noqa: BLE001 — bloklagan foydalanuvchi normal holat
            log.debug("Eslatma yetmadi: %s", u.telegram_id)
        await asyncio.sleep(0.05)


async def eslatmalar_sikli(bot: Bot) -> None:
    """Har daqiqada tekshirib, belgilangan vaqtlarda eslatma yuboradi."""
    yuborilgan: set[tuple[str, int, int]] = set()

    while True:
        try:
            now = timeutil.hozir()
            kalit_kun = now.strftime("%Y-%m-%d")

            for soat, daqiqa, matn in ESLATMALAR:
                kalit = (kalit_kun, soat, daqiqa)
                if now.hour == soat and now.minute == daqiqa and kalit not in yuborilgan:
                    yuborilgan.add(kalit)
                    await _eslatma_yubor(bot, matn)

            await _shaxsiy_eslatmalar(bot, now)

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
    asyncio.create_task(cleanup.tozalash_sikli())
    log.info("Bot polling boshlandi")
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging_setup.sozla()
    asyncio.run(run_bot())


# --------------------------------------------------------------------------- #
# Admin buyruqlari
# --------------------------------------------------------------------------- #
def _adminmi(message: Message) -> bool:
    return bool(message.from_user) and message.from_user.id in settings.admin_id_list


@dp.message(Command("stat"))
async def cmd_stat(message: Message) -> None:
    """Qisqa statistika: nechta foydalanuvchi, bugun qancha faol."""
    if not _adminmi(message):
        return  # admin emas — buyruq umuman mavjud emasdek javobsiz qoladi

    from sqlalchemy import func

    bugun = timeutil.bugun()
    hafta = bugun - timedelta(days=7)

    async with SessionLocal() as session:
        jami = await session.scalar(select(func.count(User.id))) or 0
        yangi_hafta = (
            await session.scalar(
                select(func.count(User.id)).where(User.created_at >= hafta)
            )
            or 0
        )
        bugun_faol = (
            await session.scalar(
                select(func.count(func.distinct(Meal.user_id))).where(
                    Meal.sana == bugun
                )
            )
            or 0
        )
        bugun_ovqat = (
            await session.scalar(
                select(func.count(Meal.id)).where(Meal.sana == bugun)
            )
            or 0
        )

    await message.answer(
        f"<b>Statistika</b>\n\n"
        f"Jami foydalanuvchi: {jami}\n"
        f"So'nggi 7 kunda yangi: {yangi_hafta}\n"
        f"Bugun faol: {bugun_faol}\n"
        f"Bugun qo'shilgan ovqat: {bugun_ovqat}"
    )


@dp.message(Command("xabar"))
async def cmd_xabar(message: Message) -> None:
    """Hamma foydalanuvchiga xabar yuboradi: /xabar Salom, yangilik bor!"""
    if not _adminmi(message):
        return

    matn = (message.text or "").partition(" ")[2].strip()
    if not matn:
        await message.answer(
            "Xabar matnini yozing:\n<code>/xabar Salom, yangilik bor!</code>"
        )
        return

    async with SessionLocal() as session:
        idlar = (await session.execute(select(User.telegram_id))).scalars().all()

    await message.answer(f"Yuborilmoqda… ({len(idlar)} ta)")

    yetdi = 0
    yetmadi = 0
    for tid in idlar:
        try:
            await message.bot.send_message(tid, matn)
            yetdi += 1
        except Exception:  # noqa: BLE001 — bloklagan foydalanuvchilar normal holat
            yetmadi += 1
        # Telegram sekundiga ~30 xabarga ruxsat beradi — chegaradan pastda turamiz.
        await asyncio.sleep(0.05)

    await message.answer(f"Tayyor.\nYetdi: {yetdi}\nYetmadi: {yetmadi}")
