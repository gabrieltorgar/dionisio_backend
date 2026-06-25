"""Lógica de negocio del catálogo: sincronización OMDb y caché de imágenes.

HU-05 (imágenes locales), HU-06 (sync OMDb).

OMDb no expone "populares": se sincroniza buscando por una lista de términos
(`OMDB_SEARCH_TERMS`) y obteniendo el detalle de cada resultado por su ID IMDb.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction

from apps.movies.models import Movie, MovieLevel
from apps.movies.omdb import OMDBClient, OMDBError
from apps.movies.wikidata import WikidataClient

logger = logging.getLogger("apps")


@dataclass
class SyncResult:
    """Resumen de una sincronización (HU-06)."""

    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)


def assign_level(*, votes: int) -> str:
    """Asigna nivel según la cantidad de votos IMDb (proxy de popularidad).

    A más votos, más mainstream (nivel más casual).
    """
    if votes > 500_000:
        return MovieLevel.CASUAL
    if votes >= 100_000:
        return MovieLevel.CONOCEDOR
    if votes >= 20_000:
        return MovieLevel.LOCO
    return MovieLevel.CINEFILO


def _parse_int(value: str | None) -> int:
    """Convierte '2,000,000' o 'N/A' a entero."""
    if not value or value == "N/A":
        return 0
    digits = value.replace(",", "").strip()
    return int(digits) if digits.isdigit() else 0


def _parse_float(value: str | None) -> float:
    if not value or value == "N/A":
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def _parse_year(value: str | None) -> int:
    """OMDb devuelve '1999' o '1999–2003' (series); toma el primer año."""
    if not value or value == "N/A":
        return 0
    head = value[:4]
    return int(head) if head.isdigit() else 0


def _parse_genres(value: str | None) -> list[str]:
    if not value or value == "N/A":
        return []
    return [g.strip() for g in value.split(",") if g.strip()]


def download_poster(*, poster_url: str, imdb_id: str) -> str:
    """Descarga el poster de OMDb y lo guarda en storage local (HU-05).

    Returns:
        La ruta local del poster, o cadena vacía si la descarga falla.
    """
    try:
        response = requests.get(poster_url, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("No se pudo descargar el poster de %s: %s", imdb_id, exc)
        return ""

    path = f"posters/{imdb_id}.jpg"
    default_storage.save(path, ContentFile(response.content))
    return path


@transaction.atomic
def upsert_movie_from_omdb(
    *, payload: dict[str, Any], download_image: bool = True, title_es: str = ""
) -> bool:
    """Crea o actualiza una película desde un detalle OMDb. Devuelve True si fue creada.

    `title_es` (título en español, p. ej. de Wikidata) solo se escribe cuando se
    proporciona, para no sobrescribir una traducción existente con vacío.
    """
    imdb_id = payload["imdbID"]
    poster = payload.get("Poster", "")
    poster_url = poster if poster and poster != "N/A" else ""
    votes = _parse_int(payload.get("imdbVotes"))

    defaults = {
        "title": payload.get("Title", ""),
        "year": _parse_year(payload.get("Year")),
        "poster_url": poster_url,
        "genres": _parse_genres(payload.get("Genre")),
        "level": assign_level(votes=votes),
        "imdb_rating": _parse_float(payload.get("imdbRating")),
        "imdb_votes": votes,
    }
    if title_es:
        defaults["title_es"] = title_es

    movie, created = Movie.objects.update_or_create(imdb_id=imdb_id, defaults=defaults)

    if download_image and poster_url and not movie.poster_path:
        local_path = download_poster(poster_url=poster_url, imdb_id=imdb_id)
        if local_path:
            movie.poster_path = local_path
            movie.save(update_fields=["poster_path"])

    return created


def sync_movies(
    *,
    pages: int = 1,
    download_images: bool = True,
    terms: list[str] | None = None,
    min_year: int | None = None,
) -> SyncResult:
    """Sincroniza el catálogo desde OMDb por términos de búsqueda (HU-06).

    Sincronización manual e incremental: solo descarga películas que aún no
    están en el catálogo (omite las existentes sin consultar su detalle) y
    descarta las estrenadas antes de `min_year` (por defecto `OMDB_MIN_YEAR`).
    """
    client = OMDBClient()
    wikidata = WikidataClient()
    result = SyncResult()
    search_terms = terms or settings.OMDB_SEARCH_TERMS
    year_floor = min_year if min_year is not None else settings.OMDB_MIN_YEAR

    for term in search_terms:
        for page in range(1, pages + 1):
            for item in client.search(term=term, page=page):
                imdb_id = item.get("imdbID")
                if not imdb_id:
                    continue
                # Incremental: nunca volvemos a bajar una película ya catalogada.
                if Movie.objects.filter(imdb_id=imdb_id).exists():
                    result.skipped += 1
                    continue
                # Pre-filtro por año con el dato del resultado de búsqueda para
                # evitar gastar una llamada de detalle en películas antiguas.
                if _parse_year(item.get("Year")) < year_floor:
                    result.skipped += 1
                    continue
                try:
                    detail = client.detail(imdb_id=imdb_id)
                    # Confirmación definitiva del año con el detalle completo.
                    if _parse_year(detail.get("Year")) < year_floor:
                        result.skipped += 1
                        continue
                    # Título en español desde Wikidata (OMDb no traduce).
                    title_es = wikidata.spanish_title(imdb_id=imdb_id)
                    created = upsert_movie_from_omdb(
                        payload=detail,
                        download_image=download_images,
                        title_es=title_es,
                    )
                    if created:
                        result.created += 1
                    else:
                        result.updated += 1
                except (OMDBError, KeyError, ValueError) as exc:
                    msg = f"{term}/{imdb_id}: {exc}"
                    result.errors.append(msg)
                    logger.exception("Error sincronizando película %s", msg)

    logger.info(
        "Sync OMDb: %s creadas, %s actualizadas, %s omitidas, %s errores",
        result.created,
        result.updated,
        result.skipped,
        len(result.errors),
    )
    return result
