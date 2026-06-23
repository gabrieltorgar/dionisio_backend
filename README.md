# Dionisio · Backend

API REST de **Dionisio**, el juego social cinéfilo. Django 5.2 + DRF + PostgreSQL.

## Arquitectura

Capas estrictas: **View → Serializer → Service → Model**, con `selectors.py` para
lecturas complejas. PYTHONPATH raíz: `src/` (imports desde `apps.`, `common.`, `core.`, `api.`).

```
src/
  api/                 # urls raíz, health, JWT
  core/                # settings, env, celery
  common/              # modelos abstractos (TimestampedModel)
  apps/
    movies/            # catálogo, sync OMDb, colecciones (E2)
    config_settings/   # parámetros dinámicos del juego (E3)
    games/             # partidas, turnos, marcador (E5)
```

## Puesta en marcha

El `manage.py` vive dentro de `src/`. Hay un `Makefile` con los comandos
habituales (`make help`):

```bash
make install                              # uv sync
cp src/core/.env.example src/core/.env    # configura entorno (o: make ... )
make migrations                           # genera migraciones
make migrate                              # aplica migraciones
make data                                 # colecciones curadas (HU-07)
make superuser                            # acceso al backoffice/admin
make run                                  # servidor en :8500
```

O directamente: `uv run python src/manage.py <comando>`.

> Las migraciones no están versionadas en este scaffold inicial: genéralas con
> `make migrations` tras la primera instalación.

El admin usa **django-unfold** (UX moderna), tematizado con la paleta de marca
en `core/settings_unfold.py`.

## Sincronización OMDb

```bash
uv run python manage.py sync_movies --pages 2                 # manual (HU-06)
uv run python manage.py sync_movies --terms batman matrix     # términos propios
```

OMDb no expone "populares": el catálogo se puebla buscando por una lista de
términos (`OMDB_SEARCH_TERMS`) y obteniendo el detalle de cada resultado por su
ID de IMDb. El `level` se asigna por `imdbVotes` (más votos → más mainstream).

Tarea Celery semanal `sync_movies_weekly` (domingos 03:00 UTC). Requiere
`OMDB_API_KEY` en el `.env`. Worker + beat:

```bash
uv run celery -A core worker -l info
uv run celery -A core beat -l info
```

## Endpoints principales

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| GET | `/api/health/` | Estado del servicio | público |
| GET | `/api/movies/?level=&genre=&collection=` | Catálogo filtrable (HU-04) | público |
| PATCH | `/api/movies/{id}/` | Editar level/colección/activo (HU-33) | staff |
| POST | `/api/movies/sync/` | Disparar sync OMDb (HU-33) | staff |
| GET/POST | `/api/collections/` | Colecciones (HU-07, HU-34) | lectura pública / escritura staff |
| GET | `/api/config/game-settings/` | Parámetros del juego (HU-09) | público |
| POST/DELETE | `/api/config/game-settings/admin/` | Override / reset (HU-35) | staff |
| POST | `/api/games/` | Crear partida (HU-13) | público |
| POST | `/api/games/{id}/turns/` | Crear turno | público |
| POST | `/api/games/{id}/turns/{turn_id}/result/` | Registrar resultado (HU-13/21/22/25) | público |
| PATCH | `/api/games/{id}/finish/` | Finalizar partida | público |
| GET | `/api/games/{id}/results/` | Ranking final (HU-29) | público |
| POST | `/api/auth/token/` | JWT para backoffice | público |

## Configuración dinámica del juego

Prioridad: **BD (`GameSetting`) > variable de entorno (default)**. El endpoint
`/api/config/game-settings/` resuelve ambos. Cambios registrados en
`GameSettingHistory` (HU-35).

## Rondas especiales (determinismo back ↔ Flutter)

`apps/games/rounds.py` deriva el tipo de ronda especial del número de escena con
un algoritmo portable (replicado en Dart): especial si `scene % interval == 0`;
`lightning` si la escena es par, `team` si es impar.

## Tests

```bash
uv run pytest          # cobertura objetivo 80%
uv run ruff check src
uv run ruff format src
```
