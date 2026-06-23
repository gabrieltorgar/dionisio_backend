"""Tests de configuración dinámica del juego (HU-09, HU-35)."""

import pytest
from django.urls import reverse

from apps.config_settings.models import GameSetting, GameSettingHistory
from apps.config_settings.services import (
    get_game_settings,
    reset_game_setting,
    set_game_setting,
)


@pytest.mark.django_db
def test_game_settings_endpoint_is_public_and_returns_defaults(api_client):
    response = api_client.get(reverse("game-settings"))

    assert response.status_code == 200
    assert response.data["turn_duration_seconds"] == 60
    assert response.data["steal_window_seconds"] == 10
    assert set(response.data.keys()) == {
        "turn_duration_seconds",
        "steal_window_seconds",
        "speed_bonus_threshold_seconds",
        "special_round_interval",
        "lightning_round_duration_seconds",
    }


@pytest.mark.django_db
def test_db_override_takes_priority_over_env_default():
    set_game_setting(key="turn_duration_seconds", value=90)

    resolved = get_game_settings()

    assert resolved["turn_duration_seconds"] == 90
    assert GameSettingHistory.objects.filter(key="turn_duration_seconds").count() == 1


@pytest.mark.django_db
def test_reset_returns_to_env_default():
    set_game_setting(key="steal_window_seconds", value=20)
    reset_game_setting(key="steal_window_seconds")

    resolved = get_game_settings()

    assert resolved["steal_window_seconds"] == 10
    assert not GameSetting.objects.filter(key="steal_window_seconds").exists()


@pytest.mark.django_db
def test_set_unknown_key_raises():
    from django.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        set_game_setting(key="not_a_real_param", value=10)
