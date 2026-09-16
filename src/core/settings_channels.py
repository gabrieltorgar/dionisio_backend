"""Channels — WebSockets para la lotería en tiempo real.

Capa de canales: con `REDIS_URL` usa Redis (varios procesos/instancias);
sin ella, la capa en memoria, suficiente para desarrollo y para un despliegue
de un solo proceso.
"""

import environ

env = environ.Env()

ASGI_APPLICATION = "core.asgi.application"

REDIS_URL = env.str("REDIS_URL", default="")

if REDIS_URL:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [REDIS_URL]},
        }
    }
else:
    CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
