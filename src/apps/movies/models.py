"""Modelos del catálogo de películas (HU-04, HU-07)."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import TimestampedModel


class MovieLevel(models.TextChoices):
    """Nivel de dificultad cinéfila asignado a una película."""

    CASUAL = "casual", _("Espectador Casual")
    CONOCEDOR = "conocedor", _("Conocedor")
    LOCO = "loco", _("Loco por las Películas")
    CINEFILO = "cinefilo", _("Cinéfilo")


class Collection(TimestampedModel):
    """Colección temática curada de películas (HU-07)."""

    name = models.CharField(_("nombre"), max_length=120)
    slug = models.SlugField(_("slug"), max_length=140, unique=True)
    emoji = models.CharField(_("emoji"), max_length=8, blank=True)
    description = models.TextField(_("descripción"), blank=True)
    is_active = models.BooleanField(_("activa"), default=True, db_index=True)

    class Meta:
        verbose_name = _("colección")
        verbose_name_plural = _("colecciones")
        ordering = ["name"]
        db_table = "movie_collection"

    def __str__(self) -> str:
        return self.name


class Movie(TimestampedModel):
    """Película del catálogo, sincronizada desde OMDb con copia local (HU-04)."""

    imdb_id = models.CharField(_("ID IMDb"), max_length=20, unique=True)
    title = models.CharField(_("título"), max_length=255)
    title_es = models.CharField(_("título en español"), max_length=255, blank=True)
    year = models.PositiveSmallIntegerField(_("año"))
    poster_path = models.CharField(_("ruta local del poster"), max_length=500, blank=True)
    poster_url = models.URLField(_("URL del poster en OMDb"), blank=True)
    genres = models.JSONField(_("géneros"), default=list, blank=True)
    level = models.CharField(
        _("nivel"),
        max_length=20,
        choices=MovieLevel.choices,
        db_index=True,
    )
    collections = models.JSONField(_("colecciones (slugs)"), default=list, blank=True)
    imdb_rating = models.FloatField(_("rating IMDb"), default=0)
    imdb_votes = models.PositiveIntegerField(_("votos IMDb"), default=0)
    is_active = models.BooleanField(_("activa"), default=True, db_index=True)

    class Meta:
        verbose_name = _("película")
        verbose_name_plural = _("películas")
        ordering = ["-imdb_votes"]
        db_table = "movie"
        indexes = [
            models.Index(fields=["level", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.display_title} ({self.year})"

    @property
    def display_title(self) -> str:
        """Título preferido para mostrar (español si está disponible)."""
        return self.title_es or self.title
