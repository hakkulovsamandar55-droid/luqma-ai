"""Mifflin-St Jeor va limit hisoblash testlari."""

import pytest

from nutrition import bmr_mifflin, hisobla, tdee


def test_bmr_erkak():
    # 10*80 + 6.25*180 - 5*30 + 5 = 800 + 1125 - 150 + 5
    assert bmr_mifflin("erkak", 80, 180, 30) == pytest.approx(1780.0)


def test_bmr_ayol():
    # 10*60 + 6.25*165 - 5*25 - 161 = 600 + 1031.25 - 125 - 161
    assert bmr_mifflin("ayol", 60, 165, 25) == pytest.approx(1345.25)


def test_tdee_faollik_bilan_oshadi():
    bmr = bmr_mifflin("erkak", 80, 180, 30)
    assert tdee(bmr, "sedentary") < tdee(bmr, "moderate") < tdee(bmr, "athlete")


def test_maqsad_kaloriyaga_tasir_qiladi():
    kwargs = dict(jins="erkak", vazn_kg=80, boy_sm=180, yosh=30, faollik="moderate")
    yoqotish = hisobla(**kwargs, maqsad="yoqotish")
    saqlash = hisobla(**kwargs, maqsad="saqlash")
    oshirish = hisobla(**kwargs, maqsad="oshirish")

    assert yoqotish.kaloriya < saqlash.kaloriya < oshirish.kaloriya


def test_makrolar_kaloriyaga_mos_keladi():
    lim = hisobla(
        jins="erkak", vazn_kg=80, boy_sm=180, yosh=30,
        faollik="moderate", maqsad="saqlash",
    )
    jami = lim.protein_g * 4 + lim.yog_g * 9 + lim.uglevod_g * 4
    # Yaxlitlash sababli 2% gacha farq bo'lishi mumkin.
    assert jami == pytest.approx(lim.kaloriya, rel=0.02)


def test_minimal_kaloriyadan_pastga_tushmaydi():
    """Kichik jussali ayol + agressiv defitsit ham xavfsiz chegarada qoladi."""
    lim = hisobla(
        jins="ayol", vazn_kg=45, boy_sm=150, yosh=60,
        faollik="sedentary", maqsad="yoqotish",
    )
    assert lim.kaloriya >= 1200


def test_suv_limiti_vaznga_bogliq():
    kwargs = dict(boy_sm=180, yosh=30, faollik="light", maqsad="saqlash", jins="erkak")
    assert hisobla(**kwargs, vazn_kg=60).suv_ml < hisobla(**kwargs, vazn_kg=100).suv_ml


def test_notogri_faollik_default_ga_tushadi():
    lim = hisobla(
        jins="erkak", vazn_kg=80, boy_sm=180, yosh=30,
        faollik="yoq-bunday", maqsad="saqlash",
    )
    kutilgan = hisobla(
        jins="erkak", vazn_kg=80, boy_sm=180, yosh=30,
        faollik="light", maqsad="saqlash",
    )
    assert lim.kaloriya == kutilgan.kaloriya
