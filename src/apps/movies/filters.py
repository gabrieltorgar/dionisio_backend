"""Filtros DRF del catálogo (HU-04)."""

from django_filters import rest_framework as filters

from apps.movies.models import Movie


class MovieFilter(filters.FilterSet):
    """Filtra por nivel, género y colección."""

    genre = filters.CharFilter(method="filter_genre")
    collection = filters.CharFilter(method="filter_collection")

    class Meta:
        model = Movie
        fields = ["level", "genre", "collection"]

    def filter_genre(self, queryset, _name, value):
        return queryset.filter(genres__contains=[value])

    def filter_collection(self, queryset, _name, value):
        return queryset.filter(collections__contains=[value])
