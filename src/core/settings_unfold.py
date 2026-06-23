"""Configuración de django-unfold (admin moderno).

Tematizado con la paleta de marca Dionisio (oro Oscar como color primario).
Los colores se expresan en formato Tailwind ("R G B").
"""

from django.utils.translation import gettext_lazy as _

UNFOLD = {
    "SITE_TITLE": "Dionisio · Admin",
    "SITE_HEADER": "Dionisio",
    "SITE_SUBHEADER": _("El juego social cinéfilo"),
    "SITE_SYMBOL": "movie",  # ícono Material Symbols
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "COLORS": {
        # Oro Oscar — acento principal de la marca.
        "primary": {
            "50": "251 240 208",
            "100": "251 240 208",
            "200": "246 224 168",
            "300": "240 206 122",
            "400": "232 184 75",
            "500": "232 184 75",
            "600": "184 132 15",
            "700": "139 96 0",
            "800": "110 76 0",
            "900": "82 57 0",
            "950": "54 38 0",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": _("Catálogo"),
                "items": [
                    {
                        "title": _("Películas"),
                        "icon": "movie",
                        "link": "/admin/movies/movie/",
                    },
                    {
                        "title": _("Colecciones"),
                        "icon": "collections_bookmark",
                        "link": "/admin/movies/collection/",
                    },
                ],
            },
            {
                "title": _("Juego"),
                "items": [
                    {
                        "title": _("Partidas"),
                        "icon": "sports_esports",
                        "link": "/admin/games/game/",
                    },
                    {
                        "title": _("Turnos"),
                        "icon": "playlist_play",
                        "link": "/admin/games/turn/",
                    },
                    {
                        "title": _("Parámetros"),
                        "icon": "tune",
                        "link": "/admin/config_settings/gamesetting/",
                    },
                ],
            },
        ],
    },
}
