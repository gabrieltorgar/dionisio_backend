"""Tests del catálogo (HU-04, HU-06, HU-07)."""

import pytest
from django.urls import reverse

from apps.movies.models import Movie, MovieLevel
from apps.movies.services import assign_level, upsert_movie_from_omdb
from apps.movies.tests.factories import CollectionFactory, MovieFactory


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
