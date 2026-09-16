"""Lecturas de solo consulta: arma los payloads que viajan por el WebSocket."""

from apps.loteria.cards import card_name
from apps.loteria.models import Player, Room


def card_payload(number: int | None) -> dict | None:
    """Carta serializada (número + nombre); el frontend resuelve la imagen."""
    if number is None:
        return None
    return {"number": number, "name": card_name(number)}


def room_payload(room: Room) -> dict:
    return {
        "code": room.code,
        "status": room.status,
        "round": room.round_number,
        "paused": room.paused,
        "drawn": room.drawn,
        "current": card_payload(room.current_card),
        "drawn_count": room.drawn_count,
        "remaining": room.remaining,
        "interval_ms": room.draw_interval_ms,
        "winner": (
            {"id": room.winner_id, "name": room.winner.name} if room.winner_id else None
        ),
    }


def player_public(player: Player) -> dict:
    """Lo que ven los demás: nombre y cuántas casillas lleva."""
    return {
        "id": player.id,
        "name": player.name,
        "marked_count": len(set(player.marked)),
        "is_winner": player.is_winner,
        "connected": player.connected,
    }


def player_private(player: Player) -> dict:
    """Lo que ve el propio jugador: su tablero y sus marcas."""
    return {
        "role": "player",
        "id": player.id,
        "name": player.name,
        "board": [card_payload(n) for n in player.board],
        "marked": sorted(set(player.marked)),
    }


def players_payload(room: Room) -> list[dict]:
    return [player_public(p) for p in room.players.all()]


def state_payload(room: Room, player: Player | None) -> dict:
    """Snapshot completo para quien se conecta (jugador o anfitrión)."""
    return {
        "room": room_payload(room),
        "players": players_payload(room),
        "you": player_private(player) if player else {"role": "host"},
    }
