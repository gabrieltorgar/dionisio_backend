"""Admin del motor de juego. Usa django-unfold (admin moderno)."""

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from apps.games.models import Game, Team, Turn


class TeamInline(TabularInline):
    model = Team
    extra = 0


@admin.register(Game)
class GameAdmin(ModelAdmin):
    list_display = ("id", "mode", "status", "started_at", "finished_at")
    list_filter = ("mode", "status")
    inlines = [TeamInline]


@admin.register(Turn)
class TurnAdmin(ModelAdmin):
    list_display = ("id", "game", "team", "scene_number", "status", "speed_bonus")
    list_filter = ("status", "speed_bonus")
