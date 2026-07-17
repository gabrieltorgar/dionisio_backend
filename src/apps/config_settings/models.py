"""Modelos de configuración dinámica del juego (HU-35).

Prioridad de resolución: BD (`GameSetting`) > variable de entorno (default).
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import TimestampedModel


class GameSetting(TimestampedModel):
    """Override en BD de un parámetro de juego. Si no existe, se usa la env var."""

    key = models.CharField(_("clave"), max_length=64, unique=True)
    value = models.IntegerField(_("valor"))

    class Meta:
        verbose_name = _("parámetro de juego")
        verbose_name_plural = _("parámetros de juego")
        db_table = "game_setting"
        ordering = ["key"]

    def __str__(self) -> str:
        return f"{self.key}={self.value}"

    @staticmethod
    def allowed_keys() -> set[str]:
        """Claves válidas, derivadas de los defaults de settings."""
        return set(settings.GAME_SETTINGS_DEFAULTS.keys())


class GameSettingHistory(TimestampedModel):
    """Historial de cambios de parámetros (HU-35)."""

    key = models.CharField(_("clave"), max_length=64, db_index=True)
    value = models.IntegerField(_("valor"))
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="game_setting_changes",
        verbose_name=_("modificado por"),
    )

    class Meta:
        verbose_name = _("historial de parámetro")
        verbose_name_plural = _("historial de parámetros")
        db_table = "game_setting_history"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.key}={self.value} @ {self.created_at:%Y-%m-%d %H:%M}"
