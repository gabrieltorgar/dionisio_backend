"""Modelos del motor de juego (HU-13)."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import TimestampedModel


class GameMode(models.TextChoices):
    TEAMS = "teams", _("Equipos")
    DUEL = "duel", _("Duelo")


class GameStatus(models.TextChoices):
    ACTIVE = "active", _("En curso")
    FINISHED = "finished", _("Finalizada")


class TurnStatus(models.TextChoices):
    PENDING = "pending", _("Pendiente")
    ACTING = "acting", _("Actuando")
    GUESSED = "guessed", _("Adivinada")
    FAILED = "failed", _("Fallida")
    STOLEN = "stolen", _("Robada")
    PASSED = "passed", _("Pasada")


class Game(TimestampedModel):
    """Una partida. `config` guarda los parámetros usados (HU-13)."""

    mode = models.CharField(_("modo"), max_length=10, choices=GameMode.choices)
    config = models.JSONField(_("configuración"), default=dict)
    status = models.CharField(
        _("estado"),
        max_length=10,
        choices=GameStatus.choices,
        default=GameStatus.ACTIVE,
        db_index=True,
    )
    started_at = models.DateTimeField(_("iniciada el"), auto_now_add=True)
    finished_at = models.DateTimeField(_("finalizada el"), null=True, blank=True)

    class Meta:
        verbose_name = _("partida")
        verbose_name_plural = _("partidas")
        db_table = "game"
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"Partida {self.pk} ({self.mode})"


class Team(TimestampedModel):
    """Equipo/productora de una partida. `score` admite medias estrellas (HU-13, HU-21)."""

    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="teams", verbose_name=_("partida")
    )
    name = models.CharField(_("nombre"), max_length=20)
    avatar = models.CharField(_("avatar"), max_length=8, blank=True)
    score = models.DecimalField(_("puntaje"), max_digits=5, decimal_places=1, default=0)
    streak = models.PositiveSmallIntegerField(_("racha"), default=0)

    class Meta:
        verbose_name = _("equipo")
        verbose_name_plural = _("equipos")
        db_table = "game_team"
        ordering = ["-score"]

    def __str__(self) -> str:
        return self.name


class Turn(TimestampedModel):
    """Turno de actuación de una película (HU-13)."""

    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="turns", verbose_name=_("partida")
    )
    team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="turns", verbose_name=_("equipo")
    )
    movie = models.ForeignKey(
        "movies.Movie",
        on_delete=models.PROTECT,
        related_name="turns",
        verbose_name=_("película"),
    )
    scene_number = models.PositiveSmallIntegerField(_("número de escena"))
    status = models.CharField(
        _("estado"),
        max_length=10,
        choices=TurnStatus.choices,
        default=TurnStatus.PENDING,
    )
    time_used = models.PositiveSmallIntegerField(_("tiempo usado (s)"), default=0)
    speed_bonus = models.BooleanField(_("bonus de velocidad"), default=False)
    stolen_by = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stolen_turns",
        verbose_name=_("robada por"),
    )

    class Meta:
        verbose_name = _("turno")
        verbose_name_plural = _("turnos")
        db_table = "game_turn"
        ordering = ["scene_number", "id"]

    def __str__(self) -> str:
        return f"Turno escena {self.scene_number} — {self.team.name}"
