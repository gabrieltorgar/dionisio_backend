"""Rutas REST de la lotería."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.loteria.views import CardsView, RoomViewSet

router = DefaultRouter()
router.register("loteria/rooms", RoomViewSet, basename="loteria-room")

urlpatterns = [
    path("loteria/cards/", CardsView.as_view(), name="loteria-cards"),
    *router.urls,
]
