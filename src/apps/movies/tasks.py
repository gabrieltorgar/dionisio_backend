"""Tareas Celery del catálogo (HU-06)."""

import logging

from celery import shared_task

from apps.movies.services import sync_movies

logger = logging.getLogger("apps")


@shared_task(name="apps.movies.tasks.sync_movies_weekly")
def sync_movies_weekly() -> dict[str, int]:
    """Sincronización semanal programada (domingos 03:00 UTC)."""
    result = sync_movies(pages=1, download_images=True)
    return {
        "created": result.created,
        "updated": result.updated,
        "errors": len(result.errors),
    }
