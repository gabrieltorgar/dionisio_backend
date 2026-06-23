"""Consultas de lectura del catálogo (HU-04)."""

from django.db.models import QuerySet

from apps.movies.models import Collection, Movie


def list_active_movies(
    *,
    level: str | None = None,
    genre: str | None = None,
    collection: str | None = None,
) -> QuerySet[Movie]:
    """Devuelve películas activas filtradas por nivel, género y/o colección."""
    qs = Movie.objects.filter(is_active=True)
    if level:
        qs = qs.filter(level=level)
    if genre:
        qs = qs.filter(genres__contains=[genre])
    if collection:
        qs = qs.filter(collections__contains=[collection])
    return qs


def list_active_collections() -> QuerySet[Collection]:
    """Devuelve las colecciones activas (HU-07)."""
    return Collection.objects.filter(is_active=True)
