"""initData HMAC validatsiyasi testlari."""

import hashlib
import hmac
import json
import time
from urllib.parse import quote, urlencode

import pytest

from auth import InitDataError, parse_init_data

TOKEN = "123456:TEST-TOKEN-FOR-UNIT-TESTS"


def make_init_data(user_id: int = 42, auth_date: int | None = None, **extra) -> str:
    fields = {
        "auth_date": str(auth_date if auth_date is not None else int(time.time())),
        "query_id": "AAH123",
        "user": json.dumps(
            {"id": user_id, "first_name": "Ali", "last_name": "Valiyev", "username": "ali"},
            separators=(",", ":"),
        ),
        **extra,
    }
    check = "\n".join(f"{k}={fields[k]}" for k in sorted(fields))
    secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


def test_togri_initdata_qabul_qilinadi():
    user = parse_init_data(make_init_data(777), TOKEN)
    assert user.id == 777
    assert user.toliq_ism == "Ali Valiyev"
    assert user.username == "ali"


def test_buzilgan_hash_rad_etiladi():
    buzilgan = make_init_data().replace("hash=", "hash=0")
    with pytest.raises(InitDataError):
        parse_init_data(buzilgan, TOKEN)


def test_boshqa_token_bilan_rad_etiladi():
    with pytest.raises(InitDataError):
        parse_init_data(make_init_data(), "999:BOSHQA-TOKEN")


def test_ozgartirilgan_maydon_rad_etiladi():
    """Foydalanuvchi o'z ID sini almashtirsa hash mos kelmaydi."""
    original = make_init_data(42)
    soxta = original.replace(quote('"id":42'), quote('"id":99'))
    assert soxta != original, "test o'zi ishlamayapti — almashtirish amalga oshmadi"
    with pytest.raises(InitDataError):
        parse_init_data(soxta, TOKEN)


def test_muddati_otgan_initdata_rad_etiladi():
    eski = make_init_data(auth_date=int(time.time()) - 90_000)
    with pytest.raises(InitDataError, match="muddati"):
        parse_init_data(eski, TOKEN, max_age=3600)

    # max_age=0 bo'lsa muddat tekshirilmaydi
    assert parse_init_data(eski, TOKEN, max_age=0).id == 42


def test_bosh_initdata_rad_etiladi():
    with pytest.raises(InitDataError):
        parse_init_data("", TOKEN)


def test_hash_siz_initdata_rad_etiladi():
    with pytest.raises(InitDataError):
        parse_init_data("auth_date=123&user=%7B%7D", TOKEN)
