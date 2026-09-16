"""Configuración ASGI. PYTHONPATH raíz: src/.

Sirve HTTP (Django) y WebSocket (Channels) en la misma aplicación: el
despliegue ASGI atiende la API y las salas de lotería en tiempo real.
"""

import os
import sys
from pathlib import Path

src_path = Path(__file__).resolve().parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

from django.core.asgi import get_asgi_application  # noqa: E402

# La app HTTP debe construirse antes de importar consumers (cargan modelos).
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402

from apps.loteria.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        # Las salas son públicas y se autentican con su propio token en la
        # query string, así que no se monta AuthMiddlewareStack ni sesiones.
        "websocket": URLRouter(websocket_urlpatterns),
    }
)
