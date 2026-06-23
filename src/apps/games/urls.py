"""Rutas del motor de juego."""

from rest_framework.routers import DefaultRouter

from apps.games.views import GameViewSet

router = DefaultRouter()
router.register("games", GameViewSet, basename="game")

urlpatterns = router.urls
