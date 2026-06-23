"""Vistas del motor de juego (HU-13, HU-29).

Los endpoints de juego son públicos (sin cuenta para jugar, según el backlog).
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.games.models import Game, Turn
from apps.games.selectors import game_results
from apps.games.serializers import (
    GameCreateSerializer,
    GameResultTeamSerializer,
    GameSerializer,
    TurnCreateSerializer,
    TurnResultSerializer,
    TurnSerializer,
)
from apps.games.services import create_game, finish_game, register_turn_result


class GameViewSet(viewsets.GenericViewSet):
    """`/api/games/` — crear partida, consultar, crear turnos y registrar resultados."""

    permission_classes = [AllowAny]
    queryset = Game.objects.all()

    def create(self, request: Request) -> Response:
        serializer = GameCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            game = create_game(**serializer.validated_data)
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response(GameSerializer(game).data, status=status.HTTP_201_CREATED)

    def retrieve(self, _request: Request, pk: str | None = None) -> Response:
        game = get_object_or_404(Game, pk=pk)
        return Response(GameSerializer(game).data)

    @action(detail=True, methods=["post"])
    def turns(self, request: Request, pk: str | None = None) -> Response:
        """`POST /api/games/{id}/turns/` — crea un turno."""
        game = get_object_or_404(Game, pk=pk)
        serializer = TurnCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        turn = Turn.objects.create(
            game=game,
            team_id=serializer.validated_data["team_id"],
            movie_id=serializer.validated_data["movie_id"],
            scene_number=serializer.validated_data["scene_number"],
        )
        return Response(TurnSerializer(turn).data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["post"],
        url_path=r"turns/(?P<turn_id>[^/.]+)/result",
    )
    def turn_result(
        self, request: Request, pk: str | None = None, turn_id: str | None = None
    ) -> Response:
        """`POST /api/games/{id}/turns/{turn_id}/result/` — registra el resultado (HU-13)."""
        turn = get_object_or_404(Turn, pk=turn_id, game_id=pk)
        serializer = TurnResultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            turn = register_turn_result(turn=turn, **serializer.validated_data)
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response(TurnSerializer(turn).data)

    @action(detail=True, methods=["patch"])
    def finish(self, _request: Request, pk: str | None = None) -> Response:
        """`PATCH /api/games/{id}/finish/` — finaliza la partida (HU-13)."""
        game = get_object_or_404(Game, pk=pk)
        finish_game(game=game)
        return Response(GameSerializer(game).data)

    @action(detail=True, methods=["get"])
    def results(self, _request: Request, pk: str | None = None) -> Response:
        """`GET /api/games/{id}/results/` — ranking final con desglose (HU-29)."""
        game = get_object_or_404(Game, pk=pk)
        teams = game_results(game=game)
        return Response(GameResultTeamSerializer(teams, many=True).data)
