"""SQLAlchemy modellari."""

from datetime import date as date_type
from datetime import datetime, time, timezone

from sqlalchemy import (
    Boolean,
    BigInteger,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)

    ism: Mapped[str | None] = mapped_column(String(128), default=None)
    username: Mapped[str | None] = mapped_column(String(64), default=None)
    telefon: Mapped[str | None] = mapped_column(String(32), default=None)

    yosh: Mapped[int | None] = mapped_column(Integer, default=None)
    jins: Mapped[str | None] = mapped_column(String(8), default=None)  # erkak | ayol
    boy_sm: Mapped[float | None] = mapped_column(Float, default=None)
    joriy_vazn_kg: Mapped[float | None] = mapped_column(Float, default=None)
    istalgan_vazn_kg: Mapped[float | None] = mapped_column(Float, default=None)

    # sedentary | light | moderate | high | athlete
    faollik_darajasi: Mapped[str] = mapped_column(String(16), default="light")
    # yoqotish | saqlash | oshirish
    maqsad_turi: Mapped[str] = mapped_column(String(16), default="saqlash")

    kunlik_kaloriya_limit: Mapped[int] = mapped_column(Integer, default=2000)
    kunlik_protein_limit: Mapped[int] = mapped_column(Integer, default=150)
    kunlik_yog_limit: Mapped[int] = mapped_column(Integer, default=67)
    kunlik_uglevod_limit: Mapped[int] = mapped_column(Integer, default=200)
    kunlik_suv_limit_ml: Mapped[int] = mapped_column(Integer, default=2000)

    # Foydalanuvchi limitlarni qo'lda kiritgan bo'lsa, avtomatik qayta hisoblanmaydi.
    limit_qolda: Mapped[bool] = mapped_column(Integer, default=0)

    eslatmalar_yoqilgan: Mapped[bool] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # --- Admin boshqaruvi ---
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # Premium: kunlik AI chegaralari kengayadi. Muddat tugasa oddiy holatga
    # qaytadi — alohida ish talab qilmaydi, tekshiruv o'qish paytida bo'ladi.
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_tugash: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    # Premium AI tekshiruvidan o'tib berilgan, lekin admin hali tasdiqlamagan.
    premium_tasdiq_kutilmoqda: Mapped[bool] = mapped_column(Boolean, default=False)

    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    block_sabab: Mapped[str | None] = mapped_column(String(256), default=None)

    oxirgi_faollik: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, index=True
    )

    meals: Mapped[list["Meal"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def premium_faolmi(self) -> bool:
        """Premium hozir kuchdami. Muddat o'tgan bo'lsa False.

        SQLite vaqtni zonasiz saqlaydi, shuning uchun bazadan o'qilgan qiymat
        naive bo'lib chiqadi. Aware bilan solishtirsak TypeError bo'ladi —
        ikkalasini ham UTC aware ko'rinishga keltiramiz.
        """
        if not self.is_premium:
            return False
        if self.premium_tugash is None:
            return True  # muddatsiz premium

        tugash = self.premium_tugash
        if tugash.tzinfo is None:
            tugash = tugash.replace(tzinfo=timezone.utc)
        return tugash > utcnow()

    @property
    def profil_toliq(self) -> bool:
        return all(
            v is not None
            for v in (self.yosh, self.jins, self.boy_sm, self.joriy_vazn_kg)
        )


class Meal(Base):
    __tablename__ = "meals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    rasm_yoli: Mapped[str | None] = mapped_column(String(256), default=None)
    taom_nomi: Mapped[str] = mapped_column(String(160))
    ulush: Mapped[str | None] = mapped_column(String(80), default=None)

    kaloriya: Mapped[int] = mapped_column(Integer, default=0)
    protein_g: Mapped[float] = mapped_column(Float, default=0)
    yog_g: Mapped[float] = mapped_column(Float, default=0)
    uglevod_g: Mapped[float] = mapped_column(Float, default=0)

    manba: Mapped[str] = mapped_column(String(16), default="ai")  # ai | qolda | favorite
    sana: Mapped[date_type] = mapped_column(Date, index=True)
    vaqt: Mapped[time] = mapped_column(Time)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship(back_populates="meals")


class WeightLog(Base):
    __tablename__ = "weight_log"
    __table_args__ = (UniqueConstraint("user_id", "sana", name="uq_weight_user_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    vazn_kg: Mapped[float] = mapped_column(Float)
    sana: Mapped[date_type] = mapped_column(Date, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WaterLog(Base):
    __tablename__ = "water_log"
    __table_args__ = (UniqueConstraint("user_id", "sana", name="uq_water_user_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    miqdor_ml: Mapped[int] = mapped_column(Integer, default=0)
    sana: Mapped[date_type] = mapped_column(Date, index=True)


class Favorite(Base):
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    taom_nomi: Mapped[str] = mapped_column(String(160))
    ulush: Mapped[str | None] = mapped_column(String(80), default=None)
    kaloriya: Mapped[int] = mapped_column(Integer, default=0)
    protein_g: Mapped[float] = mapped_column(Float, default=0)
    yog_g: Mapped[float] = mapped_column(Float, default=0)
    uglevod_g: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ChatMessage(Base):
    """Murabbiy bilan suhbat — foydalanuvchi va AI xabarlari."""

    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    rol: Mapped[str] = mapped_column(String(16))  # user | murabbiy
    matn: Mapped[str] = mapped_column(String(4000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )


class AiUsage(Base):
    """Kunlik AI chaqiruvlari hisobi — xarajatni cheklash uchun.

    Har chaqiruv pul turadi, shuning uchun foydalanuvchi kuniga qancha
    ishlatganini sanab boramiz. Tur bo'yicha alohida: 'tahlil' (rasm/matn)
    va 'chat' (murabbiy).
    """

    __tablename__ = "ai_usage"
    __table_args__ = (
        UniqueConstraint("user_id", "sana", "tur", name="uq_usage_user_date_kind"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    sana: Mapped[date_type] = mapped_column(Date, index=True)
    tur: Mapped[str] = mapped_column(String(16))  # tahlil | chat
    soni: Mapped[int] = mapped_column(Integer, default=0)


class Tarif(Base):
    """Premium tariflari — admin paneldan boshqariladi."""

    __tablename__ = "tariflar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(String(64))
    kun: Mapped[int] = mapped_column(Integer)
    narx: Mapped[int] = mapped_column(Integer)  # so'mda, butun son
    tavsif: Mapped[str | None] = mapped_column(String(200), default=None)
    faol: Mapped[bool] = mapped_column(Boolean, default=True)
    tartib: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TolovSozlama(Base):
    """To'lov rekvizitlari. Jadvalda faqat bitta qator bo'ladi (id=1)."""

    __tablename__ = "tolov_sozlama"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    karta_raqam: Mapped[str] = mapped_column(String(32), default="")
    karta_egasi: Mapped[str] = mapped_column(String(128), default="")
    izoh: Mapped[str | None] = mapped_column(String(300), default=None)

    # Chek sanasi shuncha kundan eski bo'lsa qabul qilinmaydi.
    chek_amal_kuni: Mapped[int] = mapped_column(Integer, default=3)

    # Yordam tugmasi shu Telegram profiliga olib boradi (@ siz yoziladi).
    yordam_username: Mapped[str] = mapped_column(String(64), default="")

    # Premium oynasidagi matn — admin paneldan tahrirlanadi.
    premium_sarlavha: Mapped[str] = mapped_column(
        String(120), default="Premium bilan ko'proq imkoniyat"
    )
    # Har qator — bitta afzallik. Ro'yxat sifatida ko'rsatiladi.
    premium_afzalliklar: Mapped[str] = mapped_column(
        Text,
        default=(
            "Ovqat rasmidan cheksiz kaloriya tahlili\n"
            "AI murabbiy bilan kengaytirilgan suhbat\n"
            "Kunlik chegaralar sezilarli kengayadi\n"
            "Yangi funksiyalarga birinchi bo'lib kirish"
        ),
    )


class Payment(Base):
    """Premium uchun to'lov arizasi.

    Oqim: foydalanuvchi chek rasmini yuboradi -> AI rasmdagi matnni o'qiydi ->
    avtomatik solishtiruv. Mos kelsa premium DARHOL beriladi, lekin ariza
    "kutilmoqda" holatida qoladi va admin qayta ko'rib chiqadi.

    Avtomatik tekshiruv haqiqiy isbot emas: chekni yasash yoki birovnikini
    qayta yuborish mumkin. Shuning uchun admin qarori oxirgi so'z.
    """

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    tarif_id: Mapped[int | None] = mapped_column(
        ForeignKey("tariflar.id", ondelete="SET NULL"), default=None
    )

    tarif_nom: Mapped[str] = mapped_column(String(64), default="")
    tarif_kun: Mapped[int] = mapped_column(Integer, default=0)
    kutilgan_summa: Mapped[int] = mapped_column(Integer, default=0)

    chek_yoli: Mapped[str | None] = mapped_column(String(256), default=None)
    # Bir xil rasmni qayta yuborishni aniqlash uchun.
    chek_hash: Mapped[str | None] = mapped_column(String(64), index=True, default=None)

    # AI rasmdan o'qigan hamma matn — admin ko'rishi uchun saqlanadi.
    ai_matn: Mapped[str | None] = mapped_column(Text, default=None)
    aniqlangan_karta: Mapped[str | None] = mapped_column(String(32), default=None)
    aniqlangan_summa: Mapped[int | None] = mapped_column(Integer, default=None)
    aniqlangan_sana: Mapped[str | None] = mapped_column(String(32), default=None)
    tranzaksiya_id: Mapped[str | None] = mapped_column(String(64), index=True, default=None)

    # kutilmoqda | tasdiqlangan | rad_etilgan
    holat: Mapped[str] = mapped_column(String(16), default="kutilmoqda", index=True)
    # AI tekshiruvidan o'tdimi (premium darhol berildimi)
    avto_otdi: Mapped[bool] = mapped_column(Boolean, default=False)
    tekshiruv_izoh: Mapped[str | None] = mapped_column(String(500), default=None)

    admin_izoh: Mapped[str | None] = mapped_column(String(300), default=None)
    admin_id: Mapped[int | None] = mapped_column(Integer, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
    korilgan_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )


class Exercise(Base):
    """Mashq — admin paneldan boshqariladi.

    Video ilova ichida saqlanmaydi: faqat havola turadi. Sabab — ilova
    hajmi kichik qolishi kerak va videolar keyinchalik boshqa saqlashga
    ko'chirilishi mumkin (havola o'zgaradi, kod o'zgarmaydi).
    """

    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(String(120))
    tavsif: Mapped[str | None] = mapped_column(Text, default=None)

    # boshlangich | orta | yuqori
    daraja: Mapped[str] = mapped_column(String(16), default="boshlangich")
    # kuch | cho'zilish | harakatchanlik | umumiy
    turkum: Mapped[str] = mapped_column(String(24), default="umumiy")

    davomiylik_sek: Mapped[int] = mapped_column(Integer, default=60)
    takror: Mapped[str | None] = mapped_column(String(64), default=None)
    kaloriya: Mapped[int] = mapped_column(Integer, default=0)

    video_url: Mapped[str | None] = mapped_column(String(500), default=None)
    rasm_url: Mapped[str | None] = mapped_column(String(500), default=None)

    faol: Mapped[bool] = mapped_column(Boolean, default=True)
    tartib: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ExerciseLog(Base):
    """Bajarilgan mashq."""

    __tablename__ = "exercise_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    exercise_id: Mapped[int | None] = mapped_column(
        ForeignKey("exercises.id", ondelete="SET NULL"), default=None
    )
    nom: Mapped[str] = mapped_column(String(120), default="")
    davomiylik_sek: Mapped[int] = mapped_column(Integer, default=0)
    kaloriya: Mapped[int] = mapped_column(Integer, default=0)
    sana: Mapped[date_type] = mapped_column(Date, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class FoodItem(Base):
    """Mahalliy ovqat bazasi.

    Nima uchun kerak: har "osh" uchun AI chaqirish pul turadi va sekin.
    Ko'p ishlatiladigan taomlar bazada tursa, qidiruv bir zumda ishlaydi
    va AI faqat notanish taomlar uchun chaqiriladi.
    """

    __tablename__ = "food_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(String(120), index=True)
    # Qidiruv uchun: "osh palov plov" kabi muqobil nomlar
    kalit_sozlar: Mapped[str] = mapped_column(String(300), default="")

    ulush: Mapped[str] = mapped_column(String(64), default="100 g")
    ulush_gramm: Mapped[int] = mapped_column(Integer, default=100)

    kaloriya: Mapped[int] = mapped_column(Integer, default=0)
    protein_g: Mapped[float] = mapped_column(Float, default=0)
    yog_g: Mapped[float] = mapped_column(Float, default=0)
    uglevod_g: Mapped[float] = mapped_column(Float, default=0)

    turkum: Mapped[str] = mapped_column(String(32), default="umumiy")
    faol: Mapped[bool] = mapped_column(Boolean, default=True)


class Reminder(Base):
    """Foydalanuvchi eslatmalari — bot orqali yuboriladi."""

    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # ovqat | suv | harakat | uyqu
    tur: Mapped[str] = mapped_column(String(16))
    matn: Mapped[str] = mapped_column(String(200), default="")
    soat: Mapped[int] = mapped_column(Integer, default=9)
    daqiqa: Mapped[int] = mapped_column(Integer, default=0)
    yoqilgan: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
