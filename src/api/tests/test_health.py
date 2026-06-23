"""Test del endpoint de salud (HU-01)."""

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_health_returns_ok(api_client):
    response = api_client.get(reverse("health"))

    assert response.status_code == 200
    assert response.data == {"status": "ok"}
