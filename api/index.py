"""Entrypoint serverless de Vercel para la aplicación WSGI de Django.

El builder `@vercel/python` de Vercel importa este módulo y sirve el callable
`app` (WSGI/ASGI) a nivel de módulo. El proyecto usa layout `src/`, así que
ponemos `src` en el import path antes de construir la aplicación WSGI,
replicando lo que hace `src/manage.py` para los comandos locales.
"""

import os
import sys
from pathlib import Path

# El proyecto usa layout src/: hace importables `core`, `apps`, `common`, `api`.
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

from django.core.wsgi import get_wsgi_application  # noqa: E402

# Vercel sirve el que encuentre; exponemos ambos nombres.
app = get_wsgi_application()
application = app
