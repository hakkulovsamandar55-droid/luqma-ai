"""To'lov oqimi testlari: chek yuborish, premium berish, admin qarori."""

import io
from unittest.mock import AsyncMock, patch

import pytest

import timeutil
from config import settings
from db import SessionLocal
from models import Tarif, TolovSozlama, User
from vision import VisionError

KARTA = "8600 1234 5678 9012"
ISM = "ALIYEV ALISHER"


def chek_fayl(nom: str = "chek.jpg", bayt: bytes = b"soxta-rasm-baytlari"):
    return {"chek": (nom, io.BytesIO(bayt), "image/jpeg")}


def ai_javob(**kwargs) -> dict:
    d = {
        "barcha_matn": "Click\n8600 **** **** 9012\n30 000 so'm",
        "karta_raqamlari": ["8600 **** **** 9012"],
        "summalar": [30000],
        "asosiy_summa": 30000,
        "sana": timeutil.bugun().isoformat(),
        "vaqt": "14:22",
        "tranzaksiya_id": "TRX-1",
        "qabul_qiluvchi": "ALIYEV A.",
        "bank": "Click",
        "muvaffaqiyatli": True,
        "chekka_oxshaydi": True,
    }
    d.update(kwargs)
    return d


async def _sozla(narx: int = 30_000) -> int:
    """Tarif va to'lov rekvizitlarini tayyorlaydi, tarif id qaytaradi."""
    async with SessionLocal() as session:
        s = await session.get(TolovSozlama, 1)
        if s is None:
            s = TolovSozlama(id=1)
            session.add(s)
        s.karta_raqam = KARTA
        s.karta_egasi = ISM
        s.chek_amal_kuni = 3

        t = Tarif(nom="1 oy", kun=30, narx=narx, faol=True)
        session.add(t)
        await session.commit()
        await session.refresh(t)
        return t.id


async def _meni_admin_qil(client) -> None:
    me = (await client.get("/api/user/me")).json()
    async with SessionLocal() as session:
        u = await session.get(User, me["id"])
        u.is_admin = True
        await session.commit()


# --------------------------------------------------------------------------- #
# Tarif va rekvizitlar
# --------------------------------------------------------------------------- #
@pytest.mark.anyio
async def test_faol_tariflar_korinadi(client):
    await _sozla()
    r = await client.get("/api/tariffs")
    assert r.status_code == 200
    assert any(t["nom"] == "1 oy" for t in r.json())


@pytest.mark.anyio
async def test_ochirilgan_tarif_korinmaydi(client):
    tid = await _sozla()
    await _meni_admin_qil(client)
    await client.patch(f"/api/admin/tariffs/{tid}", json={"faol": False})

    assert all(t["id"] != tid for t in (await client.get("/api/tariffs")).json())


@pytest.mark.anyio
async def test_karta_malumoti_korinadi(client):
    await _sozla()
    d = (await client.get("/api/payment-info")).json()
    assert d["karta_raqam"] == KARTA
    assert d["karta_egasi"] == ISM


@pytest.mark.anyio
async def test_tarif_crud(client):
    await _meni_admin_qil(client)

    r = await client.post(
        "/api/admin/tariffs", json={"nom": "3 oy", "kun": 90, "narx": 80_000}
    )
    assert r.status_code == 200
    tid = r.json()["id"]

    r = await client.patch(f"/api/admin/tariffs/{tid}", json={"narx": 75_000})
    assert r.json()["narx"] == 75_000
    assert r.json()["kun"] == 90  # tegilmagan maydon o'zgarmaydi

    assert (await client.delete(f"/api/admin/tariffs/{tid}")).status_code == 204
    assert (await client.patch(f"/api/admin/tariffs/{tid}", json={})).status_code == 404


@pytest.mark.anyio
async def test_oddiy_user_tarif_qosha_olmaydi(client):
    r = await client.post(
        "/api/admin/tariffs", json={"nom": "Tekin", "kun": 9999, "narx": 0}
    )
    assert r.status_code == 404


# --------------------------------------------------------------------------- #
# Chek yuborish
# --------------------------------------------------------------------------- #
@pytest.mark.anyio
async def test_togri_chek_premium_beradi(client):
    tid = await _sozla()

    with patch("receipt.chekni_oqi", new=AsyncMock(return_value=ai_javob())):
        r = await client.post(
            "/api/payments", data={"tarif_id": tid}, files=chek_fayl()
        )

    assert r.status_code == 200
    d = r.json()
    assert d["avto_otdi"] is True
    assert d["holat"] == "kutilmoqda"  # admin hali ko'rmagan

    # Premium darhol ishlaydi va muddatsiz — admin qaroriga qadar.
    me = (await client.get("/api/user/me")).json()
    assert me["is_premium"] is True


@pytest.mark.anyio
async def test_notogri_summa_premium_bermaydi(client):
    tid = await _sozla()

    with patch(
        "receipt.chekni_oqi",
        new=AsyncMock(return_value=ai_javob(asosiy_summa=100, summalar=[100])),
    ):
        r = await client.post(
            "/api/payments", data={"tarif_id": tid}, files=chek_fayl()
        )

    assert r.json()["avto_otdi"] is False
    assert "summa" in r.json()["tekshiruv_izoh"].lower()
    assert (await client.get("/api/user/me")).json()["is_premium"] is False


@pytest.mark.anyio
async def test_bir_xil_chek_ikki_marta_otmaydi(client):
    tid = await _sozla()
    bayt = b"aynan-shu-rasm"

    with patch("receipt.chekni_oqi", new=AsyncMock(return_value=ai_javob())):
        birinchi = await client.post(
            "/api/payments", data={"tarif_id": tid}, files=chek_fayl(bayt=bayt)
        )
        ikkinchi = await client.post(
            "/api/payments", data={"tarif_id": tid}, files=chek_fayl(bayt=bayt)
        )

    assert birinchi.json()["avto_otdi"] is True
    assert ikkinchi.json()["avto_otdi"] is False
    assert "ilgari yuborilgan" in ikkinchi.json()["tekshiruv_izoh"]


@pytest.mark.anyio
async def test_bir_xil_tranzaksiya_id_otmaydi(client):
    """Boshqa rasm, lekin o'sha tranzaksiya — qayta ishlatishga urinish."""
    tid = await _sozla()

    with patch("receipt.chekni_oqi", new=AsyncMock(return_value=ai_javob())):
        await client.post(
            "/api/payments", data={"tarif_id": tid}, files=chek_fayl(bayt=b"rasm-1")
        )
        ikkinchi = await client.post(
            "/api/payments", data={"tarif_id": tid}, files=chek_fayl(bayt=b"rasm-2")
        )

    assert ikkinchi.json()["avto_otdi"] is False
    assert "tranzaksiya" in ikkinchi.json()["tekshiruv_izoh"].lower()


@pytest.mark.anyio
async def test_ai_ishlamasa_ariza_qoladi(client):
    """AI xato bersa ariza yo'qolmaydi — admin qo'lda ko'radi."""
    tid = await _sozla()

    with patch("receipt.chekni_oqi", new=AsyncMock(side_effect=VisionError("x"))):
        r = await client.post(
            "/api/payments", data={"tarif_id": tid}, files=chek_fayl()
        )

    assert r.status_code == 200
    assert r.json()["avto_otdi"] is False
    assert r.json()["holat"] == "kutilmoqda"


@pytest.mark.anyio
async def test_yoq_tarifga_chek(client):
    await _sozla()
    r = await client.post("/api/payments", data={"tarif_id": 99999}, files=chek_fayl())
    assert r.status_code == 404


@pytest.mark.anyio
async def test_kunlik_chek_chegarasi(client, monkeypatch):
    tid = await _sozla()
    monkeypatch.setattr(settings, "chek_kunlik_limit", 2)

    with patch("receipt.chekni_oqi", new=AsyncMock(return_value=ai_javob())):
        for i in range(2):
            r = await client.post(
                "/api/payments",
                data={"tarif_id": tid},
                files=chek_fayl(bayt=f"rasm-{i}".encode()),
            )
            assert r.status_code == 200

        uchinchi = await client.post(
            "/api/payments", data={"tarif_id": tid}, files=chek_fayl(bayt=b"rasm-3")
        )

    assert uchinchi.status_code == 429


# --------------------------------------------------------------------------- #
# Admin qarori
# --------------------------------------------------------------------------- #
@pytest.mark.anyio
async def test_admin_tasdiqlasa_muddat_qoyiladi(client):
    tid = await _sozla()
    await _meni_admin_qil(client)

    with patch("receipt.chekni_oqi", new=AsyncMock(return_value=ai_javob())):
        p = (
            await client.post("/api/payments", data={"tarif_id": tid}, files=chek_fayl())
        ).json()

    r = await client.patch(f"/api/admin/payments/{p['id']}", json={"tasdiq": True})
    assert r.status_code == 200
    assert r.json()["holat"] == "tasdiqlangan"

    me = (await client.get("/api/user/me")).json()
    assert me["is_premium"] is True
    # Endi muddat aniq — cheksiz emas.
    async with SessionLocal() as session:
        u = await session.get(User, me["id"])
        assert u.premium_tugash is not None
        assert u.premium_tasdiq_kutilmoqda is False


@pytest.mark.anyio
async def test_admin_rad_etsa_premium_olinadi(client):
    tid = await _sozla()
    await _meni_admin_qil(client)

    with patch("receipt.chekni_oqi", new=AsyncMock(return_value=ai_javob())):
        p = (
            await client.post("/api/payments", data={"tarif_id": tid}, files=chek_fayl())
        ).json()

    assert (await client.get("/api/user/me")).json()["is_premium"] is True

    r = await client.patch(
        f"/api/admin/payments/{p['id']}",
        json={"tasdiq": False, "izoh": "Chek soxta"},
    )
    assert r.json()["holat"] == "rad_etilgan"
    assert r.json()["admin_izoh"] == "Chek soxta"

    assert (await client.get("/api/user/me")).json()["is_premium"] is False


@pytest.mark.anyio
async def test_rad_etish_qolda_berilgan_premiumni_olmaydi(client):
    """Admin qo'lda bergan premium chek rad etilganda yo'qolmasligi kerak."""
    tid = await _sozla()
    await _meni_admin_qil(client)
    me = (await client.get("/api/user/me")).json()

    # Avval qo'lda premium beramiz (tasdiq kutilmayapti).
    await client.patch(
        f"/api/admin/users/{me['id']}", json={"is_premium": True, "premium_kun": 30}
    )

    with patch(
        "receipt.chekni_oqi",
        new=AsyncMock(return_value=ai_javob(asosiy_summa=1, summalar=[1])),
    ):
        p = (
            await client.post("/api/payments", data={"tarif_id": tid}, files=chek_fayl())
        ).json()

    await client.patch(f"/api/admin/payments/{p['id']}", json={"tasdiq": False})

    assert (await client.get("/api/user/me")).json()["is_premium"] is True


@pytest.mark.anyio
async def test_admin_arizalarni_koradi(client):
    tid = await _sozla()
    await _meni_admin_qil(client)

    with patch("receipt.chekni_oqi", new=AsyncMock(return_value=ai_javob())):
        await client.post("/api/payments", data={"tarif_id": tid}, files=chek_fayl())

    r = await client.get("/api/admin/payments?holat=kutilmoqda")
    assert r.status_code == 200
    assert len(r.json()) >= 1
    # Admin AI o'qigan matnni ham ko'radi.
    assert r.json()[0]["ai_matn"] is not None
    assert r.json()[0]["user_telegram_id"] != 0


@pytest.mark.anyio
async def test_oddiy_user_arizalarni_kora_olmaydi(client):
    assert (await client.get("/api/admin/payments")).status_code == 404


@pytest.mark.anyio
async def test_oz_arizalarini_koradi(client):
    tid = await _sozla()

    with patch("receipt.chekni_oqi", new=AsyncMock(return_value=ai_javob())):
        await client.post("/api/payments", data={"tarif_id": tid}, files=chek_fayl())

    r = await client.get("/api/payments/me")
    assert r.status_code == 200
    assert len(r.json()) == 1
    # Foydalanuvchiga AI matni ko'rsatilmaydi.
    assert "ai_matn" not in r.json()[0]


# --------------------------------------------------------------------------- #
# Tahlil premium talab qiladi
# --------------------------------------------------------------------------- #
@pytest.mark.anyio
async def test_premiumsiz_tahlil_qilib_bolmaydi(client, monkeypatch):
    """Asosiy to'siq backendda: API to'g'ridan-to'g'ri chaqirilishi mumkin."""
    from config import settings as st

    monkeypatch.setattr(st, "bepul_tahlil_soni", 0)

    r = await client.post("/api/meals/analyze-text", json={"matn": "osh"})
    assert r.status_code == 402
    assert "premium" in r.json()["detail"].lower()


@pytest.mark.anyio
async def test_premium_bilan_tahlil_ishlaydi(client):
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

    me = (await client.get("/api/user/me")).json()
    async with SessionLocal() as session:
        u = await session.get(User, me["id"])
        u.is_premium = True
        await session.commit()

    with patch("vision.matnni_tahlil_qil", new=AsyncMock(return_value=tahlil)):
        r = await client.post("/api/meals/analyze-text", json={"matn": "osh"})
    assert r.status_code == 200


@pytest.mark.anyio
async def test_bepul_sinov_soni_ishlaydi(client, monkeypatch):
    """Admin bepul sinov bersa, yangi foydalanuvchi sotib olmasdan sinaydi."""
    from config import settings as st
    from schemas import MealAnalysis

    monkeypatch.setattr(st, "bepul_tahlil_soni", 2)

    tahlil = MealAnalysis(
        taom_nomi="Osh",
        ulush="1 tovoq",
        kaloriya=600,
        protein_g=25.0,
        yog_g=20.0,
        uglevod_g=70.0,
        ishonch=0.8,
    )

    with patch("vision.matnni_tahlil_qil", new=AsyncMock(return_value=tahlil)):
        for _ in range(2):
            assert (
                await client.post("/api/meals/analyze-text", json={"matn": "osh"})
            ).status_code == 200
        uchinchi = await client.post("/api/meals/analyze-text", json={"matn": "osh"})

    assert uchinchi.status_code == 402


@pytest.mark.anyio
async def test_chat_premiumsiz_ham_ishlaydi(client):
    """Murabbiy to'siq ortida emas — u ilovani sinab ko'rish yo'li."""
    import chat as coach

    with patch.object(coach, "javob_ol", new=AsyncMock(return_value="ok")):
        r = await client.post("/api/chat", json={"matn": "salom"})
    assert r.status_code == 200


@pytest.mark.anyio
async def test_yordam_username_saqlanadi(client):
    await _meni_admin_qil(client)

    r = await client.put(
        "/api/admin/payment-settings",
        json={
            "karta_raqam": KARTA,
            "karta_egasi": ISM,
            "chek_amal_kuni": 3,
            "yordam_username": "luqma_admin",
        },
    )
    assert r.status_code == 200
    assert r.json()["yordam_username"] == "luqma_admin"

    # Oddiy foydalanuvchi ham ko'ra oladi — yordam tugmasi shundan oladi.
    assert (await client.get("/api/payment-info")).json()["yordam_username"] == "luqma_admin"


# --------------------------------------------------------------------------- #
# Rasm formati
# --------------------------------------------------------------------------- #
@pytest.mark.anyio
async def test_heic_aniq_xabar_bilan_rad_etiladi(client):
    """HEIC ni AI o'qiy olmaydi va brauzer ko'rsatmaydi — darhol tushuntiramiz."""
    tid = await _sozla()

    r = await client.post(
        "/api/payments",
        data={"tarif_id": tid},
        files={"chek": ("chek.heic", io.BytesIO(b"rasm"), "image/heic")},
    )

    assert r.status_code == 415
    assert "HEIC" in r.json()["detail"]


@pytest.mark.anyio
async def test_png_chek_png_bolib_saqlanadi(client):
    """Kengaytma MIME turiga mos bo'lishi kerak, aks holda rasm ochilmaydi."""
    tid = await _sozla()

    with patch("receipt.chekni_oqi", new=AsyncMock(return_value=ai_javob())):
        r = await client.post(
            "/api/payments",
            data={"tarif_id": tid},
            files={"chek": ("chek.png", io.BytesIO(b"png-baytlari"), "image/png")},
        )

    assert r.status_code == 200
    async with SessionLocal() as session:
        from sqlalchemy import select

        from models import Payment

        p = await session.scalar(select(Payment).order_by(Payment.id.desc()))
        assert p.chek_yoli.endswith(".png")


# --------------------------------------------------------------------------- #
# Bir nechta ariza
# --------------------------------------------------------------------------- #
@pytest.mark.anyio
async def test_bitta_arizani_rad_etish_ikkinchisini_buzmaydi(client):
    """Ikkita avtomatik o'tgan ariza bo'lsa, birini rad etish premiumni olmaydi."""
    tid = await _sozla()
    await _meni_admin_qil(client)

    with patch("receipt.chekni_oqi", new=AsyncMock(return_value=ai_javob())):
        birinchi = (
            await client.post(
                "/api/payments", data={"tarif_id": tid}, files=chek_fayl(bayt=b"rasm-a")
            )
        ).json()

    with patch(
        "receipt.chekni_oqi",
        new=AsyncMock(return_value=ai_javob(tranzaksiya_id="TRX-2")),
    ):
        ikkinchi = (
            await client.post(
                "/api/payments", data={"tarif_id": tid}, files=chek_fayl(bayt=b"rasm-b")
            )
        ).json()

    assert birinchi["avto_otdi"] is True
    assert ikkinchi["avto_otdi"] is True

    # Birinchisini rad etamiz — ikkinchisi hali kutmoqda, premium qolishi kerak.
    await client.patch(f"/api/admin/payments/{birinchi['id']}", json={"tasdiq": False})
    assert (await client.get("/api/user/me")).json()["is_premium"] is True

    # Ikkinchisi ham rad etilsa — endi asos qolmadi.
    await client.patch(f"/api/admin/payments/{ikkinchi['id']}", json={"tasdiq": False})
    assert (await client.get("/api/user/me")).json()["is_premium"] is False


# --------------------------------------------------------------------------- #
# Hisobni o'chirish
# --------------------------------------------------------------------------- #
@pytest.mark.anyio
async def test_hisob_ochirilsa_chek_ham_ketadi(client):
    """Chekda ism, karta va tranzaksiya ID bor — hisob bilan birga o'chishi shart."""
    from pathlib import Path

    tid = await _sozla()

    with patch("receipt.chekni_oqi", new=AsyncMock(return_value=ai_javob())):
        await client.post("/api/payments", data={"tarif_id": tid}, files=chek_fayl())

    me = (await client.get("/api/user/me")).json()

    async with SessionLocal() as session:
        from sqlalchemy import select

        from models import Payment

        p = await session.scalar(select(Payment).where(Payment.user_id == me["id"]))
        assert p is not None
        fayl = Path(settings.media_path) / Path(p.chek_yoli).name
        assert fayl.exists()

    assert (await client.delete("/api/user/me")).status_code == 204

    assert not fayl.exists()
    async with SessionLocal() as session:
        from sqlalchemy import func, select

        from models import Payment

        qolgan = await session.scalar(
            select(func.count(Payment.id)).where(Payment.user_id == me["id"])
        )
        assert qolgan == 0
