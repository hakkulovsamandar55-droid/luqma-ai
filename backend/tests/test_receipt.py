"""Chek solishtiruv algoritmi testlari.

Bu yerda AI chaqirilmaydi — faqat `receipt.tekshir()` qoidalari sinaladi.
Algoritm pul bilan bog'liq, shuning uchun chetki holatlar batafsil qoplangan.
"""

from datetime import date

import pytest

import receipt

KARTA = "8600 1234 5678 9012"
ISM = "ALIYEV ALISHER"
SUMMA = 30_000
BUGUN = date(2026, 8, 6)


def xom(**kwargs) -> dict:
    """To'g'ri chek — testlar kerakli maydonini o'zgartiradi."""
    asos = {
        "barcha_matn": "Click\nO'tkazma\n8600 **** **** 9012\n30 000 so'm\n06.08.2026",
        "karta_raqamlari": ["8600 **** **** 9012"],
        "summalar": [30000],
        "asosiy_summa": 30000,
        "sana": "2026-08-06",
        "vaqt": "14:22",
        "tranzaksiya_id": "TRX123456",
        "qabul_qiluvchi": "ALIYEV A.",
        "bank": "Click",
        "muvaffaqiyatli": True,
        "chekka_oxshaydi": True,
    }
    asos.update(kwargs)
    return asos


def tekshir(**kwargs):
    return receipt.tekshir(
        xom(**kwargs),
        kutilgan_karta=KARTA,
        kutilgan_ism=ISM,
        kutilgan_summa=SUMMA,
        amal_kuni=3,
        bugun=BUGUN,
    )


# --------------------------------------------------------------------------- #
# Yordamchi funksiyalar
# --------------------------------------------------------------------------- #
def test_oxirgi_tort_raqam():
    assert receipt.oxirgi_tort("8600 1234 5678 9012") == "9012"
    assert receipt.oxirgi_tort("8600****9012") == "9012"
    assert receipt.oxirgi_tort("**** 9012") == "9012"
    assert receipt.oxirgi_tort("12") == ""
    assert receipt.oxirgi_tort("") == ""


def test_ism_solishtirish_turli_yozuvda():
    """Cheklarda ism turlicha yoziladi — bitta so'z mos kelsa yetarli."""
    assert receipt.ismlar_mos("ALIYEV ALISHER", "ALIYEV A.")
    assert receipt.ismlar_mos("ALIYEV ALISHER", "Alisher Aliyev")
    assert receipt.ismlar_mos("Aliyev Alisher", "A. ALIYEV")


def test_ism_mos_kelmasa():
    assert not receipt.ismlar_mos("ALIYEV ALISHER", "KARIMOV BOBUR")
    assert not receipt.ismlar_mos("ALIYEV ALISHER", "")
    assert not receipt.ismlar_mos("", "ALIYEV")


def test_hash_bir_xil_rasmda_teng():
    a = receipt.rasm_hash(b"rasm-baytlari")
    b = receipt.rasm_hash(b"rasm-baytlari")
    assert a == b
    assert a != receipt.rasm_hash(b"boshqa-rasm")


# --------------------------------------------------------------------------- #
# To'g'ri chek
# --------------------------------------------------------------------------- #
def test_togri_chek_otadi():
    n = tekshir()
    assert n.otdi is True
    assert n.izoh == "Hammasi mos keldi"


def test_karta_yashirilgan_bolsa_ham_otadi():
    """Bank oxirgi 4 raqamdan boshqasini yashiradi — shuni solishtiramiz."""
    n = tekshir(karta_raqamlari=["**** **** **** 9012"])
    assert n.otdi is True


def test_summa_kichik_farq_bilan_otadi():
    """Komissiya yoki yaxlitlash farqi rad etilmasin."""
    n = tekshir(asosiy_summa=30_500, summalar=[30_500])
    assert n.otdi is True


def test_asosiy_summa_notogri_aniqlansa_boshqasidan_topadi():
    """AI 'asosiy' summani xato tanlashi mumkin — ro'yxatdan qidiramiz."""
    n = tekshir(asosiy_summa=1500, summalar=[1500, 30_000])
    assert n.otdi is True


def test_karta_yoq_lekin_ism_mos():
    """Ba'zi ilovalar kartani ko'rsatmaydi — ism bo'yicha o'tadi, lekin belgi qoladi."""
    n = tekshir(karta_raqamlari=[], qabul_qiluvchi="ALIYEV A.")
    assert n.otdi is True
    assert "ism bo'yicha" in n.izoh.lower() or "ism bo\u2019yicha" in n.izoh.lower()


def test_kechagi_chek_otadi():
    n = tekshir(sana="2026-08-05")
    assert n.otdi is True


# --------------------------------------------------------------------------- #
# Rad etiladigan holatlar
# --------------------------------------------------------------------------- #
def test_chek_emas_rad_etiladi():
    n = tekshir(chekka_oxshaydi=False)
    assert n.otdi is False
    assert "chek" in n.izoh.lower()


def test_bajarilmagan_tolov_rad_etiladi():
    n = tekshir(muvaffaqiyatli=False)
    assert n.otdi is False


def test_boshqa_karta_rad_etiladi():
    n = tekshir(karta_raqamlari=["8600 **** **** 1111"], qabul_qiluvchi="Boshqa Odam")
    assert n.otdi is False
    assert "karta" in n.izoh.lower()


def test_kam_summa_rad_etiladi():
    n = tekshir(asosiy_summa=5000, summalar=[5000])
    assert n.otdi is False
    assert "summa" in n.izoh.lower()


def test_kop_summa_ham_rad_etiladi():
    """Kutilganidan ko'p bo'lsa ham avtomatik o'tmaydi — admin ko'radi."""
    n = tekshir(asosiy_summa=300_000, summalar=[300_000])
    assert n.otdi is False


def test_eskirgan_chek_rad_etiladi():
    n = tekshir(sana="2026-07-01")
    assert n.otdi is False
    assert "eskirgan" in n.izoh.lower()


def test_kelajakdagi_sana_rad_etiladi():
    """Sanasi o'zgartirilgan chekni ushlaydi."""
    n = tekshir(sana="2026-09-01")
    assert n.otdi is False
    assert "kelajak" in n.izoh.lower()


def test_sanasiz_chek_rad_etiladi():
    n = tekshir(sana=None)
    assert n.otdi is False
    assert "sana" in n.izoh.lower()


def test_ogri_sana_formati_rad_etiladi():
    n = tekshir(sana="kecha")
    assert n.otdi is False


def test_hamma_narsa_notogri():
    n = tekshir(
        karta_raqamlari=["1111"],
        qabul_qiluvchi="Kimdir",
        asosiy_summa=1,
        summalar=[1],
        sana="2020-01-01",
    )
    assert n.otdi is False


# --------------------------------------------------------------------------- #
# Chegara holatlari
# --------------------------------------------------------------------------- #
def test_bosh_maydonlar_yiqitmaydi():
    """AI hech narsa topa olmasa ham funksiya xato bermasin."""
    n = receipt.tekshir(
        {
            "barcha_matn": "",
            "karta_raqamlari": [],
            "summalar": [],
            "asosiy_summa": None,
            "sana": None,
            "vaqt": None,
            "tranzaksiya_id": None,
            "qabul_qiluvchi": None,
            "bank": None,
            "muvaffaqiyatli": True,
            "chekka_oxshaydi": True,
        },
        kutilgan_karta=KARTA,
        kutilgan_ism=ISM,
        kutilgan_summa=SUMMA,
        amal_kuni=3,
        bugun=BUGUN,
    )
    assert n.otdi is False


def test_yetishmagan_kalitlar_yiqitmaydi():
    n = receipt.tekshir(
        {"chekka_oxshaydi": True, "muvaffaqiyatli": True},
        kutilgan_karta=KARTA,
        kutilgan_ism=ISM,
        kutilgan_summa=SUMMA,
        amal_kuni=3,
        bugun=BUGUN,
    )
    assert n.otdi is False


def test_bugungi_chek_amal_kuni_1_bolsa_otadi():
    n = receipt.tekshir(
        xom(),
        kutilgan_karta=KARTA,
        kutilgan_ism=ISM,
        kutilgan_summa=SUMMA,
        amal_kuni=1,
        bugun=BUGUN,
    )
    assert n.otdi is True


@pytest.mark.parametrize("karta", ["8600123456789012", "8600-1234-5678-9012"])
def test_karta_formati_muhim_emas(karta):
    n = receipt.tekshir(
        xom(karta_raqamlari=[karta]),
        kutilgan_karta=KARTA,
        kutilgan_ism=ISM,
        kutilgan_summa=SUMMA,
        amal_kuni=3,
        bugun=BUGUN,
    )
    assert n.otdi is True
