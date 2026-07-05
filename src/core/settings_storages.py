"""Backend de almacenamiento de media: Cloudflare R2 (compatible con S3) en
producción, filesystem local en desarrollo.

Lo importa `settings.py` después del `.env` (DRY: asume que el entorno ya fue
leído). Es dueño del ajuste `STORAGES`. En Vercel el filesystem es de solo
lectura y efímero, así que la media subida (`ImageField`/`FileField`) debe vivir
en un store externo y persistente — Cloudflare R2, alcanzado por el backend S3
de `django-storages`.

R2 se activa con `USE_R2` (por defecto se enciende cuando las credenciales
están presentes); si no, la media cae a `FileSystemStorage` de Django para que
las corridas locales y los tests no necesiten credenciales cloud. Los estáticos
conservan el storage por defecto de Django — WhiteNoise los sirve vía finders
(ver `env.py`); **solo la media va a R2**.
"""

import environ

env = environ.Env()

# --- Credenciales / configuración de Cloudflare R2 ---
R2_ACCOUNT_ID = env.str("R2_ACCOUNT_ID", default="")
R2_ACCESS_KEY_ID = env.str("R2_ACCESS_KEY_ID", default="")
R2_SECRET_ACCESS_KEY = env.str("R2_SECRET_ACCESS_KEY", default="")
R2_BUCKET_NAME = env.str("R2_BUCKET_NAME", default="")
# Endpoint S3 con scope de cuenta; derivado del account id si no se da.
R2_ENDPOINT_URL = env.str(
    "R2_ENDPOINT_URL",
    default=(
        f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com" if R2_ACCOUNT_ID else ""
    ),
)
# Host público que sirve los objetos (un subdominio `r2.dev` o un dominio
# propio). Solo host; una URL completa se normaliza a su host más abajo.
R2_PUBLIC_URL = env.str("R2_PUBLIC_URL", default="")

# Activa R2 explícitamente con USE_R2, o implícitamente cuando hay credenciales.
_r2_configured = bool(
    R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY and R2_BUCKET_NAME and R2_ENDPOINT_URL
)
USE_R2 = env.bool("USE_R2", default=_r2_configured)

# El storage por defecto (media) es local salvo que R2 se active abajo. Los
# estáticos conservan el storage por defecto de Django; WhiteNoise los sirve
# mediante finders.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

if USE_R2:
    # Host sin esquema ni slash final, como lo espera django-storages.
    _custom_domain = R2_PUBLIC_URL.split("://", 1)[-1].rstrip("/") or None
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": R2_BUCKET_NAME,
            "endpoint_url": R2_ENDPOINT_URL,
            "access_key": R2_ACCESS_KEY_ID,
            "secret_key": R2_SECRET_ACCESS_KEY,
            # R2 ignora las regiones pero boto3 igual exige un valor.
            "region_name": "auto",
            "signature_version": "s3v4",
            "addressing_style": "virtual",
            # R2 no soporta ACLs; enviar una revienta al subir.
            "default_acl": None,
            # Nunca sobrescribir silenciosamente un objeto con el mismo nombre.
            "file_overwrite": False,
            # Media de lectura pública: URLs limpias, sin querystrings firmados.
            "querystring_auth": False,
            # Sirve los objetos desde el host público en vez del endpoint S3.
            "custom_domain": _custom_domain,
        },
    }
