"""Endpoints REST de la lotería: crear sala, unirse y consultar.

La partida en vivo viaja por WebSocket (`apps.loteria.consumers`); aquí solo
está el apretón de manos que entrega el código y los tokens.
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.loteria.cards import CARDS
from apps.loteria.models import Room
from apps.loteria.selectors import player_private, players_payload, room_payload
from apps.loteria.serializers import JoinSerializer, RoomCreateSerializer
from apps.loteria.services import create_room, join_room


class CardsView(APIView):
    """`/api/loteria/cards/` — catálogo de las 54 cartas (número + nombre)."""

    permission_classes = [AllowAny]

    def get(self, _request: Request) -> Response:
        return Response({"count": len(CARDS), "results": list(CARDS)})


class RoomViewSet(viewsets.GenericViewSet):
    """`/api/loteria/rooms/` — crear sala, consultarla y unirse con el código."""

    permission_classes = [AllowAny]
    queryset = Room.objects.all()
    lookup_field = "code"
    lookup_value_regex = "[A-Za-z0-9]{6}"

    def create(self, request: Request) -> Response:
        serializer = RoomCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            room = create_room(**serializer.validated_data)
        except DjangoValidationError as exc:
            return Response(
                {"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {
                "host_token": room.host_token,
                "room": room_payload(room),
                "players": [],
            },
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, _request: Request, code: str | None = None) -> Response:
        room = get_object_or_404(Room, code=(code or "").upper())
        return Response({"room": room_payload(room), "players": players_payload(room)})

    @action(detail=True, methods=["post"])
    def join(self, request: Request, code: str | None = None) -> Response:
        serializer = JoinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            player = join_room(code or "", serializer.validated_data["name"])
        except DjangoValidationError as exc:
            return Response(
                {"detail": " ".join(exc.messages)}, status=status.HTTP_400_BAD_REQUEST
            )
        room = player.room
        return Response(
            {
                "player_token": player.token,
                "room": room_payload(room),
                "players": players_payload(room),
                "you": player_private(player),
            },
            status=status.HTTP_201_CREATED,
        )
