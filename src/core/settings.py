"""Configuración Django de Dionisio.

`settings.py` inicializa `environ` una sola vez y contiene únicamente la
configuración propia de Django. Los bloques de STATIC/MEDIA/seguridad viven en
`env.py`; cada librería de terceros relevante tiene su `settings_<name>.py`.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# --- Inicialización única de environ (DRY: el resto de módulos asume .env cargado) ---
env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / "src" / "core" / ".env")

SECRET_KEY = env("SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])

# --- Aplicaciones ---
DJANGO_APPS = [
    # Unfold debe ir ANTES de django.contrib.admin (admin moderno).
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "django_filters",
]

LOCAL_APPS = [
    "apps.movies",
    "apps.games",
    "apps.config_settings",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

# --- Base de datos ---
DATABASES = {"default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3")}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Parámetros de juego (HU-09): defaults seguros vía env vars ---
GAME_SETTINGS_DEFAULTS = {
    "turn_duration_seconds": env.int("TURN_DURATION_SECONDS", default=60),
    "steal_window_seconds": env.int("STEAL_WINDOW_SECONDS", default=10),
    "speed_bonus_threshold_seconds": env.int("SPEED_BONUS_THRESHOLD_SECONDS", default=20),
    "special_round_interval": env.int("SPECIAL_ROUND_INTERVAL", default=3),
    "lightning_round_duration_seconds": env.int(
        "LIGHTNING_ROUND_DURATION_SECONDS", default=30
    ),
}

# --- OMDb ---
OMDB_API_KEY = env("OMDB_API_KEY", default="")
OMDB_API_BASE_URL = env("OMDB_API_BASE_URL", default="https://www.omdbapi.com")
OMDB_IMAGE_BASE_URL = env("OMDB_IMAGE_BASE_URL", default="https://img.omdbapi.com")
OMDB_ATTRIBUTION = {"source": "OMDb", "source_url": "https://www.omdbapi.com"}
# OMDb no expone "populares": se sincroniza buscando por términos (param `s`).
OMDB_SEARCH_TERMS = env.list(
    "OMDB_SEARCH_TERMS",
    default=[
        "star",
        "love",
        "night",
        "world",
        "man",
        "life",
        "war",
        "dark",
        "king",
        "dead",
    ],
)
# Año mínimo de estreno admitido en el catálogo (se descartan películas previas).
OMDB_MIN_YEAR = env.int("OMDB_MIN_YEAR", default=1990)

# --- Logging (rotación obligatoria) ---
LOG_DIR = Path(env("LOG_DIR", default=str(BASE_DIR / "logs")))
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {"format": "{levelname} {asctime} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "dionisio.log"),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "apps": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
        "django": {"handlers": ["console", "file"], "level": "WARNING", "propagate": False},
        "root": {"handlers": ["console", "file"], "level": "WARNING"},
    },
}

# --- Bloques modulares ---
from .env import *  # noqa: E402,F401,F403
from .settings_rest import *  # noqa: E402,F401,F403
from .settings_cors import *  # noqa: E402,F401,F403
from .settings_unfold import *  # noqa: E402,F401,F403
