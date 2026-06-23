"""Vistas transversales de la API."""

from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    """`GET /api/health/` — comprobación de salud del servicio (HU-01)."""

    permission_classes = [AllowAny]

    def get(self, _request: Request) -> Response:
        return Response({"status": "ok"})
