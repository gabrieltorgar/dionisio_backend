"""Management command para sincronizar el catálogo manualmente (HU-06)."""

from django.core.management.base import BaseCommand

from apps.movies.services import sync_movies


class Command(BaseCommand):
    help = "Sincroniza el catálogo de películas desde OMDb."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--pages", type=int, default=1, help="Páginas por término.")
        parser.add_argument(
            "--terms",
            nargs="+",
            default=None,
            help="Términos de búsqueda (por defecto OMDB_SEARCH_TERMS).",
        )
        parser.add_argument(
            "--no-images",
            action="store_true",
            help="No descargar posters localmente.",
        )

    def handle(self, *_args, **options) -> None:
        result = sync_movies(
            pages=options["pages"],
            download_images=not options["no_images"],
            terms=options["terms"],
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Sync completa: {result.created} creadas, "
                f"{result.updated} actualizadas, {len(result.errors)} errores."
            )
        )
        for error in result.errors:
            self.stdout.write(self.style.WARNING(f"  - {error}"))
