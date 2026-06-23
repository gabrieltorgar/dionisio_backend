"""Fixtures compartidas de pytest."""

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def staff_user(db):
    from django.contrib.auth.models import User

    return User.objects.create_user(
        username="staff", password="pass1234", is_staff=True
    )
