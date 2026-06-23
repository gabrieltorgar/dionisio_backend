"""Cliente HTTP de OMDb (omdbapi.com) (HU-06).

OMDb expone dos modos: búsqueda por término (`s`, paginada) y detalle por
identificador IMDb (`i`) o título (`t`). No hay endpoint de "populares", por lo
que la sincronización se hace buscando por una lista de términos configurable.
"""

import logging
import time
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger("apps")

_MAX_RETRIES = 4
_BACKOFF_BASE_SECONDS = 1.0


class OMDBError(Exception):
    """Error al comunicarse con OMDb."""


class OMDBClient:
    """Cliente mínimo de la API de OMDb."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.api_key = api_key or settings.OMDB_API_KEY
        self.base_url = (base_url or settings.OMDB_API_BASE_URL).rstrip("/")
        self.session = session or requests.Session()

    def _get(self, params: dict[str, Any]) -> dict[str, Any]:
        """GET a OMDb con reintento básico.

        OMDb responde siempre 200 con `{"Response": "True"|"False"}`.

        Raises:
            OMDBError: si la respuesta es de error o se agotan los reintentos.
        """
        query = {"apikey": self.api_key, "r": "json", "v": 1, **params}

        last_error = "desconocido"
        for attempt in range(_MAX_RETRIES):
            try:
                response = self.session.get(self.base_url + "/", params=query, timeout=15)
            except requests.RequestException as exc:
                last_error = str(exc)
                time.sleep(_BACKOFF_BASE_SECONDS * 2**attempt)
                continue

            if response.status_code != 200:
                last_error = f"HTTP {response.status_code}"
                time.sleep(_BACKOFF_BASE_SECONDS * 2**attempt)
                continue

            data = response.json()
            if data.get("Response") == "False":
                error = data.get("Error", "")
                # Límite diario alcanzado: reintentar no ayuda.
                if "limit" in error.lower():
                    raise OMDBError(f"OMDb: {error}")
                # "Movie not found!" / "Too many results." → error de consulta.
                raise OMDBError(f"OMDb: {error}")
            return data

        raise OMDBError(f"OMDb sin respuesta válida: {last_error}")

    def search(
        self,
        *,
        term: str,
        page: int = 1,
        media_type: str = "movie",
    ) -> list[dict[str, Any]]:
        """Busca por término. Devuelve la lista `Search` (puede estar vacía)."""
        try:
            data = self._get({"s": term, "page": page, "type": media_type})
        except OMDBError as exc:
            logger.warning("Búsqueda OMDb '%s' p%s falló: %s", term, page, exc)
            return []
        return data.get("Search", [])

    def detail(self, *, imdb_id: str) -> dict[str, Any]:
        """Detalle completo por ID de IMDb (incluye Genre, imdbRating, imdbVotes)."""
        return self._get({"i": imdb_id, "plot": "short"})
