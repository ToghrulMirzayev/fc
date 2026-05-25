"""
Branding strings — single source of truth for the product name and all
user-facing copy that references it.

To rebrand the platform:
1. Change APP_NAME in .env (the human-readable name; defaults to "Fitness Court")
2. Edit any product-specific copy in this file
3. Replace logo files in frontend/public/brand/ if you have new artwork

If you need to refer to the product in code, import from here — never
hardcode the name elsewhere.
"""

from app.core.config import settings

# Static brand metadata — change here if the product evolves.
BOT_NAME = "Fitness Court Bot"
BOT_REPO_URL = "https://github.com/toghrul/fitnesscourt"
BOT_SUPPORT_EMAIL = "support@fitnesscourt.com"


def app_name() -> str:
    """The current product name. Comes from APP_NAME env var.

    Defaults to "Fitness Court" but ops can change it without redeploy.
    """
    return settings.APP_NAME


# ──────────────────────────────────────────────────────────
# Email subjects
# ──────────────────────────────────────────────────────────
def email_subject_welcome() -> str:
    return f"Welcome to {app_name()}"


def email_subject_password_reset() -> str:
    return f"{app_name()} — password reset"


def email_subject_invoice() -> str:
    return f"{app_name()} — your invoice"


# ──────────────────────────────────────────────────────────
# Telegram bot copy (EN + RU — picked from member.locale)
# ──────────────────────────────────────────────────────────
BOT_COPY: dict[str, dict[str, str]] = {
    "en": {
        "welcome_unlinked": (
            "👋 Welcome to {app}!\n\n"
            "Your account isn't linked yet. Ask your gym to give you a "
            "one-time linking code, then send it here."
        ),
        "welcome_linked": "Welcome back, {name}! 💪",
        "menu_my_plan": "📋 My Plan",
        "menu_show_qr": "🎫 Show QR for check-in",
        "menu_history": "📊 Visit History",
        "menu_help": "❓ Help",
        "qr_caption": (
            "Show this QR to the front desk. It refreshes every {ttl}s for "
            "your security."
        ),
        "plan_expired": "Your plan expired on {date}. Contact the gym to renew.",
        "linking_success": "✅ Account linked! Welcome, {name}.",
        "linking_invalid": "❌ Invalid or expired code. Ask staff for a new one.",
    },
    "ru": {
        "welcome_unlinked": (
            "👋 Добро пожаловать в {app}!\n\n"
            "Ваш аккаунт ещё не привязан. Попросите в зале одноразовый "
            "код привязки и отправьте его сюда."
        ),
        "welcome_linked": "С возвращением, {name}! 💪",
        "menu_my_plan": "📋 Мой тариф",
        "menu_show_qr": "🎫 QR для прохода",
        "menu_history": "📊 История посещений",
        "menu_help": "❓ Помощь",
        "qr_caption": (
            "Покажите QR-код на ресепшене. Он обновляется каждые {ttl} сек "
            "для безопасности."
        ),
        "plan_expired": "Ваш тариф истёк {date}. Обратитесь в зал для продления.",
        "linking_success": "✅ Аккаунт привязан! Добро пожаловать, {name}.",
        "linking_invalid": "❌ Неверный или истёкший код. Попросите новый у персонала.",
    },
}


def bot_text(key: str, locale: str = "en", **kwargs: object) -> str:
    """Get a bot copy string with placeholders filled.

    Example:
        bot_text("welcome_linked", "ru", name="Анна")
    """
    locale = locale if locale in BOT_COPY else "en"
    template = BOT_COPY[locale].get(key) or BOT_COPY["en"][key]
    return template.format(app=app_name(), **kwargs)
