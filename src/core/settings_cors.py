"""CORS — seguro por defecto.

Orígenes explícitos desde `.env` (landing React, backoffice React, Flutter web).
"""

import environ

env = environ.Env()

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:5173", "http://localhost:5174"],
)
CORS_ALLOW_CREDENTIALS = True
