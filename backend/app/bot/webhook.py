"""Telegram webhook receiver.

POST /bot/webhook receives updates from Telegram. We validate the secret
header before passing the update to aiogram.
"""

from aiogram.types import Update
from fastapi import APIRouter, Header, HTTPException, Request

from app.bot.handlers import bot, dp
from app.core.config import settings

router = APIRouter()


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict:
    if bot is None:
        raise HTTPException(status_code=503, detail="Telegram bot not configured")
    if settings.TELEGRAM_WEBHOOK_SECRET and (
        x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET
    ):
        raise HTTPException(status_code=401, detail="Bad webhook secret")

    payload = await request.json()
    update = Update.model_validate(payload)
    await dp.feed_update(bot, update)
    return {"ok": True}
