"""Mashq bo'limi, mahalliy ovqat bazasi va eslatmalar testlari."""

import pytest

from db import SessionLocal
from models import Exercise, FoodItem, User

PROFIL = {
    "jins": "erkak",
    "yosh": 30,
    "boy_sm": 175,
    "joriy_vazn_kg": 80,
    "faollik_darajasi": "moderate",
    "maqsad_turi": "saqlash",
}


async def _meni_admin_qil(client) -> None:
    me = (await client.get("/api/user/me")).json()
    async with SessionLocal() as session:
        u = await session.get(User, me["id"])
        u.is_admin = True
        await session.commit()


async def _mashq_qosh(nom="Cho'kkalash", daraja="boshlangich", turkum="kuch") -> int:
    async with SessionLocal() as session:
        e = Exercise(
            nom=nom,
            daraja=daraja,
            turkum=turkum,
            davomiylik_sek=180,
            kaloriya=45,
        )
        session.add(e)
        await session.commit()
        await session.refresh(e)
        return e.id


# --------------------------------------------------------------------------- #
# Ovqat bazasi
# --------------------------------------------------------------------------- #
@pytest.mark.anyio
async def test_baza_avtomatik_toldiriladi(client):
    """init_db boshlang'ich taomlarni qo'shadi — bo'sh ilova bo'lmasin."""
    r = await client.get("/api/foods")
    assert r.status_code == 200
    assert len(r.json()) > 0


@pytest.mark.anyio
async def test_qidiruv_nom_boyicha(client):
    r = await client.get("/api/foods?q=osh")
    assert r.status_code == 200
    assert any("osh" in f["nom"].lower() for f in r.json())


@pytest.mark.anyio
async def test_qidiruv_kalit_soz_boyicha(client):
    """'palov' deb qidirilsa ham 'Osh' topilishi kerak."""
    r = await client.get("/api/foods?q=palov")
    nomlar = [f["nom"] for f in r.json()]
    assert "Osh" in nomlar


@pytest.mark.anyio
async def test_qidiruv_premium_talab_qilmaydi(client):
    """Baza qidiruvi AI chaqirmaydi — hammaga ochiq bo'lishi kerak."""
    me = (await client.get("/api/user/me")).json()
    assert me["is_premium"] is False

    r = await client.get("/api/foods?q=somsa")
    assert r.status_code == 200
    assert len(r.json()) > 0


@pytest.mark.anyio
async def test_qidiruv_topilmasa_bosh_royxat(client):
    r = await client.get("/api/foods?q=zzzxxxyyy")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.anyio
async def test_ochirilgan_ovqat_korinmaydi(client):
    async with SessionLocal() as session:
        f = FoodItem(nom="Test taom", kalit_sozlar="testtaom", faol=False)
        session.add(f)
        await session.commit()

    r = await client.get("/api/foods?q=testtaom")
    assert r.json() == []


# --------------------------------------------------------------------------- #
# Mashqlar
# --------------------------------------------------------------------------- #
@pytest.mark.anyio
async def test_mashqlar_royxati(client):
    await _mashq_qosh()
    r = await client.get("/api/exercises")
    assert r.status_code == 200
    assert any(e["nom"] == "Cho'kkalash" for e in r.json())


@pytest.mark.anyio
async def test_mashq_daraja_boyicha_filtr(client):
    await _mashq_qosh("Oson mashq", daraja="boshlangich")
    await _mashq_qosh("Qiyin mashq", daraja="yuqori")

    r = await client.get("/api/exercises?daraja=yuqori")
    nomlar = [e["nom"] for e in r.json()]
    assert "Qiyin mashq" in nomlar
    assert "Oson mashq" not in nomlar


@pytest.mark.anyio
async def test_mashq_bajarilganini_saqlash(client):
    eid = await _mashq_qosh()

    r = await client.post("/api/exercise-logs", json={"exercise_id": eid})
    assert r.status_code == 200
    assert r.json()["nom"] == "Cho'kkalash"
    # Kaloriya bazadan olinadi, mijozdan emas.
    assert r.json()["kaloriya"] == 45


@pytest.mark.anyio
async def test_mijoz_kaloriyani_ozgartira_olmaydi(client):
    """Mashq bazadan tanlangan bo'lsa, qiymatlar serverdan olinadi."""
    eid = await _mashq_qosh()

    # Ruxsat etilgan oraliqda, lekin bazadagidan farqli qiymat:
    # validatsiya emas, server mantiqi tekshirilyapti.
    r = await client.post(
        "/api/exercise-logs",
        json={"exercise_id": eid, "kaloriya": 500, "nom": "Soxta"},
    )
    assert r.status_code == 200
    assert r.json()["kaloriya"] == 45
    assert r.json()["nom"] == "Cho'kkalash"


@pytest.mark.anyio
async def test_haddan_katta_kaloriya_rad_etiladi(client):
    """Validatsiya aqlga sig'maydigan qiymatni o'tkazmasligi kerak."""
    r = await client.post("/api/exercise-logs", json={"kaloriya": 99999})
    assert r.status_code == 422


@pytest.mark.anyio
async def test_mashq_loglari_faqat_ozimniki(client):
    """Boshqa foydalanuvchining mashqlari ko'rinmasligi kerak."""
    from models import ExerciseLog

    import timeutil

    async with SessionLocal() as session:
        boshqa = User(telegram_id=880_001)
        session.add(boshqa)
        await session.commit()
        await session.refresh(boshqa)

        session.add(
            ExerciseLog(
                user_id=boshqa.id,
                nom="Begona mashq",
                davomiylik_sek=60,
                kaloriya=20,
                sana=timeutil.bugun(),
            )
        )
        await session.commit()

    r = await client.get("/api/exercise-logs")
    assert all(x["nom"] != "Begona mashq" for x in r.json())


@pytest.mark.anyio
async def test_admin_mashq_crud(client):
    await _meni_admin_qil(client)

    r = await client.post(
        "/api/admin/exercises",
        json={"nom": "Yangi mashq", "daraja": "orta", "turkum": "kuch"},
    )
    assert r.status_code == 200
    eid = r.json()["id"]

    r = await client.patch(
        f"/api/admin/exercises/{eid}",
        json={"nom": "Yangi mashq", "daraja": "orta", "turkum": "kuch", "faol": False},
    )
    assert r.json()["faol"] is False

    # O'chirilgan mashq foydalanuvchiga ko'rinmaydi.
    assert all(e["id"] != eid for e in (await client.get("/api/exercises")).json())

    assert (await client.delete(f"/api/admin/exercises/{eid}")).status_code == 204


@pytest.mark.anyio
async def test_oddiy_user_mashq_qosha_olmaydi(client):
    r = await client.post("/api/admin/exercises", json={"nom": "Ruxsatsiz"})
    assert r.status_code == 404


# --------------------------------------------------------------------------- #
# Eslatmalar
# --------------------------------------------------------------------------- #
@pytest.mark.anyio
async def test_eslatma_yaratish_va_royxat(client):
    r = await client.post(
        "/api/reminders", json={"tur": "suv", "soat": 10, "daqiqa": 30}
    )
    assert r.status_code == 200
    assert r.json()["tur"] == "suv"

    royxat = (await client.get("/api/reminders")).json()
    assert len(royxat) == 1


@pytest.mark.anyio
async def test_eslatma_ozgartirish(client):
    r = await client.post("/api/reminders", json={"tur": "ovqat", "soat": 8})
    rid = r.json()["id"]

    r = await client.patch(
        f"/api/reminders/{rid}",
        json={"tur": "ovqat", "soat": 9, "daqiqa": 15, "yoqilgan": False},
    )
    assert r.json()["soat"] == 9
    assert r.json()["yoqilgan"] is False


@pytest.mark.anyio
async def test_eslatma_ochirish(client):
    r = await client.post("/api/reminders", json={"tur": "harakat", "soat": 18})
    rid = r.json()["id"]

    assert (await client.delete(f"/api/reminders/{rid}")).status_code == 204
    assert (await client.get("/api/reminders")).json() == []


@pytest.mark.anyio
async def test_boshqaning_eslatmasini_ozgartirib_bolmaydi(client):
    from models import Reminder

    async with SessionLocal() as session:
        boshqa = User(telegram_id=880_002)
        session.add(boshqa)
        await session.commit()
        await session.refresh(boshqa)

        r = Reminder(user_id=boshqa.id, tur="suv", soat=10)
        session.add(r)
        await session.commit()
        await session.refresh(r)
        begona_id = r.id

    resp = await client.patch(
        f"/api/reminders/{begona_id}", json={"tur": "suv", "soat": 23}
    )
    assert resp.status_code == 404

    assert (await client.delete(f"/api/reminders/{begona_id}")).status_code == 404


@pytest.mark.anyio
async def test_notogri_eslatma_turi_rad_etiladi(client):
    r = await client.post("/api/reminders", json={"tur": "boshqa", "soat": 10})
    assert r.status_code == 422


@pytest.mark.anyio
async def test_notogri_soat_rad_etiladi(client):
    r = await client.post("/api/reminders", json={"tur": "suv", "soat": 25})
    assert r.status_code == 422
