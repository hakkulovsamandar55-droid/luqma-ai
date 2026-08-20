"""Murabbiy chat testlari — AI chaqiruvi mocklanadi."""

from unittest.mock import AsyncMock, patch

import pytest

import chat as coach
from vision import VisionError

PROFIL = {
    "jins": "erkak",
    "yosh": 30,
    "boy_sm": 175,
    "joriy_vazn_kg": 80,
    "faollik_darajasi": "moderate",
    "maqsad_turi": "saqlash",
}


async def _profil(client):
    r = await client.put("/api/user/me", json=PROFIL)
    assert r.status_code == 200
    return r.json()


@pytest.mark.anyio
async def test_tarix_boshida_bosh(client):
    await _profil(client)
    r = await client.get("/api/chat/history")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.anyio
async def test_savol_va_javob_saqlanadi(client):
    await _profil(client)

    with patch.object(coach, "javob_ol", new=AsyncMock(return_value="Yaxshi savol.")):
        r = await client.post("/api/chat", json={"matn": "Kechqurun nima yesam?"})

    assert r.status_code == 200
    assert r.json()["rol"] == "murabbiy"
    assert r.json()["matn"] == "Yaxshi savol."

    # Ikkalasi ham tarixda: savol ham, javob ham.
    tarix = (await client.get("/api/chat/history")).json()
    assert [m["rol"] for m in tarix] == ["user", "murabbiy"]
    assert tarix[0]["matn"] == "Kechqurun nima yesam?"


@pytest.mark.anyio
async def test_ai_ishlamasa_tushunarli_xato(client):
    await _profil(client)

    with patch.object(coach, "javob_ol", new=AsyncMock(side_effect=VisionError("x"))):
        r = await client.post("/api/chat", json={"matn": "Salom"})

    assert r.status_code == 503
    # Foydalanuvchiga texnik xato emas, oddiy jumla ko'rsatiladi.
    assert "urinib" in r.json()["detail"]


@pytest.mark.anyio
async def test_bosh_xabar_qabul_qilinmaydi(client):
    await _profil(client)
    r = await client.post("/api/chat", json={"matn": "   "})
    # Faqat probeldan iborat savol AI ga umuman yuborilmaydi.
    assert r.status_code == 422


@pytest.mark.anyio
async def test_juda_uzun_xabar_rad_etiladi(client):
    await _profil(client)
    r = await client.post("/api/chat", json={"matn": "a" * 1001})
    assert r.status_code == 422


@pytest.mark.anyio
async def test_kunlik_limit_ishlaydi(client, monkeypatch):
    await _profil(client)
    from config import settings

    monkeypatch.setattr(settings, "chat_kunlik_limit", 2)

    with patch.object(coach, "javob_ol", new=AsyncMock(return_value="ok")):
        for _ in range(2):
            assert (await client.post("/api/chat", json={"matn": "salom"})).status_code == 200
        uchinchi = await client.post("/api/chat", json={"matn": "salom"})

    assert uchinchi.status_code == 429


@pytest.mark.anyio
async def test_tozalash(client):
    await _profil(client)

    with patch.object(coach, "javob_ol", new=AsyncMock(return_value="ok")):
        await client.post("/api/chat", json={"matn": "salom"})

    assert (await client.delete("/api/chat")).status_code == 204
    assert (await client.get("/api/chat/history")).json() == []


@pytest.mark.anyio
async def test_maslahat_ovqatsiz_kunda(client):
    await _profil(client)
    r = await client.get("/api/chat/tip")
    assert r.status_code == 200
    assert "birinchi ovqat" in r.json()["tavsiya"].lower()


@pytest.mark.anyio
async def test_maslahat_meyordan_oshganda(client):
    user = await _profil(client)

    # Me'yordan ancha ko'p ovqat qo'shamiz.
    await client.post(
        "/api/meals",
        json={
            "taom_nomi": "Katta osh",
            "kaloriya": user["kunlik_kaloriya_limit"] + 500,
            "protein_g": 50,
            "yog_g": 40,
            "uglevod_g": 200,
        },
    )

    tavsiya = (await client.get("/api/chat/tip")).json()["tavsiya"]
    assert "oshdingiz" in tavsiya


@pytest.mark.anyio
async def test_kontekstda_bugungi_ovqat_bor(client):
    """Murabbiyga yuboriladigan kontekst foydalanuvchining raqamlarini o'z ichiga oladi."""
    await _profil(client)
    await client.post(
        "/api/meals",
        json={
            "taom_nomi": "Somsa",
            "kaloriya": 320,
            "protein_g": 12,
            "yog_g": 18,
            "uglevod_g": 30,
        },
    )

    yuborilgan = {}

    async def _tut(session, user, savol):
        yuborilgan["kontekst"] = await coach._kontekst(session, user)
        return "javob"

    with patch.object(coach, "javob_ol", new=_tut):
        await client.post("/api/chat", json={"matn": "Nima yesam?"})

    k = yuborilgan["kontekst"]
    assert "Somsa" in k
    assert "320" in k
    assert "KUNLIK ME'YORI" in k
