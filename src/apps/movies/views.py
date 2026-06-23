"""Vistas del catálogo (HU-04, HU-07, HU-33, HU-34)."""

from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response

from apps.movies.filters import MovieFilter
from apps.movies.models import Collection, Movie
from apps.movies.permissions import IsStaffOrReadOnly
from apps.movies.selectors import (
    list_active_collections,
    list_active_movies,
    movie_deck,
)
from apps.movies.serializers import (
    CollectionSerializer,
    MovieAdminSerializer,
    MovieSerializer,
)
from apps.movies.services import sync_movies


class MovieViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """`/api/movies/` — listado público con filtros; edición para staff (HU-04, HU-33)."""

    filterset_class = MovieFilter
    permission_classes = [IsStaffOrReadOnly]

    def get_queryset(self):
        # El staff ve todo el catálogo; el público solo películas activas.
        if self.request.user and self.request.user.is_staff:
            return Movie.objects.all()
        return list_active_movies()

    def get_serializer_class(self):
        if self.action in {"update", "partial_update"}:
            return MovieAdminSerializer
        return MovieSerializer

    @action(detail=False, methods=["get"])
    def deck(self, request: Request) -> Response:
        """`GET /api/movies/deck/` — mazo aleatorio para una partida.

        Query params: `level`, `genre`, `collection`, `count` (1-100),
        `exclude` (imdb_ids separados por coma, ya usados recientemente).
        Maximiza la dispersión entre partidas (HU-04).
        """
        count = max(1, min(int(request.query_params.get("count", 30)), 100))
        exclude = [x for x in request.query_params.get("exclude", "").split(",") if x]
        movies = movie_deck(
            level=request.query_params.get("level"),
            genre=request.query_params.get("genre"),
            collection=request.query_params.get("collection"),
            exclude_ids=exclude,
            count=count,
        )
        return Response(MovieSerializer(movies, many=True).data)

    @action(detail=False, methods=["post"], permission_classes=[IsAdminUser])
    def sync(self, request: Request) -> Response:
        """`POST /api/movies/sync/` — dispara una sincronización OMDb manual (HU-33).

        Incremental: omite las películas ya catalogadas y las anteriores al
        año mínimo (`OMDB_MIN_YEAR`, sobreescribible con `min_year`).
        """
        pages = int(request.data.get("pages", 1))
        min_year = request.data.get("min_year")
        result = sync_movies(
            pages=pages,
            download_images=True,
            min_year=int(min_year) if min_year is not None else None,
        )
        return Response(
            {
                "created": result.created,
                "updated": result.updated,
                "skipped": result.skipped,
                "errors": result.errors,
            }
        )


class CollectionViewSet(viewsets.ModelViewSet):
    """`/api/collections/` — CRUD de colecciones; lectura pública (HU-07, HU-34)."""

    serializer_class = CollectionSerializer
    permission_classes = [IsStaffOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        if self.request.user and self.request.user.is_staff:
            return Collection.objects.all()
        return list_active_collections()
