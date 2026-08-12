"""Admin panel testlari — huquqlar, premium, bloklash."""

from unittest.mock import AsyncMock, patch

import pytest

from config import settings
from db import SessionLocal
from models import User

PROFIL = {
    "jins": "erkak",
    "yosh": 30,
    "boy_sm": 175,
    "joriy_vazn_kg": 80,
    "faollik_darajasi": "moderate",
    "maqsad_turi": "saqlash",
}


async def _boshqa_user(telegram_id: int = 900_001, **kwargs) -> int:
    """Test uchun ikkinchi foydalanuvchi yaratadi."""
    async with SessionLocal() as session:
        u = User(telegram_id=telegram_id, ism="Test", **kwargs)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return u.id


async def _meni_admin_qil(client) -> None:
    """Joriy (dev) foydalanuvchini bazada admin qiladi."""
    me = (await client.get("/api/user/me")).json()
    async with SessionLocal() as session:
        u = await session.get(User, me["id"])
        u.is_admin = True
        await session.commit()


# --------------------------------------------------------------------------- #
# Huquqlar
# --------------------------------------------------------------------------- #
@pytest.mark.anyio
async def test_oddiy_user_admin_panelga_kira_olmaydi(client):
    await client.put("/api/user/me", json=PROFIL)

    for yol in ("/api/admin/stats", "/api/admin/users"):
        r = await client.get(yol)
        # 404 — panel borligini ham bildirmaymiz.
        assert r.status_code == 404, yol


@pytest.mark.anyio
async def test_admin_me_oddiy_userda_false(client):
    r = await client.get("/api/admin/me")
    assert r.status_code == 200
    assert r.json()["admin"] is False


@pytest.mark.anyio
async def test_env_dagi_admin_kira_oladi(client, monkeypatch):
    """ADMIN_IDS dagi odam bazada is_admin bo'lmasa ham admin."""
    me = (await client.get("/api/user/me")).json()
    monkeypatch.setattr(settings, "admin_ids", str(me["telegram_id"]))

    assert (await client.get("/api/admin/me")).json()["admin"] is True
    assert (await client.get("/api/admin/stats")).status_code == 200


@pytest.mark.anyio
async def test_bazadagi_admin_kira_oladi(client):
    await _meni_admin_qil(client)
    assert (await client.get("/api/admin/stats")).status_code == 200


# --------------------------------------------------------------------------- #
# Statistika va ro'yxat
# --------------------------------------------------------------------------- #
@pytest.mark.anyio
async def test_stats_maydonlari(client):
    await _meni_admin_qil(client)
    d = (await client.get("/api/admin/stats")).json()

    for maydon in (
        "jami_foydalanuvchi",
        "faol_bugun",
        "premium_soni",
        "bloklangan_soni",
        "bugun_ai_chaqiruv",
    ):
        assert maydon in d, maydon
    assert d["jami_foydalanuvchi"] >= 1


@pytest.mark.anyio
async def test_qidiruv_ism_boyicha(client):
    await _meni_admin_qil(client)
    await _boshqa_user(900_010)

    d = (await client.get("/api/admin/users?q=Test")).json()
    assert d["jami"] >= 1
    assert any(u["ism"] == "Test" for u in d["foydalanuvchilar"])


@pytest.mark.anyio
async def test_qidiruv_telegram_id_boyicha(client):
    await _meni_admin_qil(client)
    await _boshqa_user(900_011)

    d = (await client.get("/api/admin/users?q=900011")).json()
    assert d["jami"] == 1
    assert d["foydalanuvchilar"][0]["telegram_id"] == 900_011


@pytest.mark.anyio
async def test_filtr_bloklangan(client):
    await _meni_admin_qil(client)
    await _boshqa_user(900_012, is_blocked=True)
    await _boshqa_user(900_013)

    d = (await client.get("/api/admin/users?filtr=bloklangan")).json()
    assert all(u["is_blocked"] for u in d["foydalanuvchilar"])
    assert d["jami"] >= 1


# --------------------------------------------------------------------------- #
# Premium
# --------------------------------------------------------------------------- #
@pytest.mark.anyio
async def test_premium_muddat_bilan_beriladi(client):
    await _meni_admin_qil(client)
    uid = await _boshqa_user(900_020)

    r = await client.patch(
        f"/api/admin/users/{uid}", json={"is_premium": True, "premium_kun": 30}
    )
    assert r.status_code == 200
    assert r.json()["is_premium"] is True
    assert r.json()["premium_faolmi"] is True
    assert r.json()["premium_tugash"] is not None


@pytest.mark.anyio
async def test_premium_muddatsiz(client):
    await _meni_admin_qil(client)
    uid = await _boshqa_user(900_021)

    r = await client.patch(
        f"/api/admin/users/{uid}", json={"is_premium": True, "premium_kun": 0}
    )
    assert r.json()["premium_tugash"] is None
    assert r.json()["premium_faolmi"] is True


@pytest.mark.anyio
async def test_muddati_otgan_premium_faol_emas(client):
    """premium_tugash o'tib ketgan bo'lsa, premium ishlamaydi."""
    from datetime import timedelta

    from models import utcnow

    await _meni_admin_qil(client)
    uid = await _boshqa_user(900_022)

    async with SessionLocal() as session:
        u = await session.get(User, uid)
        u.is_premium = True
        u.premium_tugash = utcnow() - timedelta(days=1)
        await session.commit()
        assert u.premium_faolmi is False


@pytest.mark.anyio
async def test_premium_kengaytirilgan_chegara_oladi(client, monkeypatch):
    """Premium foydalanuvchi oddiy chegaradan ko'p tahlil qila oladi."""
    import limits

    monkeypatch.setattr(settings, "tahlil_kunlik_limit", 2)
    monkeypatch.setattr(settings, "premium_tahlil_kunlik_limit", 50)

    oddiy = User(telegram_id=900_030)
    premium = User(telegram_id=900_031, is_premium=True)

    assert limits.chegara("tahlil", oddiy.premium_faolmi) == 2
    assert limits.chegara("tahlil", premium.premium_faolmi) == 50


# --------------------------------------------------------------------------- #
# Bloklash
# --------------------------------------------------------------------------- #
@pytest.mark.anyio
async def test_bloklash_va_ochish(client):
    await _meni_admin_qil(client)
    uid = await _boshqa_user(900_040)

    r = await client.patch(
        f"/api/admin/users/{uid}",
        json={"is_blocked": True, "block_sabab": "Spam"},
    )
    assert r.json()["is_blocked"] is True
    assert r.json()["block_sabab"] == "Spam"

    r = await client.patch(f"/api/admin/users/{uid}", json={"is_blocked": False})
    assert r.json()["is_blocked"] is False
    # Blok olib tashlanganda sabab ham tozalanadi.
    assert r.json()["block_sabab"] is None


@pytest.mark.anyio
async def test_bloklangan_user_hech_qayerga_kira_olmaydi(client, monkeypatch):
    """Blok auth bosqichida ushlanadi — hamma endpoint himoyalangan."""
    me = (await client.get("/api/user/me")).json()

    async with SessionLocal() as session:
        u = await session.get(User, me["id"])
        u.is_blocked = True
        u.block_sabab = "Qoida buzilgan"
        await session.commit()

    for yol in ("/api/user/me", "/api/meals", "/api/chat/history"):
        r = await client.get(yol)
        assert r.status_code == 403, yol
        assert "Qoida buzilgan" in r.json()["detail"]


# --------------------------------------------------------------------------- #
# Himoya qoidalari
# --------------------------------------------------------------------------- #
@pytest.mark.anyio
async def test_ozini_bloklab_bolmaydi(client):
    await _meni_admin_qil(client)
    me = (await client.get("/api/user/me")).json()

    r = await client.patch(f"/api/admin/users/{me['id']}", json={"is_blocked": True})
    assert r.status_code == 400


@pytest.mark.anyio
async def test_ozini_adminlikdan_chiqarib_bolmaydi(client):
    await _meni_admin_qil(client)
    me = (await client.get("/api/user/me")).json()

    r = await client.patch(f"/api/admin/users/{me['id']}", json={"is_admin": False})
    assert r.status_code == 400


@pytest.mark.anyio
async def test_asosiy_adminni_ozgartirib_bolmaydi(client, monkeypatch):
    """.env dagi adminni panel orqali o'chirib bo'lmaydi."""
    await _meni_admin_qil(client)
    uid = await _boshqa_user(900_050)

    monkeypatch.setattr(settings, "admin_ids", "900050")

    r = await client.patch(f"/api/admin/users/{uid}", json={"is_blocked": True})
    assert r.status_code == 403

    r = await client.patch(f"/api/admin/users/{uid}", json={"is_admin": False})
    assert r.status_code == 403


@pytest.mark.anyio
async def test_yoq_userni_ozgartirish(client):
    await _meni_admin_qil(client)
    r = await client.patch("/api/admin/users/999999", json={"is_premium": True})
    assert r.status_code == 404


@pytest.mark.anyio
async def test_admin_tayinlash(client):
    await _meni_admin_qil(client)
    uid = await _boshqa_user(900_060)

    r = await client.patch(f"/api/admin/users/{uid}", json={"is_admin": True})
    assert r.status_code == 200
    assert r.json()["is_admin"] is True


# --------------------------------------------------------------------------- #
# Umumiy budjet
# --------------------------------------------------------------------------- #
@pytest.mark.anyio
async def test_umumiy_budjet_tugasa_hamma_uchun_toxtaydi(client, monkeypatch):
    from schemas import MealAnalysis

    tahlil = MealAnalysis(
        taom_nomi="Osh",
        ulush="1 tovoq",
        kaloriya=600,
        protein_g=25.0,
        yog_g=20.0,
        uglevod_g=70.0,
        ishonch=0.8,
    )

    await client.put("/api/user/me", json=PROFIL)
    # Tahlil premium talab qiladi.
    me = (await client.get("/api/user/me")).json()
    async with SessionLocal() as session:
        u = await session.get(User, me["id"])
        u.is_premium = True
        await session.commit()

    monkeypatch.setattr(settings, "umumiy_kunlik_limit", 2)
    monkeypatch.setattr(settings, "tahlil_kunlik_limit", 100)
    monkeypatch.setattr(settings, "premium_tahlil_kunlik_limit", 100)

    with patch("vision.matnni_tahlil_qil", new=AsyncMock(return_value=tahlil)):
        for _ in range(2):
            assert (
                await client.post("/api/meals/analyze-text", json={"matn": "osh"})
            ).status_code == 200

        uchinchi = await client.post("/api/meals/analyze-text", json={"matn": "osh"})

    assert uchinchi.status_code == 503
