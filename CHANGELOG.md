# Changelog — Dionisio Backend

## [0.3.0] — 2026-06-22 — Admin Unfold, Makefile y ajustes de estructura

### Added

- **core/settings_unfold.py — Admin moderno (django-unfold)**: Config `UNFOLD` con título/encabezado de marca, color primario oro Oscar y navegación lateral (Catálogo, Juego). `"unfold"` registrado antes de `django.contrib.admin`.
- **Makefile — Comandos de proyecto**: Targets `install/migrate/migrations/run/test/cov/lint/format/superuser/data/sync/clean/clean_migrations/lock/collectstatic/setup/dev` y workers de Celery, adaptados a las apps de Dionisio (movies, games, config_settings).
- **apps/\*/migrations/__init__.py — Paquetes de migraciones**: Carpetas `migrations/` inicializadas en cada app.

### Changed

- **apps/movies/admin.py, apps/games/admin.py, apps/config_settings/admin.py — Base Unfold**: `admin.ModelAdmin` → `unfold.admin.ModelAdmin` e inlines a `unfold.admin.TabularInline` (sin cambiar la lógica del admin).
- **src/manage.py — Ubicación en src/**: `manage.py` movido dentro de `src/` y ajustado para añadir su propio directorio a `sys.path`.

## [0.2.0] — 2026-06-22 — Migración del catálogo de TMDB a OMDb

### Added

- **apps/movies/omdb.py — Cliente OMDb**: Cliente para omdbapi.com con búsqueda paginada por término (`s`) y detalle por ID de IMDb (`i`), con reintento y manejo de `Response:"False"` (incluido límite diario).
- **core/settings.py — OMDB_SEARCH_TERMS**: Lista de términos configurable para poblar el catálogo (OMDb no expone "populares").

### Changed

- **apps/movies/models.py — Campos OMDb**: `tmdb_id` (Integer) → `imdb_id` (Char, ej. `tt0137523`); `tmdb_popularity` → `imdb_rating` + `imdb_votes`; `poster_url` ahora opcional; orden por `-imdb_votes`.
- **apps/movies/services.py — Sync por términos**: `upsert_movie_from_tmdb` → `upsert_movie_from_omdb` (parseo de `Year`/`Genre`/`imdbVotes`); `assign_level` ahora usa votos IMDb en vez de popularidad; `sync_movies` busca por términos y detalla cada resultado.
- **apps/movies/serializers.py / admin.py — Contrato OMDb**: La salida expone `imdb_id`, `imdb_rating`, `imdb_votes` y `attribution` apunta a `OMDb / omdbapi.com`.
- **core/settings.py + .env(.example) — Variables OMDb**: `TMDB_*` reemplazadas por `OMDB_API_KEY`, `OMDB_API_BASE_URL`, `OMDB_IMAGE_BASE_URL`, `OMDB_SEARCH_TERMS`.
- **management/commands/sync_movies.py — Flag --terms**: Permite pasar términos de búsqueda propios.

### Removed

- **apps/movies/tmdb.py — Cliente TMDB**: Vaciado (deprecado); el catálogo ya no usa themoviedb.org.

## [0.1.0] — 2026-06-22 — Infraestructura, catálogo, configuración y motor de juego

### Added

- **pyproject.toml — Scaffold uv + ruff**: Dependencias (Django 5.2, DRF, SimpleJWT, django-environ, CORS, filter, Celery, redis, storages, pillow, requests) y config de ruff/pytest. PYTHONPATH raíz `src/`.
- **core/settings.py + env.py + settings_\*.py — Configuración por entorno**: `settings.py` inicializa environ una vez; `env.py` con STATIC/MEDIA/seguridad; `settings_rest`, `settings_cors` (seguro por defecto) y `settings_celery` modulares. Logging con `RotatingFileHandler`.
- **api/views.py — Health check (HU-01)**: `GET /api/health/` retorna `200 {"status":"ok"}`.
- **api/urls.py — JWT del backoffice**: Endpoints `auth/token/` y `auth/token/refresh/` (SimpleJWT) para staff.
- **common/models.py — TimestampedModel**: Modelo abstracto con `created_at`/`updated_at`.
- **apps/movies/models.py — Movie y Collection (HU-04, HU-07)**: `Movie` con `tmdb_id`, títulos, nivel (TextChoices), géneros/colecciones JSON, popularidad y posters local+TMDB; `Collection` curada con slug y emoji.
- **apps/movies/tmdb.py — Cliente TMDB (HU-06)**: GET con reintento exponencial ante 429 (rate limiting).
- **apps/movies/services.py — Sync y caché de imágenes (HU-05, HU-06)**: `assign_level` por popularidad, `upsert_movie_from_tmdb` idempotente por `tmdb_id`, `download_poster` a storage local y `sync_movies` (populares, top rated, por géneros).
- **apps/movies/tasks.py + management/commands/sync_movies.py — Sincronización (HU-06)**: Tarea Celery `sync_movies_weekly` (domingos 03:00 UTC) y command manual `sync_movies`.
- **apps/movies/views.py — Catálogo y backoffice (HU-04, HU-33, HU-34)**: `MovieViewSet` (listado público filtrable por level/genre/collection, edición staff, acción `sync`) y `CollectionViewSet` (CRUD). Atribución TMDB en el serializer.
- **apps/movies/fixtures/collections.json — Colecciones iniciales (HU-07)**: Grandes Clásicos, Héroes, Ciencia Ficción, Noche de Terror, Familiar, Navidad y Ganadoras del Oscar.
- **apps/config_settings/ — Configuración dinámica (HU-09, HU-35)**: `GameSetting`/`GameSettingHistory`; servicio que resuelve BD sobre env var; `GET /api/config/game-settings/` público y endpoints admin de override/reset con historial.
- **apps/games/models.py — Game, Team, Turn (HU-13)**: Partida con `config` JSON, equipos con `score` decimal (admite medias estrellas) y racha, turnos con estado/tiempo/bonus/robo.
- **apps/games/rounds.py — Rondas especiales determinísticas (HU-20/23/24)**: Algoritmo portable (replicado en Dart) que deriva lightning/team del número de escena.
- **apps/games/services.py — Lógica de puntuación (HU-13/21/22/25)**: `register_turn_result` aplica bonus de velocidad, robo de media estrella y bonus de racha; `create_game` y `finish_game` transaccionales.
- **apps/games/views.py — Endpoints de partida (HU-13, HU-29)**: Crear partida, crear turno, registrar resultado, finalizar y ranking final con desglose (aciertos/fallos/robos).
- **tests — Suites por app**: Cobertura de asignación de nivel, upsert idempotente, atribución y filtros del catálogo; resolución BD>env de settings; bonus/robo/racha y flujo completo de partida vía API; health check.

### Changed

- **core/settings.py — CORS seguro por defecto**: `CORS_ALLOW_ALL_ORIGINS=False` con orígenes explícitos desde `.env` (landing 5174, backoffice 5173).
