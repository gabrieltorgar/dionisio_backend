"""Tests de la configuración de storage de media (FS local vs Cloudflare R2)."""

from django.conf import settings
from django.core.files.storage import default_storage
from storages.backends.s3 import S3Storage


def test_default_media_storage_is_local_without_r2():
    """Con R2 desactivado (el default de tests), la media queda en el filesystem."""
    assert settings.USE_R2 is False
    assert (
        settings.STORAGES["default"]["BACKEND"]
        == "django.core.files.storage.FileSystemStorage"
    )
    assert default_storage.__class__.__name__ == "FileSystemStorage"


def test_r2_options_produce_clean_public_urls():
    """Las opciones de R2 que configuramos producen URLs públicas en el dominio
    propio, sin querystrings firmados."""
    storage = S3Storage(
        bucket_name="dionisio-media",
        endpoint_url="https://acc.r2.cloudflarestorage.com",
        region_name="auto",
        addressing_style="virtual",
        default_acl=None,
        querystring_auth=False,
        custom_domain="media.dionisio.app",
    )

    url = storage.url("movies/poster.jpg")

    assert url == "https://media.dionisio.app/movies/poster.jpg"
    assert "?" not in url  # sin firma en lecturas públicas
