"""App Celery de Dionisio."""

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("dionisio")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Sincronización semanal: domingos 03:00 UTC (HU-06).
app.conf.beat_schedule = {
    "sync-movies-weekly": {
        "task": "apps.movies.tasks.sync_movies_weekly",
        "schedule": crontab(hour=3, minute=0, day_of_week=0),
    },
}
