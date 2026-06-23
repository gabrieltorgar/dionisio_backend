"""Factories del catálogo."""

import factory

from apps.movies.models import Collection, Movie, MovieLevel


class MovieFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Movie

    imdb_id = factory.Sequence(lambda n: f"tt{1000000 + n}")
    title = factory.Sequence(lambda n: f"Movie {n}")
    title_es = factory.Sequence(lambda n: f"Película {n}")
    year = 2020
    poster_url = "https://m.media-amazon.com/images/poster.jpg"
    genres = factory.List(["Acción"])
    level = MovieLevel.CASUAL
    collections = factory.List([])
    imdb_rating = 8.0
    imdb_votes = 600_000
    is_active = True


class CollectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Collection

    name = factory.Sequence(lambda n: f"Colección {n}")
    slug = factory.Sequence(lambda n: f"coleccion-{n}")
    emoji = "🎬"
    is_active = True
