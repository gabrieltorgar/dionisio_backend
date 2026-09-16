"""Rutas de WebSocket de la lotería."""

from django.urls import re_path

from apps.loteria.consumers import LoteriaConsumer

websocket_urlpatterns = [
    re_path(r"^ws/loteria/(?P<code>[A-Za-z0-9]{6})/$", LoteriaConsumer.as_asgi()),
]
