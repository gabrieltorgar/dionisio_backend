"""Serializers de configuración del juego (HU-09, HU-35)."""

from rest_framework import serializers

from apps.config_settings.models import GameSetting, GameSettingHistory


class GameSettingsSerializer(serializers.Serializer):
    """Salida pública de los parámetros resueltos (HU-09)."""

    turn_duration_seconds = serializers.IntegerField()
    steal_window_seconds = serializers.IntegerField()
    speed_bonus_threshold_seconds = serializers.IntegerField()
    special_round_interval = serializers.IntegerField()
    lightning_round_duration_seconds = serializers.IntegerField()


class GameSettingWriteSerializer(serializers.Serializer):
    """Entrada para sobreescribir un parámetro (HU-35)."""

    key = serializers.CharField()
    value = serializers.IntegerField(min_value=1)

    def validate_key(self, value: str) -> str:
        if value not in GameSetting.allowed_keys():
            raise serializers.ValidationError(f"Parámetro desconocido: {value}")
        return value


class GameSettingHistorySerializer(serializers.ModelSerializer):
    """Historial de cambios (HU-35)."""

    changed_by = serializers.StringRelatedField()

    class Meta:
        model = GameSettingHistory
        fields = ["id", "key", "value", "changed_by", "created_at"]
