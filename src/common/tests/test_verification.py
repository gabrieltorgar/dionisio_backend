"""Tests del flujo de verificación por código universal."""

import logging

import pytest
from django.conf import settings

from common import verification


def test_universal_code_default_is_979797():
    assert settings.EMAIL_VERIFICATION_UNIVERSAL_CODE == "979797"
    assert verification.get_universal_code() == "979797"


@pytest.mark.parametrize("code", ["979797", " 979797 "])
def test_is_valid_code_accepts_universal_code(code):
    assert verification.is_valid_code(code) is True


@pytest.mark.parametrize("code", [None, "", "000000", "abc"])
def test_is_valid_code_rejects_anything_else(code):
    assert verification.is_valid_code(code) is False


def test_send_verification_code_logs_without_raising(caplog):
    # El logger "apps" tiene propagate=False, así que enganchamos el handler de
    # caplog directamente para capturar sus records.
    apps_logger = logging.getLogger("apps")
    apps_logger.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.INFO, logger="apps"):
            verification.send_verification_code(
                email="user@example.com",
                purpose=verification.VerificationPurpose.REGISTRATION,
            )
    finally:
        apps_logger.removeHandler(caplog.handler)
    assert "user@example.com" in caplog.text
