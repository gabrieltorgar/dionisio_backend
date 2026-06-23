"""Rutas del catálogo."""

from rest_framework.routers import DefaultRouter

from apps.movies.views import CollectionViewSet, MovieViewSet

router = DefaultRouter()
router.register("movies", MovieViewSet, basename="movie")
router.register("collections", CollectionViewSet, basename="collection")

urlpatterns = router.urls
