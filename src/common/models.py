"""Modelos abstractos reutilizables."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class TimestampedModel(models.Model):
    """Añade marcas de creación y actualización."""

    created_at = models.DateTimeField(_("creado el"), auto_now_add=True)
    updated_at = models.DateTimeField(_("actualizado el"), auto_now=True)

    class Meta:
        abstract = True
