"""Tests del catálogo (HU-04, HU-06, HU-07)."""

import pytest
from django.urls import reverse

from apps.movies import services
from apps.movies.models import Movie, MovieLevel
from apps.movies.services import assign_level, sync_movies, upsert_movie_from_omdb
from apps.movies.tests.factories import CollectionFactory, MovieFactory


class _FakeOMDBClient:
    """Cliente OMDb falso para sincronización: registra los detalles pedidos."""

    def __init__(self, *, search_items, details):
        self._search_items = search_items
        self._details = details
        self.detail_calls: list[str] = []

    def search(self, *, term, page=1, media_type="movie"):  # noqa: ARG002
        return self._search_items if page == 1 else []

    def detail(self, *, imdb_id):
        self.detail_calls.append(imdb_id)
        return self._details[imdb_id]


class _FakeWikidata:
    """Cliente Wikidata falso: mapea imdb_id → título en español."""

    def __init__(self, mapping=None):
        self._mapping = mapping or {}

    def spanish_title(self, *, imdb_id):
        return self._mapping.get(imdb_id, "")


def _patch_clients(monkeypatch, *, omdb, wikidata=None):
    """Inyecta clientes falsos de OMDb y Wikidata en el módulo de servicios."""
    monkeypatch.setattr(services, "OMDBClient", lambda *a, **k: omdb)
    monkeypatch.setattr(
        services, "WikidataClient", lambda *a, **k: wikidata or _FakeWikidata()
    )


@pytest.mark.parametrize(
    ("votes", "expected"),
    [
        (600_000, MovieLevel.CASUAL),
        (500_001, MovieLevel.CASUAL),
        (200_000, MovieLevel.CONOCEDOR),
        (100_000, MovieLevel.CONOCEDOR),
        (50_000, MovieLevel.LOCO),
        (20_000, MovieLevel.LOCO),
        (5_000, MovieLevel.CINEFILO),
    ],
)
def test_assign_level_by_votes(votes, expected):
    assert assign_level(votes=votes) == expected


@pytest.mark.django_db
def test_upsert_movie_is_idempotent_by_imdb_id():
    payload = {
        "imdbID": "tt0137523",
        "Title": "Fight Club",
        "Year": "1999",
        "Genre": "Drama, Thriller",
        "imdbRating": "8.8",
        "imdbVotes": "2,300,000",
        "Poster": "https://m.media-amazon.com/images/fc.jpg",
    }
    created_first = upsert_movie_from_omdb(payload=payload, download_image=False)
    created_second = upsert_movie_from_omdb(payload=payload, download_image=False)

    assert created_first is True
    assert created_second is False
    assert Movie.objects.filter(imdb_id="tt0137523").count() == 1
    movie = Movie.objects.get(imdb_id="tt0137523")
    assert movie.title == "Fight Club"
    assert movie.year == 1999
    assert movie.imdb_votes == 2_300_000
    assert movie.level == MovieLevel.CASUAL
    assert "Thriller" in movie.genres


def _detail(imdb_id, title, year, votes="2,300,000"):
    return {
        "imdbID": imdb_id,
        "Title": title,
        "Year": year,
        "Genre": "Drama",
        "imdbRating": "8.0",
        "imdbVotes": votes,
        "Poster": "N/A",
    }


@pytest.mark.django_db
def test_sync_skips_movies_already_in_catalog(monkeypatch, settings):
    """No vuelve a descargar ni consultar el detalle de una película existente."""
    settings.OMDB_SEARCH_TERMS = ["term"]
    settings.OMDB_MIN_YEAR = 1990
    MovieFactory(imdb_id="tt_existing", year=2000)

    fake = _FakeOMDBClient(
        search_items=[
            {"imdbID": "tt_existing", "Year": "2000"},
            {"imdbID": "tt_new", "Year": "2005"},
        ],
        details={"tt_new": _detail("tt_new", "New Movie", "2005")},
    )
    _patch_clients(monkeypatch, omdb=fake)

    result = sync_movies(pages=1, download_images=False)

    assert result.created == 1
    assert result.skipped == 1
    assert fake.detail_calls == ["tt_new"]  # nunca se pidió el detalle del existente
    assert Movie.objects.count() == 2


@pytest.mark.django_db
def test_sync_skips_movies_before_min_year(monkeypatch, settings):
    """Descarta películas anteriores al año mínimo sin gastar llamada de detalle."""
    settings.OMDB_SEARCH_TERMS = ["term"]
    settings.OMDB_MIN_YEAR = 1990

    fake = _FakeOMDBClient(
        search_items=[
            {"imdbID": "tt_old", "Year": "1985"},
            {"imdbID": "tt_recent", "Year": "1999"},
        ],
        details={"tt_recent": _detail("tt_recent", "Recent", "1999")},
    )
    _patch_clients(monkeypatch, omdb=fake)

    result = sync_movies(pages=1, download_images=False)

    assert result.created == 1
    assert result.skipped == 1
    assert fake.detail_calls == ["tt_recent"]
    assert not Movie.objects.filter(imdb_id="tt_old").exists()


@pytest.mark.django_db
def test_sync_min_year_override(monkeypatch, settings):
    """El parámetro min_year sobreescribe OMDB_MIN_YEAR."""
    settings.OMDB_SEARCH_TERMS = ["term"]
    settings.OMDB_MIN_YEAR = 1990

    fake = _FakeOMDBClient(
        search_items=[{"imdbID": "tt_2003", "Year": "2003"}],
        details={"tt_2003": _detail("tt_2003", "Y2003", "2003")},
    )
    _patch_clients(monkeypatch, omdb=fake)

    result = sync_movies(pages=1, download_images=False, min_year=2010)

    assert result.created == 0
    assert result.skipped == 1
    assert fake.detail_calls == []


@pytest.mark.django_db
def test_sync_sets_spanish_title_from_wikidata(monkeypatch, settings):
    """El título ES de Wikidata se guarda en title_es (y manda en display_title)."""
    settings.OMDB_SEARCH_TERMS = ["term"]
    settings.OMDB_MIN_YEAR = 1990

    omdb = _FakeOMDBClient(
        search_items=[{"imdbID": "tt0137523", "Year": "1999"}],
        details={"tt0137523": _detail("tt0137523", "Fight Club", "1999")},
    )
    wikidata = _FakeWikidata({"tt0137523": "El club de la lucha"})
    _patch_clients(monkeypatch, omdb=omdb, wikidata=wikidata)

    result = sync_movies(pages=1, download_images=False)

    assert result.created == 1
    movie = Movie.objects.get(imdb_id="tt0137523")
    assert movie.title == "Fight Club"
    assert movie.title_es == "El club de la lucha"
    assert movie.display_title == "El club de la lucha"


@pytest.mark.django_db
def test_sync_without_spanish_title_leaves_title_es_empty(monkeypatch, settings):
    """Sin título ES en Wikidata, title_es queda vacío y display_title usa el original.

    (Camino de respaldo del sync.)
    """
    settings.OMDB_SEARCH_TERMS = ["term"]
    settings.OMDB_MIN_YEAR = 1990

    omdb = _FakeOMDBClient(
        search_items=[{"imdbID": "tt_only_en", "Year": "2001"}],
        details={"tt_only_en": _detail("tt_only_en", "Only English", "2001")},
    )
    _patch_clients(monkeypatch, omdb=omdb)  # Wikidata falso devuelve ""

    sync_movies(pages=1, download_images=False)

    movie = Movie.objects.get(imdb_id="tt_only_en")
    assert movie.title_es == ""
    assert movie.display_title == "Only English"


def test_wikidata_title_from_article_strips_disambiguation():
    """El respaldo por artículo de Wikipedia decodifica el slug y quita paréntesis."""
    from apps.movies.wikidata import WikidataClient

    parse = WikidataClient._title_from_article
    url = "https://es.wikipedia.org/wiki/El_club_de_la_lucha"
    assert parse(url) == "El club de la lucha"
    assert parse("https://es.wikipedia.org/wiki/Origen_(pel%C3%ADcula)") == "Origen"
    assert parse("") == ""


@pytest.mark.django_db
def test_movies_endpoint_returns_attribution_and_filters_by_level(api_client):
    MovieFactory(level=MovieLevel.CASUAL)
    MovieFactory(level=MovieLevel.CINEFILO)

    url = reverse("movie-list")
    response = api_client.get(url, {"level": MovieLevel.CINEFILO})

    assert response.status_code == 200
    results = response.data["results"]
    assert len(results) == 1
    assert results[0]["attribution"] == {
        "source": "OMDb",
        "source_url": "https://www.omdbapi.com",
    }


@pytest.mark.django_db
def test_collections_endpoint_returns_only_active(api_client):
    CollectionFactory(is_active=True)
    CollectionFactory(is_active=False)

    response = api_client.get(reverse("collection-list"))

    assert response.status_code == 200
    assert response.data["count"] == 1
