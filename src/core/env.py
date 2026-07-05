"""Configuración derivada del entorno: estáticos, media y seguridad.

Lo importa `settings.py` vía `from .env import *`. Asume que `settings.py` ya
leyó el `.env` (DRY). Es dueño de las rutas STATIC/MEDIA, WhiteNoise y del
bloque de endurecimiento de seguridad para producción.
"""

import os
from pathlib import Path

import environ

env = environ.Env()

# src/ (este archivo vive en src/core/) y raíz del repo.
SRC_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SRC_DIR.parent

# Refleja settings.DEBUG: seguro por defecto (False) en Vercel, True en local.
DEBUG = env.bool("DEBUG", default=not env.bool("VERCEL", default=False))

# --- Estáticos ---
STATIC_URL = env.str("STATIC_URL", default="static/")
# En serverless (fs de solo lectura) STATIC_ROOT debe vivir bajo /tmp para que
# un collectstatic opcional pueda escribir; con los finders de WhiteNoise
# (abajo) ni siquiera necesita existir.
_default_static_root = (
    "/tmp/static"  # noqa: S108 -- única ruta escribible en el fs de Vercel
    if env.bool("VERCEL", default=False)
    else str(REPO_ROOT / "staticfiles")
)
STATIC_ROOT = env.str("STATIC_ROOT", default=_default_static_root)
# Solo incluye dirs de estáticos extra que existan: una entrada faltante hace
# que staticfiles (collectstatic, WhiteNoise, runserver) falle al arrancar.
STATICFILES_DIRS = [d for d in (SRC_DIR / "static",) if d.exists()]

# --- WhiteNoise (sirve estáticos en serverless/producción sin collectstatic) ---
# USE_FINDERS deja que WhiteNoise sirva directo desde los dirs static de las
# apps en tiempo de request, sin paso de build collectstatic (ideal en Vercel).
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = DEBUG

# --- Media ---
MEDIA_URL = env.str("MEDIA_URL", default="/media/")
MEDIA_ROOT = env.str("MEDIA_ROOT", default=os.path.join(REPO_ROOT, "media"))

# --- Cookies (siempre activas) ---
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

# --- Endurecimiento de seguridad para producción ---
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    X_FRAME_OPTIONS = "DENY"
