"""Consultas de lectura del motor de juego (HU-29)."""

from django.db.models import Count, Q, QuerySet

from apps.games.models import Game, Team, TurnStatus


def game_results(*, game: Game) -> QuerySet[Team]:
    """Ranking de equipos con desglose de aciertos, fallos y robos (HU-29)."""
    return (
        game.teams.annotate(
            guessed=Count("turns", filter=Q(turns__status=TurnStatus.GUESSED)),
            failed=Count("turns", filter=Q(turns__status=TurnStatus.FAILED)),
            steals=Count("stolen_turns"),
        )
        .order_by("-score")
    )
