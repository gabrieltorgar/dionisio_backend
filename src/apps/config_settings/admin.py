"""Admin de configuración del juego (HU-35). Usa django-unfold (admin moderno)."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.config_settings.models import GameSetting, GameSettingHistory


@admin.register(GameSetting)
class GameSettingAdmin(ModelAdmin):
    list_display = ("key", "value", "updated_at")
    search_fields = ("key",)


@admin.register(GameSettingHistory)
class GameSettingHistoryAdmin(ModelAdmin):
    list_display = ("key", "value", "changed_by", "created_at")
    list_filter = ("key",)
    readonly_fields = ("key", "value", "changed_by", "created_at", "updated_at")

    def has_add_permission(self, _request) -> bool:
        return False
