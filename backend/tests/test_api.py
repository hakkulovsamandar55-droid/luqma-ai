"""API endpointlari uchun end-to-end testlar (AI mock qilingan)."""

import io
from datetime import timedelta

import pytest

import timeutil

from db import SessionLocal
from models import User as _User


async def _premium_qil(client):
    """Tahlil endpointlari premium talab qiladi — testda uni yoqamiz."""
    me = (await client.get("/api/user/me")).json()
    async with SessionLocal() as session:
        u = await session.get(_User, me["id"])
        u.is_premium = True
        await session.commit()

import vision
from schemas import MealAnalysis
from tests.test_auth import make_init_data

pytestmark = pytest.mark.asyncio


async def test_health(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_auth_yangi_foydalanuvchi_yaratadi(client):
    r = await client.post("/api/auth", json={"init_data": make_init_data(555)})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["yangi"] is True
    assert body["user"]["telegram_id"] == 555
    assert body["user"]["profil_toliq"] is False

    # Ikkinchi marta — yangi emas
    r2 = await client.post("/api/auth", json={"init_data": make_init_data(555)})
    assert r2.json()["yangi"] is False


async def test_auth_yaroqsiz_initdata_401(client):
    r = await client.post("/api/auth", json={"init_data": "hash=xato&auth_date=1"})
    assert r.status_code == 401


async def test_profil_yangilanganda_limitlar_qayta_hisoblanadi(client):
    r = await client.put(
        "/api/user/me",
        json={
            "yosh": 30, "jins": "erkak", "boy_sm": 180,
            "joriy_vazn_kg": 80, "istalgan_vazn_kg": 75,
            "faollik_darajasi": "moderate", "maqsad_turi": "yoqotish",
        },
    )
    assert r.status_code == 200, r.text
    user = r.json()
    assert user["profil_toliq"] is True
    assert 1500 < user["kunlik_kaloriya_limit"] < 2500
    assert user["kunlik_protein_limit"] > 0
    assert user["limit_qolda"] is False


async def test_qolda_kiritilgan_limit_saqlanadi(client):
    await client.put("/api/user/me", json={"yosh": 30, "jins": "erkak", "boy_sm": 180, "joriy_vazn_kg": 80})
    r = await client.put("/api/user/me", json={"kunlik_kaloriya_limit": 1234})
    assert r.json()["kunlik_kaloriya_limit"] == 1234
    assert r.json()["limit_qolda"] is True

    # Profil o'zgarsa ham qo'lda kiritilgan limit o'zgarmaydi
    r2 = await client.put("/api/user/me", json={"joriy_vazn_kg": 95})
    assert r2.json()["kunlik_kaloriya_limit"] == 1234

    # Reset -> formula bo'yicha qayta hisoblanadi
    r3 = await client.post("/api/user/limits/reset")
    assert r3.json()["limit_qolda"] is False
    assert r3.json()["kunlik_kaloriya_limit"] != 1234


async def test_notogri_qiymat_422(client):
    r = await client.put("/api/user/me", json={"yosh": 500})
    assert r.status_code == 422


async def test_ovqat_saqlash_va_royxat(client):
    bugun = timeutil.bugun().isoformat()
    r = await client.post(
        "/api/meals",
        json={
            "taom_nomi": "Osh", "ulush": "1 tovoq", "kaloriya": 650,
            "protein_g": 22.5, "yog_g": 28, "uglevod_g": 70, "manba": "ai",
        },
    )
    assert r.status_code == 201, r.text
    meal_id = r.json()["id"]
    assert r.json()["taom_nomi"] == "Osh"

    lst = await client.get(f"/api/meals?date={bugun}")
    assert len(lst.json()) == 1

    # Boshqa kunda bo'sh
    ertaga = (timeutil.bugun() + timedelta(days=1)).isoformat()
    assert (await client.get(f"/api/meals?date={ertaga}")).json() == []

    upd = await client.put(
        f"/api/meals/{meal_id}",
        json={"taom_nomi": "Osh (katta)", "kaloriya": 900, "protein_g": 30, "yog_g": 35, "uglevod_g": 95},
    )
    assert upd.json()["kaloriya"] == 900

    assert (await client.delete(f"/api/meals/{meal_id}")).status_code == 204
    assert (await client.get(f"/api/meals?date={bugun}")).json() == []


async def test_boshqaning_ovqatini_ochirib_bolmaydi(client):
    r = await client.post(
        "/api/meals",
        json={"taom_nomi": "Somsa", "kaloriya": 300, "protein_g": 10, "yog_g": 15, "uglevod_g": 30},
    )
    meal_id = r.json()["id"]

    boshqa = {"Authorization": f"tma {make_init_data(999)}"}
    assert (await client.delete(f"/api/meals/{meal_id}", headers=boshqa)).status_code == 404
    assert (await client.get("/api/meals", headers=boshqa)).json() == []


async def test_kunlik_summary(client):
    await client.put(
        "/api/user/me",
        json={"yosh": 30, "jins": "erkak", "boy_sm": 180, "joriy_vazn_kg": 80,
              "faollik_darajasi": "moderate", "maqsad_turi": "saqlash"},
    )
    limit = (await client.get("/api/user/me")).json()["kunlik_kaloriya_limit"]

    for nomi, kcal in [("Nonushta", 400), ("Tushlik", 700)]:
        await client.post(
            "/api/meals",
            json={"taom_nomi": nomi, "kaloriya": kcal, "protein_g": 20, "yog_g": 10, "uglevod_g": 50},
        )

    s = (await client.get("/api/stats/summary")).json()
    assert s["kaloriya"]["istemol"] == 1100
    assert s["kaloriya"]["qolgan"] == limit - 1100
    assert s["protein"]["istemol"] == 40
    assert s["ovqatlar_soni"] == 2
    assert s["streak"] == 1


async def test_haftalik_statistika(client):
    bugun = timeutil.bugun()
    for i, kcal in enumerate([500, 800, 1200]):
        await client.post(
            "/api/meals",
            json={"taom_nomi": f"Kun {i}", "kaloriya": kcal, "protein_g": 10,
                  "yog_g": 5, "uglevod_g": 40, "sana": (bugun - timedelta(days=i)).isoformat()},
        )

    w = (await client.get("/api/stats/weekly")).json()
    assert len(w["kunlar"]) == 7
    assert w["kunlar"][-1]["sana"] == bugun.isoformat()
    assert w["kunlar"][-1]["kaloriya"] == 500
    assert w["ortacha_kaloriya"] == (500 + 800 + 1200) // 3


async def test_streak_uzilganda_qayta_boshlanadi(client):
    bugun = timeutil.bugun()
    for kun in (0, 1, 4):  # 2 va 3-kunlar tashlab ketilgan
        await client.post(
            "/api/meals",
            json={"taom_nomi": "Ovqat", "kaloriya": 300, "protein_g": 10, "yog_g": 5,
                  "uglevod_g": 30, "sana": (bugun - timedelta(days=kun)).isoformat()},
        )
    assert (await client.get("/api/stats/summary")).json()["streak"] == 2


async def test_suv_hisoblagichi(client):
    assert (await client.post("/api/water", json={"miqdor_ml": 250})).json()["miqdor_ml"] == 250
    assert (await client.post("/api/water", json={"miqdor_ml": 250})).json()["miqdor_ml"] == 500
    assert (await client.post("/api/water", json={"miqdor_ml": -250})).json()["miqdor_ml"] == 250
    # Manfiyga tushmaydi
    assert (await client.post("/api/water", json={"miqdor_ml": -5000})).json()["miqdor_ml"] == 0


async def test_vazn_tarixi(client):
    bugun = timeutil.bugun()
    await client.post("/api/weight", json={"vazn_kg": 82.5, "sana": (bugun - timedelta(days=2)).isoformat()})
    await client.post("/api/weight", json={"vazn_kg": 81.0})
    # Bir kunda ikkinchi marta — yangilanadi, dublikat yaratmaydi
    await client.post("/api/weight", json={"vazn_kg": 80.5})

    rows = (await client.get("/api/weight")).json()
    assert [r["vazn_kg"] for r in rows] == [82.5, 80.5]
    assert (await client.get("/api/user/me")).json()["joriy_vazn_kg"] == 80.5


async def test_sevimli_taomlar(client):
    r = await client.post(
        "/api/favorites",
        json={"taom_nomi": "Grechka + tovuq", "kaloriya": 450, "protein_g": 40, "yog_g": 10, "uglevod_g": 50},
    )
    assert r.status_code == 201
    fav_id = r.json()["id"]
    assert len((await client.get("/api/favorites")).json()) == 1
    assert (await client.delete(f"/api/favorites/{fav_id}")).status_code == 204
    assert (await client.delete(f"/api/favorites/{fav_id}")).status_code == 404


async def test_rasm_tahlili(client, monkeypatch):
    await _premium_qil(client)
    async def fake(image_bytes, mime="image/jpeg"):
        assert image_bytes  # rasm haqiqatan yetib keldi
        return MealAnalysis(
            taom_nomi="Lag'mon", ulush="1 kosa (~400g)", kaloriya=520,
            protein_g=24.0, yog_g=18.0, uglevod_g=62.0, ishonch=0.8, izoh="Muvozanatli",
        )

    monkeypatch.setattr(vision, "rasmni_tahlil_qil", fake)
    r = await client.post(
        "/api/meals/analyze",
        files={"rasm": ("ovqat.jpg", io.BytesIO(b"\xff\xd8\xff-fake-jpeg"), "image/jpeg")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["taom_nomi"] == "Lag'mon"
    assert body["rasm_yoli"].startswith("/media/")


async def test_rasm_bolmagan_fayl_rad_etiladi(client):
    await _premium_qil(client)
    r = await client.post(
        "/api/meals/analyze",
        files={"rasm": ("virus.exe", io.BytesIO(b"MZ"), "application/octet-stream")},
    )
    assert r.status_code == 415


async def test_ai_xatosi_502_qaytaradi(client, monkeypatch):
    await _premium_qil(client)
    async def fail(*a, **kw):
        raise vision.VisionError("OpenAI javob bermadi")

    monkeypatch.setattr(vision, "rasmni_tahlil_qil", fail)
    r = await client.post(
        "/api/meals/analyze",
        files={"rasm": ("a.jpg", io.BytesIO(b"\xff\xd8\xff"), "image/jpeg")},
    )
    assert r.status_code == 502


async def test_matn_tahlili(client, monkeypatch):
    await _premium_qil(client)
    async def fake(matn):
        assert matn == "150g osh"
        return MealAnalysis(
            taom_nomi="Osh", ulush="150g", kaloriya=280,
            protein_g=9.0, yog_g=12.0, uglevod_g=32.0, ishonch=0.7,
        )

    monkeypatch.setattr(vision, "matnni_tahlil_qil", fake)
    r = await client.post("/api/meals/analyze-text", json={"matn": "150g osh"})
    assert r.status_code == 200
    assert r.json()["kaloriya"] == 280
