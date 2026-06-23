"""Serializers del catálogo (HU-04, HU-07)."""

from rest_framework import serializers

from apps.movies.models import Collection, Movie


class MovieSerializer(serializers.ModelSerializer):
    """Salida pública de una película, con atribución OMDb (HU-04)."""

    display_title = serializers.CharField(read_only=True)
    attribution = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = [
            "id",
            "imdb_id",
            "title",
            "title_es",
            "display_title",
            "year",
            "poster_path",
            "poster_url",
            "genres",
            "level",
            "collections",
            "imdb_rating",
            "imdb_votes",
            "is_active",
            "attribution",
        ]
        read_only_fields = fields

    def get_attribution(self, _obj: Movie) -> dict[str, str]:
        from django.conf import settings

        return settings.OMDB_ATTRIBUTION


class MovieAdminSerializer(serializers.ModelSerializer):
    """Edición desde el backoffice (HU-33): level, colecciones, activar/desactivar."""

    class Meta:
        model = Movie
        fields = ["id", "title", "level", "collections", "is_active"]


class CollectionSerializer(serializers.ModelSerializer):
    """Salida de una colección (HU-07)."""

    class Meta:
        model = Collection
        fields = ["id", "name", "slug", "emoji", "description", "is_active"]
        read_only_fields = ["id"]
