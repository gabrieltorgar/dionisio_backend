"""URLs raíz de la API, incluyendo cada app."""

from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from api.views import HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    # Auth JWT para el backoffice (staff).
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("", include("apps.movies.urls")),
    path("", include("apps.games.urls")),
    path("config/", include("apps.config_settings.urls")),
]
