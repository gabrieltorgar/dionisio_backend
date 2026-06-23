"""Admin del catálogo (HU-04, HU-08). Usa django-unfold (admin moderno)."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.movies.models import Collection, Movie


@admin.register(Movie)
class MovieAdmin(ModelAdmin):
    list_display = ("display_title", "year", "level", "imdb_votes", "imdb_rating", "is_active")
    list_filter = ("level", "is_active")
    search_fields = ("title", "title_es", "imdb_id")
    list_editable = ("level", "is_active")
    readonly_fields = ("imdb_id", "created_at", "updated_at")
    ordering = ("-imdb_votes",)


@admin.register(Collection)
class CollectionAdmin(ModelAdmin):
    list_display = ("name", "slug", "emoji", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
