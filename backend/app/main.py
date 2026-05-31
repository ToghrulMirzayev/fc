"""Fitness Court API entry point.

Composes:
- FastAPI app
- API v1 router (auth, tenants, memberships, ...)
- Telegram bot webhook (mounted at /bot/webhook)
- Health check
"""

from contextlib import asynccontextmanager

import sentry_sdk
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.branding import app_name
from app.core.config import settings
from app.core.logging import configure_logging

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    if settings.SENTRY_DSN_BACKEND:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN_BACKEND,
            environment=settings.ENV,
            traces_sample_rate=0.1 if settings.ENV == "prod" else 1.0,
        )
    logger.info("startup", app=app_name(), env=settings.ENV)
    yield
    logger.info("shutdown")


app = FastAPI(
    title=f"{app_name()} API",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
    lifespan=lifespan,
)

# CORS — tighten in prod via env-driven origins list.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [
        f"https://{settings.APP_DOMAIN}",
        f"https://*.{settings.APP_DOMAIN}"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe. UptimeRobot hits this."""
    return {
        "status": "ok",
        "app": app_name(),
        "env": settings.ENV,
        "version": app.version,
    }


# Routers
from app.api.v1.router import router as api_v1_router  # noqa: E402
from app.bot.webhook import router as bot_router  # noqa: E402

app.include_router(api_v1_router, prefix="/api/v1")
app.include_router(bot_router, prefix="/bot")
