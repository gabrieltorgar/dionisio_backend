"""Lógica de configuración dinámica del juego (HU-09, HU-35)."""

import logging

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.config_settings.models import GameSetting, GameSettingHistory

logger = logging.getLogger("apps")


def get_game_settings() -> dict[str, int]:
    """Resuelve los parámetros de juego: BD sobre env var (HU-09).

    Empieza por los defaults de entorno y aplica los overrides de BD encima.
    """
    resolved = dict(settings.GAME_SETTINGS_DEFAULTS)
    for setting in GameSetting.objects.all():
        if setting.key in resolved:
            resolved[setting.key] = setting.value
    return resolved


@transaction.atomic
def set_game_setting(
    *, key: str, value: int, user: AbstractBaseUser | None = None
) -> GameSetting:
    """Crea o actualiza un override y registra el cambio (HU-35).

    Raises:
        ValidationError: si la clave no es válida o el valor no es positivo.
    """
    if key not in GameSetting.allowed_keys():
        raise ValidationError(f"Parámetro desconocido: {key}")
    if value <= 0:
        raise ValidationError("El valor debe ser un entero positivo.")

    setting, _created = GameSetting.objects.update_or_create(
        key=key, defaults={"value": value}
    )
    GameSettingHistory.objects.create(
        key=key,
        value=value,
        changed_by=user if user and user.is_authenticated else None,
    )
    logger.info("Parámetro %s actualizado a %s", key, value)
    return setting


@transaction.atomic
def reset_game_setting(*, key: str, user: AbstractBaseUser | None = None) -> None:
    """Elimina el override de BD; el parámetro vuelve a su env var (HU-35)."""
    deleted, _ = GameSetting.objects.filter(key=key).delete()
    if deleted:
        default = settings.GAME_SETTINGS_DEFAULTS.get(key)
        if default is not None:
            GameSettingHistory.objects.create(
                key=key,
                value=default,
                changed_by=user if user and user.is_authenticated else None,
            )
        logger.info("Parámetro %s reseteado a default", key)
