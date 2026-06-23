"""Permisos del catálogo."""

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView


class IsStaffOrReadOnly(permissions.BasePermission):
    """Lectura pública; escritura solo para staff (backoffice)."""

    def has_permission(self, request: Request, _view: APIView) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)
