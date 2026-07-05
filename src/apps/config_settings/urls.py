"""Rutas de configuración del juego."""

from django.urls import path

from apps.config_settings.views import (
    GameSettingsAdminView,
    GameSettingsHistoryView,
    GameSettingsView,
)

urlpatterns = [
    path("game-settings/", GameSettingsView.as_view(), name="game-settings"),
    path(
        "game-settings/admin/",
        GameSettingsAdminView.as_view(),
        name="game-settings-admin",
    ),
    path(
        "game-settings/history/",
        GameSettingsHistoryView.as_view(),
        name="game-settings-history",
    ),
]
