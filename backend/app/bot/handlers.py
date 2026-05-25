"""Telegram bot handlers.

Webhook mode. The dispatcher is bound to the FastAPI app via /bot/webhook.

Handlers are minimal in v1.0:
- /start — show welcome, prompt to link or show menu
- Plain text matching 6 digits — try to consume linking code
- "My plan" button — show plan summary
- "Show QR" button — generate and send rotating QR
- "History" button — last 5 visits
"""

from __future__ import annotations

from datetime import date

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    BufferedInputFile,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.branding import bot_text
from app.core.config import settings
from app.core.security import make_qr_token
from app.db.session import SessionLocal
from app.models.member import Member
from app.models.membership import Membership, MembershipStatus
from app.services.linking import consume_linking_code
from app.services.member import days_left_to, get_active_membership
from app.services.qr_image import qr_png_bytes

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN) if settings.TELEGRAM_BOT_TOKEN else None
dp = Dispatcher()


def _menu_keyboard(locale: str = "en") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=bot_text("menu_my_plan", locale)),
                KeyboardButton(text=bot_text("menu_show_qr", locale)),
            ],
            [
                KeyboardButton(text=bot_text("menu_history", locale)),
                KeyboardButton(text=bot_text("menu_help", locale)),
            ],
        ],
        resize_keyboard=True,
    )


async def _find_member_by_tg(
    db: AsyncSession, telegram_user_id: int
) -> Member | None:
    result = await db.execute(
        select(Member).where(Member.telegram_user_id == telegram_user_id)
    )
    return result.scalar_one_or_none()


@dp.message(CommandStart())
async def handle_start(message: Message) -> None:
    if message.from_user is None:
        return
    async with SessionLocal() as db:
        member = await _find_member_by_tg(db, message.from_user.id)
        locale = (
            member.locale
            if member
            else (message.from_user.language_code or "en")[:2]
        )
        if member is None:
            await message.answer(bot_text("welcome_unlinked", locale))
        else:
            await message.answer(
                bot_text("welcome_linked", locale, name=member.full_name),
                reply_markup=_menu_keyboard(locale),
            )


@dp.message(F.text.regexp(r"^\d{6}$"))
async def handle_linking_code(message: Message) -> None:
    if message.from_user is None or message.text is None:
        return
    code = message.text.strip()
    async with SessionLocal() as db:
        member = await consume_linking_code(db, code, message.from_user.id)
        if member is None:
            locale = (message.from_user.language_code or "en")[:2]
            await message.answer(bot_text("linking_invalid", locale))
            return
        await db.commit()
        locale = member.locale
        await message.answer(
            bot_text("linking_success", locale, name=member.full_name),
            reply_markup=_menu_keyboard(locale),
        )


def _menu_label_match(text: str, key: str) -> bool:
    """A button label can come back in any locale; match against both."""
    return any(
        text == bot_text(key, loc) for loc in ("en", "ru")
    )


@dp.message(F.text)
async def handle_menu(message: Message) -> None:
    if message.from_user is None or message.text is None:
        return
    text = message.text.strip()

    async with SessionLocal() as db:
        member = await _find_member_by_tg(db, message.from_user.id)
        if member is None:
            locale = (message.from_user.language_code or "en")[:2]
            await message.answer(bot_text("welcome_unlinked", locale))
            return

        locale = member.locale

        if _menu_label_match(text, "menu_my_plan"):
            await _send_plan(message, db, member)
        elif _menu_label_match(text, "menu_show_qr"):
            await _send_qr_if_paid(message, db, member)
        elif _menu_label_match(text, "menu_history"):
            await _send_history(message, db, member)
        elif _menu_label_match(text, "menu_help"):
            await message.answer(
                "Show your QR at the front desk. Visits and plan info live here.",
                reply_markup=_menu_keyboard(locale),
            )
        else:
            await message.answer(
                "Tap a button below.", reply_markup=_menu_keyboard(locale)
            )


async def _send_plan(
    message: Message, db: AsyncSession, member: Member
) -> None:
    active = await get_active_membership(db, member.id)
    if active is None:
        await message.answer(
            bot_text("plan_expired", member.locale, date="—"),
            reply_markup=_menu_keyboard(member.locale),
        )
        return

    days = days_left_to(active.expires_on)
    if not active.is_paid:
        status_emoji = "🔒"
        status_label = "Awaiting payment"
    elif active.status == MembershipStatus.ACTIVE:
        status_emoji = "🟢"
        status_label = "Active"
    else:
        status_emoji = "🔵"
        status_label = active.status.value.capitalize()
    visits_line = (
        f"Visits: {active.visits_remaining}/{active.visit_limit}"
        if active.visit_limit is not None
        else "Visits: unlimited"
    )
    text = (
        f"{status_emoji} *{active.plan_name}* — {status_label}\n"
        f"Expires: {active.expires_on.isoformat()} ({days} days)\n"
        f"{visits_line}"
    )
    if not active.is_paid:
        text += (
            "\n\n⚠️ Your card is locked until payment is recorded. "
            "Please visit reception to complete payment."
        )
    await message.answer(
        text, parse_mode="Markdown", reply_markup=_menu_keyboard(member.locale)
    )


async def _send_qr_if_paid(
    message: Message, db: AsyncSession, member: Member
) -> None:
    """Wrap QR send with a payment check."""
    active = await get_active_membership(db, member.id)
    if active is None:
        await message.answer(
            "You don't have an active plan. Please contact the gym.",
            reply_markup=_menu_keyboard(member.locale),
        )
        return
    if not active.is_paid:
        await message.answer(
            "🔒 Your card is locked.\n\nPayment hasn't been recorded yet. "
            "Please visit reception to complete payment, then your QR will unlock.",
            reply_markup=_menu_keyboard(member.locale),
        )
        return
    await _send_qr(message, member)


async def _send_qr(message: Message, member: Member) -> None:
    token, _nonce = make_qr_token(member.id, member.tenant_id)
    png = qr_png_bytes(token)
    caption = bot_text(
        "qr_caption", member.locale, ttl=settings.QR_TOKEN_TTL_SECONDS
    )
    await message.answer_photo(
        BufferedInputFile(png, filename="qr.png"),
        caption=caption,
        reply_markup=_menu_keyboard(member.locale),
    )


async def _send_history(
    message: Message, db: AsyncSession, member: Member
) -> None:
    from app.models.visit import Visit

    result = await db.execute(
        select(Visit)
        .where(Visit.member_id == member.id)
        .order_by(Visit.checked_in_at.desc())
        .limit(5)
    )
    visits = result.scalars().all()
    if not visits:
        await message.answer(
            "No visits yet.", reply_markup=_menu_keyboard(member.locale)
        )
        return
    lines = ["📊 *Last visits*"]
    for v in visits:
        lines.append(f"• {v.checked_in_at.strftime('%b %d, %H:%M')}")
    await message.answer(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=_menu_keyboard(member.locale),
    )
