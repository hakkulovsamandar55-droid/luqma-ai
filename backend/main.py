"""Bitta process ichida FastAPI + aiogram botni ishga tushirish.

    python main.py            # API + bot birga
    uvicorn api:app           # faqat API
    python bot.py             # faqat bot
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os

import uvicorn

from api import app
from bot import run_bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("luqma")


async def main() -> None:
    config = uvicorn.Config(
        app,
        host=os.getenv("HOST", "0.0.0.0"),  # noqa: S104 - container ichida
        port=int(os.getenv("PORT", "8000")),
        log_level="info",
        access_log=False,
    )
    server = uvicorn.Server(config)

    bot_task = asyncio.create_task(run_bot(), name="bot")
    api_task = asyncio.create_task(server.serve(), name="api")

    done, pending = await asyncio.wait(
        {bot_task, api_task}, return_when=asyncio.FIRST_COMPLETED
    )
    for task in done:
        if exc := task.exception():
            log.error("%s to'xtadi: %s", task.get_name(), exc)

    for task in pending:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
