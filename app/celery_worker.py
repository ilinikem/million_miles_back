from celery import Celery
from celery.schedules import crontab

from app.settings import settings

# Читаем ENVIRONMENT как строку
if settings.ENVIRONMENT == "prod":
    broker_url = "redis://redis:6379/0"
    backend_url = "redis://redis:6379/0"
else:
    broker_url = "redis://localhost:6379/0"
    backend_url = "redis://localhost:6379/0"

celery_app = Celery(
    "million_miles",
    broker=broker_url,
    backend=backend_url,
)

celery_app.conf.beat_schedule = {
    "encar-sync-daily": {
        "task": "app.tasks.sync_encar_listings",
        "schedule": crontab(
            hour=settings.encar_beat_hour_utc,
            minute=settings.encar_beat_minute,
        ),
    },
}

celery_app.autodiscover_tasks(["app.tasks"])
