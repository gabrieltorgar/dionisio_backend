"""Flujo simulado de verificación por código.

Todavía no hay un backend de correo transaccional configurado, así que en lugar
de generar y enviar un código por usuario aceptamos un único código
**universal** (`settings.EMAIL_VERIFICATION_UNIVERSAL_CODE`, por defecto
`"979797"`). Esto permite al frontend ejercitar la experiencia completa
"enviar código → introducir código → verificar" para registro, cambio de correo
y cambio de contraseña sin envío real de emails.

`send_verification_code` solo registra el (supuesto) envío; `is_valid_code`
compara el código enviado contra el universal. Cuando se conecte el correo real,
reemplaza este módulo por un almacén de códigos por usuario más un backend de
email — los llamadores no cambian.
"""

import logging

from django.conf import settings

logger = logging.getLogger("apps")


class VerificationPurpose:
    """Razones por las que se solicita un código (para logging/copys de UX)."""

    REGISTRATION = "registration"
    EMAIL_CHANGE = "email_change"
    PASSWORD_CHANGE = "password_change"  # noqa: S105 -- etiqueta, no un secreto


def get_universal_code() -> str:
    """Devuelve el código de verificación universal configurado."""
    return str(settings.EMAIL_VERIFICATION_UNIVERSAL_CODE)


def send_verification_code(*, email: str, purpose: str) -> None:
    """Simula el envío de un código de verificación a `email`.

    Sin backend de correo configurado esto es un no-op más allá del log. El
    código que el usuario debe introducir es siempre el universal (ver docstring
    del módulo).
    """
    logger.info(
        "Código de verificación simulado enviado a %s (purpose=%s). "
        "Usa el código universal para verificar.",
        email,
        purpose,
    )


def is_valid_code(code: str | None) -> bool:
    """Devuelve `True` cuando `code` coincide con el código universal."""
    if not code:
        return False
    return str(code).strip() == get_universal_code()
