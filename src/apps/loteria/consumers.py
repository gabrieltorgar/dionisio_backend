"""Consumer de WebSocket: la partida de lotería en tiempo real.

Un grupo de canales por sala (`loteria.<CÓDIGO>`). El anfitrión abre el canto
automático (una carta cada `draw_interval_ms`, pausable) y todos los jugadores
reciben la misma carta en el mismo instante.
"""

import asyncio
import hmac
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.exceptions import ValidationError

from apps.loteria.models import Player, Room, RoomStatus
from apps.loteria.selectors import card_payload, players_payload, state_payload
from apps.loteria.services import (
    claim_loteria,
    draw_next,
    leave_room,
    reset_to_lobby,
    set_mark,
    set_paused,
    start_round,
)

logger = logging.getLogger(__name__)

# Respiro entre "¡empieza!" y la primera carta, para que todos miren su tablero.
LEAD_IN_SECONDS = 1.5

CLOSE_UNKNOWN_ROOM = 4404
CLOSE_BAD_TOKEN = 4403


class LoteriaConsumer(AsyncJsonWebsocketConsumer):
    """`ws/loteria/<code>/?token=<host_token|player_token>`."""

    room_code: str
    group_name: str
    player_id: int | None = None
    is_host: bool = False
    _cantor: asyncio.Task | None = None

    # --- Ciclo de vida ---------------------------------------------------

    async def connect(self) -> None:
        self.room_code = self.scope["url_route"]["kwargs"]["code"].upper()
        token = self._query_token()

        identity = await self._resolve_identity(self.room_code, token)
        if identity is None:
            await self.close(code=CLOSE_UNKNOWN_ROOM)
            return
        self.is_host, self.player_id = identity
        if not self.is_host and self.player_id is None:
            await self.close(code=CLOSE_BAD_TOKEN)
            return

        self.group_name = f"loteria.{self.room_code}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        if self.player_id:
            await self._set_connected(self.player_id, True)
        await self.send_state()
        await self._fanout_players()

    async def disconnect(self, code: int) -> None:
        self._cancel_cantor()
        if getattr(self, "group_name", None):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        if self.player_id:
            await self._set_connected(self.player_id, False)
            await self._fanout_players()

    # --- Mensajes del cliente --------------------------------------------

    async def receive_json(self, content: dict, **kwargs) -> None:
        action = content.get("action")
        handlers = {
            "start": self._on_start,
            "pause": self._on_pause,
            "resume": self._on_resume,
            "draw": self._on_draw,
            "mark": self._on_mark,
            "claim": self._on_claim,
            "reset": self._on_reset,
            "leave": self._on_leave,
            "state": self._on_state,
            "ping": self._on_ping,
        }
        handler = handlers.get(action)
        if handler is None:
            await self.send_json(
                {"type": "error", "detail": f"Acción desconocida: {action}"}
            )
            return
        try:
            await handler(content)
        except ValidationError as exc:
            await self.send_json({"type": "error", "detail": " ".join(exc.messages)})
        except Exception:  # pragma: no cover - red de seguridad
            logger.exception("Error en la acción %s de lotería", action)
            await self.send_json({"type": "error", "detail": "Algo salió mal."})

    async def _on_ping(self, _content: dict) -> None:
        await self.send_json({"type": "pong"})

    async def _on_state(self, _content: dict) -> None:
        await self.send_state()

    async def _on_start(self, _content: dict) -> None:
        self._require_host()
        room = await self._get_room()
        await database_sync_to_async(start_round)(room)
        # Cada jugador recibe un tablero nuevo: que cada quien pida su estado.
        await self._fanout({"type": "round_started"})
        await self._refresh_all()
        self._start_cantor()

    async def _on_pause(self, _content: dict) -> None:
        self._require_host()
        room = await self._get_room()
        await database_sync_to_async(set_paused)(room, True)
        await self._fanout({"type": "paused"})

    async def _on_resume(self, _content: dict) -> None:
        self._require_host()
        room = await self._get_room()
        await database_sync_to_async(set_paused)(room, False)
        await self._fanout({"type": "resumed"})

    async def _on_draw(self, _content: dict) -> None:
        """Adelantar la carta a mano (el anfitrión no tiene que esperar)."""
        self._require_host()
        await self._draw_and_broadcast()

    async def _on_mark(self, content: dict) -> None:
        player = await self._require_player()
        index = content.get("index")
        marked = bool(content.get("marked", True))
        player = await database_sync_to_async(set_mark)(player, index, marked)
        await self.send_json({"type": "marks", "marked": sorted(set(player.marked))})
        await self._fanout_players()

    async def _on_claim(self, _content: dict) -> None:
        player = await self._require_player()
        try:
            winner = await database_sync_to_async(claim_loteria)(player)
        except ValidationError as exc:
            await self.send_json(
                {"type": "claim_rejected", "detail": " ".join(exc.messages)}
            )
            return
        self._cancel_cantor()
        await self._fanout(
            {
                "type": "loteria",
                "winner": {"id": winner.id, "name": winner.name},
            }
        )
        await self._refresh_all()

    async def _on_reset(self, _content: dict) -> None:
        self._require_host()
        self._cancel_cantor()
        room = await self._get_room()
        await database_sync_to_async(reset_to_lobby)(room)
        await self._fanout({"type": "lobby"})
        await self._refresh_all()

    async def _on_leave(self, _content: dict) -> None:
        if self.player_id:
            player = await self._require_player()
            await database_sync_to_async(leave_room)(player)
            self.player_id = None
            await self._fanout_players()
        await self.close()

    # --- Canto automático -------------------------------------------------

    def _start_cantor(self) -> None:
        self._cancel_cantor()
        self._cantor = asyncio.create_task(self._run_cantor())

    def _cancel_cantor(self) -> None:
        if self._cantor and not self._cantor.done():
            self._cantor.cancel()
        self._cantor = None

    async def _run_cantor(self) -> None:
        """Canta una carta cada `draw_interval_ms` mientras no esté en pausa."""
        try:
            await asyncio.sleep(LEAD_IN_SECONDS)
            while True:
                room = await self._get_room()
                if room.status != RoomStatus.PLAYING:
                    return
                if not room.paused:
                    if not await self._draw_and_broadcast():
                        return
                await asyncio.sleep(room.draw_interval_ms / 1000)
        except asyncio.CancelledError:  # pragma: no cover - cierre normal
            raise

    async def _draw_and_broadcast(self) -> bool:
        """Canta la siguiente carta. False si ya no quedan."""
        room = await self._get_room()
        card = await database_sync_to_async(draw_next)(room)
        if card is None:
            await self._fanout({"type": "deck_exhausted"})
            return False
        room = await self._get_room()
        await self._fanout(
            {
                "type": "card_drawn",
                "card": card_payload(card),
                "drawn_count": room.drawn_count,
                "remaining": room.remaining,
            }
        )
        return True

    # --- Difusión ---------------------------------------------------------

    async def send_state(self) -> None:
        payload = await self._state_for_me()
        await self.send_json({"type": "state", **payload})

    async def _fanout(self, payload: dict) -> None:
        await self.channel_layer.group_send(
            self.group_name, {"type": "broadcast", "payload": payload}
        )

    async def _refresh_all(self) -> None:
        await self.channel_layer.group_send(self.group_name, {"type": "refresh"})

    async def _fanout_players(self) -> None:
        room = await self._get_room()
        payload = await database_sync_to_async(players_payload)(room)
        await self._fanout({"type": "players", "players": payload})

    async def broadcast(self, event: dict) -> None:
        """Handler del grupo: reenvía el payload tal cual."""
        await self.send_json(event["payload"])

    async def refresh(self, _event: dict) -> None:
        """Handler del grupo: cada quien recalcula SU estado (tablero propio)."""
        await self.send_state()

    # --- Acceso a datos ---------------------------------------------------

    def _query_token(self) -> str:
        raw = self.scope.get("query_string", b"").decode()
        for part in raw.split("&"):
            key, _, value = part.partition("=")
            if key == "token":
                return value
        return ""

    def _require_host(self) -> None:
        if not self.is_host:
            raise ValidationError("Solo el anfitrión puede hacer eso.")

    async def _require_player(self) -> Player:
        if not self.player_id:
            raise ValidationError("Solo los jugadores pueden hacer eso.")
        return await self._get_player(self.player_id)

    @database_sync_to_async
    def _resolve_identity(
        self, code: str, token: str
    ) -> tuple[bool, int | None] | None:
        try:
            room = Room.objects.get(code=code)
        except Room.DoesNotExist:
            return None
        if token and hmac.compare_digest(token, room.host_token):
            return True, None
        player = room.players.filter(token=token).first() if token else None
        return False, player.id if player else None

    @database_sync_to_async
    def _get_room(self) -> Room:
        return Room.objects.select_related("winner").get(code=self.room_code)

    @database_sync_to_async
    def _get_player(self, player_id: int) -> Player:
        return Player.objects.select_related("room").get(pk=player_id)

    @database_sync_to_async
    def _set_connected(self, player_id: int, connected: bool) -> None:
        Player.objects.filter(pk=player_id).update(connected=connected)

    @database_sync_to_async
    def _state_for_me(self) -> dict:
        room = Room.objects.select_related("winner").get(code=self.room_code)
        player = (
            Player.objects.filter(pk=self.player_id).first() if self.player_id else None
        )
        return state_payload(room, player)
