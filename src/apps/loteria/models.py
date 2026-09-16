"""Modelos de la lotería mexicana multijugador en tiempo real.

Una `Room` es una sala con código de 6 caracteres. El estado vive en la base de
datos (no solo en memoria) para que un jugador pueda recargar o perder la señal
y reincorporarse sin perder su tablero ni sus marcas.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.loteria.cards import BOARD_SIZE
from common.models import TimestampedModel


class RoomStatus(models.TextChoices):
    LOBBY = "lobby", _("Esperando jugadores")
    PLAYING = "playing", _("En curso")
    FINISHED = "finished", _("Terminada")


class Room(TimestampedModel):
    """Sala de lotería identificada por un código alfanumérico de 6."""

    code = models.CharField(_("código"), max_length=6, unique=True, db_index=True)
    host_token = models.CharField(_("token del anfitrión"), max_length=32)
    status = models.CharField(
        _("estado"),
        max_length=10,
        choices=RoomStatus.choices,
        default=RoomStatus.LOBBY,
        db_index=True,
    )
    # Orden barajado de los 54 números; se rebaraja en cada ronda.
    deck = models.JSONField(_("baraja"), default=list)
    drawn_count = models.PositiveIntegerField(_("cartas cantadas"), default=0)
    draw_interval_ms = models.PositiveIntegerField(
        _("intervalo entre cartas (ms)"), default=4000
    )
    paused = models.BooleanField(_("pausada"), default=False)
    round_number = models.PositiveIntegerField(_("ronda"), default=1)
    winner = models.ForeignKey(
        "loteria.Player",
        verbose_name=_("ganador"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="won_rooms",
    )

    class Meta:
        verbose_name = _("sala de lotería")
        verbose_name_plural = _("salas de lotería")
        db_table = "loteria_room"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Sala {self.code} ({self.status})"

    @property
    def drawn(self) -> list[int]:
        """Cartas ya cantadas, en orden."""
        return list(self.deck[: self.drawn_count])

    @property
    def current_card(self) -> int | None:
        """Última carta cantada, o None si aún no empieza."""
        return self.deck[self.drawn_count - 1] if self.drawn_count else None

    @property
    def remaining(self) -> int:
        return max(0, len(self.deck) - self.drawn_count)


class Player(TimestampedModel):
    """Un jugador dentro de una sala, con su tablero 4×4 y sus marcas."""

    room = models.ForeignKey(
        Room,
        verbose_name=_("sala"),
        on_delete=models.CASCADE,
        related_name="players",
    )
    name = models.CharField(_("nombre"), max_length=20)
    token = models.CharField(_("token"), max_length=32, db_index=True)
    # 16 números de carta, en el orden de la cuadrícula (izq→der, arriba→abajo).
    board = models.JSONField(_("tablero"), default=list)
    # Índices 0–15 del tablero que el jugador ha marcado.
    marked = models.JSONField(_("marcadas"), default=list)
    is_winner = models.BooleanField(_("ganó"), default=False)
    connected = models.BooleanField(_("conectado"), default=False)

    class Meta:
        verbose_name = _("jugador de lotería")
        verbose_name_plural = _("jugadores de lotería")
        db_table = "loteria_player"
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["room", "name"], name="loteria_unique_player_name_per_room"
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} @ {self.room.code}"

    @property
    def is_full(self) -> bool:
        """True si tiene marcadas las 16 casillas."""
        return len(set(self.marked)) >= BOARD_SIZE
