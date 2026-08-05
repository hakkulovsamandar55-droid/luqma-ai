"""Test fixtures — har bir test uchun toza vaqtinchalik DB."""

import os
import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# Modullar import qilinishidan OLDIN muhitni sozlaymiz.
_TMP = tempfile.mkdtemp(prefix="luqma-test-")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TMP}/test.db"
os.environ["MEDIA_DIR"] = f"{_TMP}/media"
os.environ["BOT_TOKEN"] = "123456:TEST-TOKEN-FOR-UNIT-TESTS"
os.environ["DEV_MODE"] = "true"
os.environ["OPENAI_API_KEY"] = "sk-test"

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from api import app  # noqa: E402
from db import Base, engine  # noqa: E402


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def client():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
