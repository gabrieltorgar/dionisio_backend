"""Tests del motor de juego (HU-13, HU-20, HU-21, HU-22, HU-25)."""

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.games.models import GameMode, Turn, TurnStatus
from apps.games.rounds import special_round_type
from apps.games.services import create_game, register_turn_result
from apps.movies.tests.factories import MovieFactory


@pytest.fixture
def game(db):
    return create_game(
        mode=GameMode.TEAMS,
        config={"scenes": 9},
        teams=[{"name": "Los Directores"}, {"name": "Los Críticos"}],
    )


@pytest.mark.django_db
def test_create_game_requires_two_teams():
    from django.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        create_game(mode=GameMode.TEAMS, config={}, teams=[{"name": "Solo"}])


@pytest.mark.django_db
def test_guess_within_threshold_grants_speed_bonus(game):
    movie = MovieFactory()
    team = game.teams.first()
    turn = Turn.objects.create(game=game, team=team, movie=movie, scene_number=1)

    register_turn_result(
        turn=turn,
        status=TurnStatus.GUESSED,
        time_used=15,
        speed_bonus_threshold=20,
    )
    team.refresh_from_db()

    assert turn.speed_bonus is True
    # 1 base + 1 bonus de velocidad.
    assert team.score == Decimal("2.0")


@pytest.mark.django_db
def test_steal_awards_half_star(game):
    movie = MovieFactory()
    acting_team, rival = game.teams.all()[0], game.teams.all()[1]
    turn = Turn.objects.create(game=game, team=acting_team, movie=movie, scene_number=1)

    register_turn_result(
        turn=turn,
        status=TurnStatus.STOLEN,
        time_used=60,
        speed_bonus_threshold=20,
        stolen_by_id=rival.id,
    )
    rival.refresh_from_db()

    assert turn.stolen_by_id == rival.id
    assert rival.score == Decimal("0.5")


@pytest.mark.django_db
def test_streak_bonus_on_third_consecutive_guess(game):
    team = game.teams.first()
    for scene in range(1, 4):
        turn = Turn.objects.create(
            game=game, team=team, movie=MovieFactory(), scene_number=scene
        )
        register_turn_result(
            turn=turn,
            status=TurnStatus.GUESSED,
            time_used=40,  # sin bonus de velocidad
            speed_bonus_threshold=20,
        )
    team.refresh_from_db()

    # 3 aciertos (3) + 1 bonus de racha = 4.
    assert team.streak == 3
    assert team.score == Decimal("4.0")


@pytest.mark.django_db
def test_fail_resets_streak(game):
    team = game.teams.first()
    t1 = Turn.objects.create(game=game, team=team, movie=MovieFactory(), scene_number=1)
    register_turn_result(
        turn=t1, status=TurnStatus.GUESSED, time_used=40, speed_bonus_threshold=20
    )
    t2 = Turn.objects.create(game=game, team=team, movie=MovieFactory(), scene_number=2)
    register_turn_result(
        turn=t2, status=TurnStatus.FAILED, time_used=60, speed_bonus_threshold=20
    )
    team.refresh_from_db()

    assert team.streak == 0


@pytest.mark.parametrize(
    ("scene", "interval", "expected"),
    [
        (3, 3, "team"),
        (6, 3, "lightning"),
        (9, 3, "team"),
        (1, 3, None),
        (2, 3, None),
    ],
)
def test_special_round_type_is_deterministic(scene, interval, expected):
    assert special_round_type(scene_number=scene, interval=interval) == expected


@pytest.mark.django_db
def test_full_game_flow_via_api(api_client):
    movie = MovieFactory()
    create_resp = api_client.post(
        reverse("game-list"),
        {
            "mode": "teams",
            "config": {"scenes": 3},
            "teams": [{"name": "A"}, {"name": "B"}],
        },
        format="json",
    )
    assert create_resp.status_code == 201
    game_id = create_resp.data["id"]
    team_id = create_resp.data["teams"][0]["id"]

    turn_resp = api_client.post(
        reverse("game-turns", args=[game_id]),
        {"team_id": team_id, "movie_id": movie.id, "scene_number": 1},
        format="json",
    )
    assert turn_resp.status_code == 201
    turn_id = turn_resp.data["id"]

    result_resp = api_client.post(
        reverse("game-turn-result", args=[game_id, turn_id]),
        {"status": "guessed", "time_used": 10, "speed_bonus_threshold": 20},
        format="json",
    )
    assert result_resp.status_code == 200
    assert result_resp.data["speed_bonus"] is True

    finish_resp = api_client.patch(reverse("game-finish", args=[game_id]))
    assert finish_resp.status_code == 200
    assert finish_resp.data["status"] == "finished"

    results_resp = api_client.get(reverse("game-results", args=[game_id]))
    assert results_resp.status_code == 200
    assert results_resp.data[0]["guessed"] == 1
