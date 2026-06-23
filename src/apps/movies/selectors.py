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


def movie_deck(
    *,
    level: str | None = None,
    genre: str | None = None,
    collection: str | None = None,
    exclude_ids: list[str] | None = None,
    count: int = 30,
) -> list[Movie]:
    """Arma un mazo aleatorio para una partida con máxima dispersión.

    Toma películas activas (filtradas) en orden aleatorio, excluyendo las
    `exclude_ids` (imdb_id) usadas recientemente. Si no hay suficientes sin
    excluir (catálogo pequeño), rellena con las excluidas, también al azar.
    """
    base = list_active_movies(level=level, genre=genre, collection=collection)
    exclude_ids = exclude_ids or []

    deck = list(base.exclude(imdb_id__in=exclude_ids).order_by("?")[:count])
    if len(deck) < count:
        remaining = count - len(deck)
        deck += list(base.filter(imdb_id__in=exclude_ids).order_by("?")[:remaining])
    return deck
