"""Serializers de entrada/salida del alta de salas de lotería."""

from rest_framework import serializers

from apps.loteria.services import MAX_INTERVAL_MS, MIN_INTERVAL_MS


class RoomCreateSerializer(serializers.Serializer):
    draw_interval_ms = serializers.IntegerField(
        required=False,
        default=4000,
        min_value=MIN_INTERVAL_MS,
        max_value=MAX_INTERVAL_MS,
    )


class JoinSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=20)
