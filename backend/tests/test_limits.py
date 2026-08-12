"""Kunlik chegaralar, vaqt zonasi va rasm tozalash testlari."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from db import SessionLocal
from models import User as _User


async def _premium_qil(client):
    """Tahlil endpointlari premium talab qiladi — testda uni yoqamiz."""
    me = (await client.get("/api/user/me")).json()
    async with SessionLocal() as session:
        u = await session.get(_User, me["id"])
        u.is_premium = True
        await session.commit()

import timeutil
from config import settings
from schemas import MealAnalysis

PROFIL = {
    "jins": "erkak",
    "yosh": 30,
    "boy_sm": 175,
    "joriy_vazn_kg": 80,
    "faollik_darajasi": "moderate",
    "maqsad_turi": "saqlash",
}

TAHLIL = MealAnalysis(
    taom_nomi="Osh",
    ulush="1 tovoq",
    kaloriya=600,
    protein_g=25.0,
    yog_g=20.0,
    uglevod_g=70.0,
    ishonch=0.8,
)


async def _profil(client):
    r = await client.put("/api/user/me", json=PROFIL)
    assert r.status_code == 200
    return r.json()


# --------------------------------------------------------------------------- #
# Vaqt zonasi
# --------------------------------------------------------------------------- #
def test_bugun_sozlangan_zonada():
    """bugun() server UTC bo'lsa ham sozlangan zonaga qarab hisoblanadi."""
    b = timeutil.bugun()
    assert isinstance(b, date)
    # Zona farqi bir kundan oshmaydi.
    from datetime import datetime, timezone

    utc = datetime.now(timezone.utc).date()
    assert abs((b - utc).days) <= 1


def test_kun_boshi_yarim_tun():
    boshi = timeutil.kun_boshi()
    assert (boshi.hour, boshi.minute, boshi.second) == (0, 0, 0)
    assert boshi.date() == timeutil.bugun()


def test_notogri_zona_ilovani_yiqitmaydi():
    """Noto'g'ri zona nomi yozilsa UTC ga tushadi, ilova ishlayveradi."""
    import importlib
    from zoneinfo import ZoneInfoNotFoundError

    with patch("timeutil.ZoneInfo", side_effect=ZoneInfoNotFoundError("yo'q")):
        # Import qayta bajarilganda xato ko'tarilmasligi kerak.
        try:
            importlib.reload(timeutil)
        except ZoneInfoNotFoundError:
            pytest.fail("Noto'g'ri zona ilovani yiqitdi")
    importlib.reload(timeutil)


# --------------------------------------------------------------------------- #
# Tahlil chegarasi
# --------------------------------------------------------------------------- #
@pytest.mark.anyio
async def test_matn_tahliliga_kunlik_chegara(client, monkeypatch):
    await _premium_qil(client)
    await _profil(client)
    # Premium foydalanuvchi premium chegarasiga tushadi — ikkalasini ham
    # pasaytiramiz, aks holda test chegarani sinamaydi.
    monkeypatch.setattr(settings, "tahlil_kunlik_limit", 2)
    monkeypatch.setattr(settings, "premium_tahlil_kunlik_limit", 2)

    with patch("vision.matnni_tahlil_qil", new=AsyncMock(return_value=TAHLIL)):
        for _ in range(2):
            r = await client.post("/api/meals/analyze-text", json={"matn": "osh"})
            assert r.status_code == 200
        uchinchi = await client.post("/api/meals/analyze-text", json={"matn": "osh"})

    assert uchinchi.status_code == 429
    assert "chegara" in uchinchi.json()["detail"].lower()


@pytest.mark.anyio
async def test_chegara_tur_boyicha_alohida(client, monkeypatch):
    """Tahlil chegarasi tugasa ham murabbiy bilan gaplashish mumkin."""
    await _premium_qil(client)
    await _profil(client)
    monkeypatch.setattr(settings, "tahlil_kunlik_limit", 1)
    monkeypatch.setattr(settings, "premium_tahlil_kunlik_limit", 1)
    monkeypatch.setattr(settings, "chat_kunlik_limit", 5)
    monkeypatch.setattr(settings, "premium_chat_kunlik_limit", 5)

    with patch("vision.matnni_tahlil_qil", new=AsyncMock(return_value=TAHLIL)):
        await client.post("/api/meals/analyze-text", json={"matn": "osh"})
        tugadi = await client.post("/api/meals/analyze-text", json={"matn": "osh"})
    assert tugadi.status_code == 429

    import chat as coach

    with patch.object(coach, "javob_ol", new=AsyncMock(return_value="ok")):
        r = await client.post("/api/chat", json={"matn": "salom"})
    assert r.status_code == 200


@pytest.mark.anyio
async def test_chegara_foydalanuvchilar_orasida_bolinmaydi(client, monkeypatch):
    """Bir foydalanuvchining chegarasi boshqasiga ta'sir qilmaydi."""
    await _premium_qil(client)
    from db import SessionLocal
    from models import AiUsage, User

    await _profil(client)
    monkeypatch.setattr(settings, "tahlil_kunlik_limit", 1)

    with patch("vision.matnni_tahlil_qil", new=AsyncMock(return_value=TAHLIL)):
        await client.post("/api/meals/analyze-text", json={"matn": "osh"})

    # Ikkinchi foydalanuvchi qo'shamiz va uning hisobini tekshiramiz.
    async with SessionLocal() as session:
        boshqa = User(telegram_id=999_999)
        session.add(boshqa)
        await session.commit()
        await session.refresh(boshqa)

        import limits

        soni = await limits.hisobla(session, boshqa.id, "tahlil")
        assert soni == 0

        # Birinchi foydalanuvchida esa 1 ta yozuv bor.
        yozuvlar = (await session.execute(__import__("sqlalchemy").select(AiUsage))).scalars().all()
        assert len(yozuvlar) == 1
        assert yozuvlar[0].soni == 1


# --------------------------------------------------------------------------- #
# Rasm tozalash
# --------------------------------------------------------------------------- #
@pytest.mark.anyio
async def test_eski_rasm_ochiriladi(client, tmp_path, monkeypatch):
    from db import SessionLocal
    from models import Meal, User

    import cleanup

    monkeypatch.setattr(settings, "media_dir", str(tmp_path))
    monkeypatch.setattr(settings, "rasm_saqlash_kuni", 30)

    fayl = tmp_path / "eski.jpg"
    fayl.write_bytes(b"rasm")

    async with SessionLocal() as session:
        user = User(telegram_id=555_001)
        session.add(user)
        await session.commit()
        await session.refresh(user)

        session.add(
            Meal(
                user_id=user.id,
                taom_nomi="Eski osh",
                kaloriya=500,
                protein_g=20,
                yog_g=15,
                uglevod_g=60,
                rasm_yoli="/media/eski.jpg",
                sana=timeutil.bugun() - timedelta(days=90),
                vaqt=timeutil.hozir().time().replace(microsecond=0),
            )
        )
        await session.commit()

    ochirildi = await cleanup.eski_rasmlarni_ochir()

    assert ochirildi == 1
    assert not fayl.exists()

    # Ovqat yozuvi qoladi — faqat rasm havolasi bo'shaydi.
    async with SessionLocal() as session:
        from sqlalchemy import select

        meal = await session.scalar(select(Meal).where(Meal.taom_nomi == "Eski osh"))
        assert meal is not None
        assert meal.rasm_yoli is None


@pytest.mark.anyio
async def test_yangi_rasm_saqlanadi(client, tmp_path, monkeypatch):
    from db import SessionLocal
    from models import Meal, User

    import cleanup

    monkeypatch.setattr(settings, "media_dir", str(tmp_path))
    monkeypatch.setattr(settings, "rasm_saqlash_kuni", 30)

    fayl = tmp_path / "yangi.jpg"
    fayl.write_bytes(b"rasm")

    async with SessionLocal() as session:
        user = User(telegram_id=555_002)
        session.add(user)
        await session.commit()
        await session.refresh(user)

        session.add(
            Meal(
                user_id=user.id,
                taom_nomi="Yangi osh",
                kaloriya=500,
                protein_g=20,
                yog_g=15,
                uglevod_g=60,
                rasm_yoli="/media/yangi.jpg",
                sana=timeutil.bugun(),
                vaqt=timeutil.hozir().time().replace(microsecond=0),
            )
        )
        await session.commit()

    await cleanup.eski_rasmlarni_ochir()
    assert fayl.exists()


@pytest.mark.anyio
async def test_saqlash_ochirilgan_bolsa_tegilmaydi(client, tmp_path, monkeypatch):
    import cleanup

    monkeypatch.setattr(settings, "media_dir", str(tmp_path))
    monkeypatch.setattr(settings, "rasm_saqlash_kuni", 0)

    fayl = tmp_path / "abadiy.jpg"
    fayl.write_bytes(b"rasm")

    assert await cleanup.eski_rasmlarni_ochir() == 0
    assert fayl.exists()


# --------------------------------------------------------------------------- #
# Admin
# --------------------------------------------------------------------------- #
def test_admin_royxati_parse():
    eski = settings.admin_ids
    try:
        settings.admin_ids = "111, 222 , notogri, 333"
        assert settings.admin_id_list == [111, 222, 333]

        settings.admin_ids = ""
        assert settings.admin_id_list == []
    finally:
        settings.admin_ids = eski
