"""Vistas del catálogo (HU-04, HU-07, HU-33, HU-34)."""

from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response

from apps.movies.filters import MovieFilter
from apps.movies.models import Collection, Movie
from apps.movies.permissions import IsStaffOrReadOnly
from apps.movies.selectors import list_active_collections, list_active_movies
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

    @action(detail=False, methods=["post"], permission_classes=[IsAdminUser])
    def sync(self, request: Request) -> Response:
        """`POST /api/movies/sync/` — dispara una sincronización OMDb (HU-33)."""
        pages = int(request.data.get("pages", 1))
        result = sync_movies(pages=pages, download_images=True)
        return Response(
            {
                "created": result.created,
                "updated": result.updated,
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
