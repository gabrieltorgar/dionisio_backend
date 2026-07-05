"""Lógica de negocio del motor de juego (HU-13, HU-21, HU-22, HU-25)."""

import logging
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.games.models import Game, GameStatus, Team, Turn, TurnStatus

logger = logging.getLogger("apps")

STREAK_THRESHOLD = 3
STREAK_BONUS = Decimal("1")
SPEED_BONUS = Decimal("1")
STEAL_REWARD = Decimal("0.5")
GUESS_BASE = Decimal("1")


@transaction.atomic
def create_game(*, mode: str, config: dict, teams: list[dict]) -> Game:
    """Crea una partida con sus equipos (HU-13).

    Raises:
        ValidationError: si no hay al menos dos equipos.
    """
    if len(teams) < 2:
        raise ValidationError("Una partida requiere al menos dos equipos.")

    game = Game.objects.create(mode=mode, config=config)
    Team.objects.bulk_create(
        [
            Team(game=game, name=t["name"], avatar=t.get("avatar", ""))
            for t in teams
        ]
    )
    logger.info("Partida %s creada (%s) con %s equipos", game.pk, mode, len(teams))
    return game


@transaction.atomic
def register_turn_result(
    *,
    turn: Turn,
    status: str,
    time_used: int,
    speed_bonus_threshold: int,
    stolen_by_id: int | None = None,
) -> Turn:
    """Registra el resultado de un turno y actualiza el marcador.

    HU-13, HU-21, HU-22, HU-25.

    Aplica bonus de velocidad, recompensa de robo y bonus de racha.

    Raises:
        ValidationError: si el estado es inválido.
    """
    if status not in TurnStatus.values:
        raise ValidationError(f"Estado de turno inválido: {status}")

    turn.status = status
    turn.time_used = time_used
    team = turn.team

    if status == TurnStatus.GUESSED:
        gained = GUESS_BASE
        # Bonus de velocidad (HU-22).
        if time_used <= speed_bonus_threshold:
            turn.speed_bonus = True
            gained += SPEED_BONUS
        _apply_score(team=team, amount=gained)
        team.streak += 1
        # Bonus de racha (HU-25).
        if team.streak > 0 and team.streak % STREAK_THRESHOLD == 0:
            _apply_score(team=team, amount=STREAK_BONUS)
            logger.info("Racha de %s alcanzada por %s", team.streak, team.name)
        team.save(update_fields=["score", "streak"])

    elif status == TurnStatus.STOLEN and stolen_by_id is not None:
        # Robo de película (HU-21): media estrella al equipo que roba.
        stealer = Team.objects.select_for_update().get(pk=stolen_by_id, game=turn.game)
        _apply_score(team=stealer, amount=STEAL_REWARD)
        stealer.save(update_fields=["score"])
        turn.stolen_by = stealer
        # El equipo original pierde su racha.
        team.streak = 0
        team.save(update_fields=["streak"])

    else:
        # failed / passed: se rompe la racha.
        team.streak = 0
        team.save(update_fields=["streak"])

    turn.save()
    logger.info("Turno %s registrado: %s (%ss)", turn.pk, status, time_used)
    return turn


def _apply_score(*, team: Team, amount: Decimal) -> None:
    team.score = team.score + amount


@transaction.atomic
def finish_game(*, game: Game) -> Game:
    """Finaliza una partida (HU-13, HU-29)."""
    game.status = GameStatus.FINISHED
    game.finished_at = timezone.now()
    game.save(update_fields=["status", "finished_at"])
    logger.info("Partida %s finalizada", game.pk)
    return game
