"""Vistas de configuración del juego (HU-09, HU-35)."""

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.config_settings.models import GameSettingHistory
from apps.config_settings.serializers import (
    GameSettingHistorySerializer,
    GameSettingsSerializer,
    GameSettingWriteSerializer,
)
from apps.config_settings.services import (
    get_game_settings,
    reset_game_setting,
    set_game_setting,
)


class GameSettingsView(APIView):
    """`GET /api/config/game-settings/` — parámetros resueltos, público (HU-09)."""

    permission_classes = [AllowAny]

    def get(self, _request: Request) -> Response:
        data = GameSettingsSerializer(get_game_settings()).data
        return Response(data)


class GameSettingsAdminView(APIView):
    """Backoffice: sobreescribir y resetear parámetros (HU-35)."""

    permission_classes = [IsAdminUser]

    def post(self, request: Request) -> Response:
        serializer = GameSettingWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            set_game_setting(
                key=serializer.validated_data["key"],
                value=serializer.validated_data["value"],
                user=request.user,
            )
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response(GameSettingsSerializer(get_game_settings()).data)

    def delete(self, request: Request) -> Response:
        key = request.query_params.get("key", "")
        reset_game_setting(key=key, user=request.user)
        return Response(GameSettingsSerializer(get_game_settings()).data)


class GameSettingsHistoryView(APIView):
    """`GET /api/config/game-settings/history/` — historial (HU-35)."""

    permission_classes = [IsAdminUser]

    def get(self, _request: Request) -> Response:
        history = GameSettingHistory.objects.all()[:100]
        return Response(GameSettingHistorySerializer(history, many=True).data)
