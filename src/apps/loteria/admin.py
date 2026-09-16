from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.loteria.models import Player, Room


@admin.register(Room)
class RoomAdmin(ModelAdmin):
    list_display = ("code", "status", "round_number", "drawn_count", "created_at")
    list_filter = ("status",)
    search_fields = ("code",)


@admin.register(Player)
class PlayerAdmin(ModelAdmin):
    list_display = ("name", "room", "is_winner", "connected", "created_at")
    list_filter = ("is_winner", "connected")
    search_fields = ("name", "room__code")
