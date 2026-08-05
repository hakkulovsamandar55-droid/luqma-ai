"""SQLAlchemy modellari."""

from datetime import date as date_type
from datetime import datetime, time, timezone

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
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

    meals: Mapped[list["Meal"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )

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
