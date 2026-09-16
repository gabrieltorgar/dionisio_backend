"""Lógica de la lotería: crear sala, unirse, cantar cartas y validar la lotería.

Todo el estado de juego se decide aquí (capa de servicio); las vistas REST y el
consumer de WebSocket solo orquestan.
"""

import secrets

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.loteria.cards import BOARD_SIZE, DECK_SIZE
from apps.loteria.models import Player, Room, RoomStatus

# Alfabeto sin caracteres ambiguos (sin O/0, I/1) para dictar el código en voz alta.
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 6
MAX_PLAYERS = 20
MIN_INTERVAL_MS = 1500
MAX_INTERVAL_MS = 15000


def generate_code() -> str:
    """Código de sala de 6 caracteres que no esté en uso."""
    for _ in range(50):
        code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))
        if not Room.objects.filter(code=code).exists():
            return code
    raise ValidationError("No se pudo generar un código de sala libre.")


def shuffled_deck() -> list[int]:
    """Los 54 números barajados (sin repetir)."""
    deck = list(range(1, DECK_SIZE + 1))
    rng = secrets.SystemRandom()
    rng.shuffle(deck)
    return deck


def random_board() -> list[int]:
    """16 cartas distintas para una cuadrícula 4×4."""
    rng = secrets.SystemRandom()
    return rng.sample(range(1, DECK_SIZE + 1), BOARD_SIZE)


@transaction.atomic
def create_room(draw_interval_ms: int = 4000) -> Room:
    """Crea una sala en modo lobby con la baraja lista."""
    interval = max(MIN_INTERVAL_MS, min(MAX_INTERVAL_MS, int(draw_interval_ms)))
    return Room.objects.create(
        code=generate_code(),
        host_token=secrets.token_hex(16),
        deck=shuffled_deck(),
        draw_interval_ms=interval,
    )


@transaction.atomic
def join_room(code: str, name: str) -> Player:
    """Une a un jugador a la sala y le reparte un tablero nuevo."""
    clean_name = (name or "").strip()
    if not clean_name:
        raise ValidationError("Escribe tu nombre para entrar.")

    try:
        room = Room.objects.select_for_update().get(code=code.strip().upper())
    except Room.DoesNotExist as exc:
        raise ValidationError("No existe una sala con ese código.") from exc

    if room.status == RoomStatus.PLAYING:
        raise ValidationError("La partida ya empezó; espera a la siguiente ronda.")
    if room.players.count() >= MAX_PLAYERS:
        raise ValidationError("La sala está llena.")
    if room.players.filter(name__iexact=clean_name).exists():
        raise ValidationError("Ya hay alguien con ese nombre en la sala.")

    return Player.objects.create(
        room=room,
        name=clean_name,
        token=secrets.token_hex(16),
        board=random_board(),
    )


@transaction.atomic
def start_round(room: Room) -> Room:
    """Arranca (o rearranca) la partida: rebaraja y reparte tableros nuevos."""
    if room.players.count() == 0:
        raise ValidationError("No hay jugadores en la sala.")

    room.deck = shuffled_deck()
    room.drawn_count = 0
    room.paused = False
    room.status = RoomStatus.PLAYING
    room.winner = None
    room.save(update_fields=["deck", "drawn_count", "paused", "status", "winner"])

    for player in room.players.all():
        player.board = random_board()
        player.marked = []
        player.is_winner = False
        player.save(update_fields=["board", "marked", "is_winner"])
    return room


@transaction.atomic
def draw_next(room: Room) -> int | None:
    """Canta la siguiente carta. Devuelve None si ya se acabó la baraja."""
    room = Room.objects.select_for_update().get(pk=room.pk)
    if room.status != RoomStatus.PLAYING or room.drawn_count >= len(room.deck):
        return None
    room.drawn_count += 1
    room.save(update_fields=["drawn_count"])
    return room.deck[room.drawn_count - 1]


@transaction.atomic
def set_mark(player: Player, index: int, marked: bool) -> Player:
    """Marca o desmarca una casilla del tablero (0–15)."""
    if not 0 <= int(index) < BOARD_SIZE:
        raise ValidationError("Casilla fuera del tablero.")
    player = Player.objects.select_for_update().get(pk=player.pk)
    current = set(player.marked)
    if marked:
        current.add(int(index))
    else:
        current.discard(int(index))
    player.marked = sorted(current)
    player.save(update_fields=["marked"])
    return player


@transaction.atomic
def claim_loteria(player: Player) -> Player:
    """Valida el grito de "¡lotería!".

    Se comprueba contra lo realmente cantado: si el jugador marcó cartas que no
    han salido, se rechaza con un motivo y la partida sigue.
    """
    player = Player.objects.select_for_update().select_related("room").get(pk=player.pk)
    room = player.room

    if room.status != RoomStatus.PLAYING:
        raise ValidationError("La partida no está en curso.")
    if room.winner_id:
        raise ValidationError("Alguien cantó lotería antes que tú.")
    if not player.is_full:
        faltan = BOARD_SIZE - len(set(player.marked))
        raise ValidationError(f"Aún te faltan {faltan} casillas por marcar.")

    drawn = set(room.deck[: room.drawn_count])
    invalid = [i for i in player.marked if player.board[i] not in drawn]
    if invalid:
        raise ValidationError("Marcaste cartas que todavía no han salido.")

    player.is_winner = True
    player.save(update_fields=["is_winner"])
    room.winner = player
    room.status = RoomStatus.FINISHED
    room.paused = True
    room.save(update_fields=["winner", "status", "paused"])
    return player


@transaction.atomic
def reset_to_lobby(room: Room) -> Room:
    """Vuelve a la sala de espera para jugar otra ronda con los mismos jugadores."""
    room.status = RoomStatus.LOBBY
    room.drawn_count = 0
    room.paused = False
    room.winner = None
    room.round_number += 1
    room.deck = shuffled_deck()
    room.save(
        update_fields=[
            "status",
            "drawn_count",
            "paused",
            "winner",
            "round_number",
            "deck",
        ]
    )
    room.players.update(marked=[], is_winner=False)
    return room


@transaction.atomic
def set_paused(room: Room, paused: bool) -> Room:
    room.paused = bool(paused)
    room.save(update_fields=["paused"])
    return room


def leave_room(player: Player) -> None:
    """Saca al jugador de la sala (al salir explícitamente, no al desconectarse)."""
    player.delete()
