"""Celery app.

Used for background jobs and scheduled tasks. In v1.0 we have:
- daily membership status recompute (planned)
- expiration reminder sends (planned)
- nothing wired yet; this is the skeleton.
"""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "fitnesscourt",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Periodic tasks land here in Sprint 3.
    beat_schedule={},
)


@celery_app.task
def ping() -> str:
    """Sanity-check task."""
    return "pong"
