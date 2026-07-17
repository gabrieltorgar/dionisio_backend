"""Modelo de usuario de Dionisio, autenticado por correo electrónico."""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.users.managers import UserManager
from common.models import TimestampedModel


class User(AbstractUser, TimestampedModel):
    """Usuario autenticado por correo en lugar de nombre de usuario."""

    username = None

    email = models.EmailField(
        _("correo electrónico"),
        unique=True,
        error_messages={
            "unique": _("Ya existe un usuario con ese correo electrónico."),
        },
    )
    email_verified_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("correo verificado el")
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("usuario")
        verbose_name_plural = _("usuarios")
        db_table = "users_user"

    def __str__(self) -> str:
        return self.email
