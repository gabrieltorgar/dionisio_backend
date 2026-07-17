"""Tests del modelo de usuario autenticado por correo."""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

pytestmark = pytest.mark.django_db


def test_user_uses_email_as_username_field():
    assert User.USERNAME_FIELD == "email"
    assert "username" not in [f.name for f in User._meta.get_fields()]


def test_create_user_normalizes_email_and_hashes_password():
    user = User.objects.create_user(email="Person@Dionisio.APP", password="secret123")
    # El dominio se normaliza a minúsculas.
    assert user.email == "Person@dionisio.app"
    assert user.check_password("secret123")
    assert user.is_staff is False
    assert user.is_superuser is False


def test_create_superuser_has_admin_flags():
    admin = User.objects.create_superuser(
        email="admin@dionisio.app", password="secret123"
    )
    assert admin.is_staff is True
    assert admin.is_superuser is True


def test_create_user_requires_email():
    with pytest.raises(ValueError):
        User.objects.create_user(email="", password="secret123")


def test_str_returns_email():
    user = User.objects.create_user(email="who@dionisio.app", password="secret123")
    assert str(user) == "who@dionisio.app"
