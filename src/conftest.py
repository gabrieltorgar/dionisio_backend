"""Fixtures compartidas de pytest."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def staff_user(db):
    return get_user_model().objects.create_user(
        email="staff@dionisio.app", password="pass1234", is_staff=True
    )
