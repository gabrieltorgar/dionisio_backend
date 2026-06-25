"""Cliente de Wikidata para enriquecer el catálogo con datos en español (HU-06).

OMDb no entrega traducciones. Wikidata expone datos en dominio público (CC0) y
permite mapear el identificador IMDb (propiedad `P345`) a la etiqueta en español
del título y a su artículo en la Wikipedia en español, sin restricciones de
almacenamiento.

La política de uso de Wikimedia exige un `User-Agent` descriptivo con contacto;
se configura vía `WIKIDATA_USER_AGENT`.
"""

import logging
from urllib.parse import unquote

import requests
from django.conf import settings

logger = logging.getLogger("apps")

_TIMEOUT_SECONDS = 20

# Devuelve la etiqueta en español del título y, como respaldo, el artículo de la
# Wikipedia en español asociado al ítem identificado por su IMDb ID (P345).
_SPARQL_SPANISH_TITLE = (
    "SELECT ?titleEs ?article WHERE {{ "
    '?item wdt:P345 "{imdb_id}". '
    'OPTIONAL {{ ?item rdfs:label ?titleEs FILTER(LANG(?titleEs) = "es") }} '
    "OPTIONAL {{ "
    "?article schema:about ?item ; "
    "schema:isPartOf <https://es.wikipedia.org/> . "
    "}} "
    "}} LIMIT 1"
)


class WikidataClient:
    """Cliente mínimo del SPARQL endpoint de Wikidata."""

    def __init__(
        self,
        *,
        sparql_url: str | None = None,
        user_agent: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.sparql_url = sparql_url or settings.WIKIDATA_SPARQL_URL
        self.user_agent = user_agent or settings.WIKIDATA_USER_AGENT
        self.session = session or requests.Session()

    def spanish_title(self, *, imdb_id: str) -> str:
        """Devuelve el título en español de una película, o cadena vacía.

        Prioriza la etiqueta `es` de Wikidata; si no existe, usa el título del
        artículo de la Wikipedia en español. Cualquier fallo se registra y
        devuelve cadena vacía para no interrumpir la sincronización.
        """
        if not imdb_id:
            return ""

        query = _SPARQL_SPANISH_TITLE.format(imdb_id=imdb_id)
        try:
            response = self.session.get(
                self.sparql_url,
                params={"query": query, "format": "json"},
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "application/sparql-results+json",
                },
                timeout=_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            bindings = response.json().get("results", {}).get("bindings", [])
        except (requests.RequestException, ValueError) as exc:
            logger.warning("Wikidata sin título ES para %s: %s", imdb_id, exc)
            return ""

        if not bindings:
            return ""

        row = bindings[0]
        label = row.get("titleEs", {}).get("value", "").strip()
        if label:
            return label
        return self._title_from_article(row.get("article", {}).get("value", ""))

    @staticmethod
    def _title_from_article(url: str) -> str:
        """Extrae un título legible del slug de un artículo de Wikipedia.

        `.../wiki/El_club_de_la_lucha` → `El club de la lucha`. Quita la
        desambiguación entre paréntesis (`Origen_(película)` → `Origen`).
        """
        if not url:
            return ""
        slug = url.rsplit("/", 1)[-1]
        title = unquote(slug).replace("_", " ").strip()
        if title.endswith(")") and "(" in title:
            title = title[: title.rfind("(")].strip()
        return title
