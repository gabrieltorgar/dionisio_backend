# Dionisio · Backend

API REST de **Dionisio**, el juego social cinéfilo. Django 5.2 + DRF + PostgreSQL.

## Arquitectura

Capas estrictas: **View → Serializer → Service → Model**, con `selectors.py` para
lecturas complejas. PYTHONPATH raíz: `src/` (imports desde `apps.`, `common.`, `core.`, `api.`).

```
src/
  api/                 # urls raíz, health, JWT
  core/                # settings, env
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

> ⚠️ Usa `uv`/`make`, **no `pip install` directo**. El `requirements.txt` de la
> raíz es solo para el runtime de Vercel; instalarlo con `pip` sobre un Python
> gestionado por uv/el sistema falla con `error: externally-managed-environment`.
> `uv sync` (que corre `make install`) crea y usa su propio `.venv`.

> Las migraciones no están versionadas en este scaffold inicial: genéralas con
> `make migrations` tras la primera instalación.

El admin usa **django-unfold** (UX moderna), tematizado con la paleta de marca
en `core/settings_unfold.py`.

## Sincronización OMDb

```bash
uv run python manage.py sync_movies --pages 2                 # manual (HU-06)
uv run python manage.py sync_movies --terms batman matrix     # términos propios
uv run python manage.py sync_movies --min-year 2000           # sobreescribe OMDB_MIN_YEAR
```

OMDb no expone "populares": el catálogo se puebla buscando por una lista de
términos (`OMDB_SEARCH_TERMS`) y obteniendo el detalle de cada resultado por su
ID de IMDb. El `level` se asigna por `imdbVotes` (más votos → más mainstream).

La sincronización es **manual e incremental**: requiere `OMDB_API_KEY` en el
`.env`, solo descarga películas que aún no están en el catálogo (omite las
existentes) y descarta las estrenadas antes de `OMDB_MIN_YEAR` (por defecto
1990). También puede dispararse desde el backoffice con `POST /api/movies/sync/`.

OMDb no entrega traducciones. El título en español (`title_es`) se obtiene de
**Wikidata** (datos CC0) mapeando el `imdb_id` por su propiedad `P345`, con
respaldo al título del artículo de la **Wikipedia en español**. Wikimedia exige
un `User-Agent` con contacto: configúralo en `WIKIDATA_USER_AGENT`. Si no hay
traducción disponible, `display_title` usa el título original.

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

## Verificación de cuenta por código universal

Mientras no haya un backend de correo transaccional, la verificación por email
se **simula** con un único código universal
(`EMAIL_VERIFICATION_UNIVERSAL_CODE`, por defecto `979797`). El frontend puede
ejercitar el flujo completo "enviar código → introducir código → verificar"
(registro, cambio de correo, cambio de contraseña) sin envío real.

`common/verification.py` expone `send_verification_code()` (solo registra),
`is_valid_code()` (compara con el universal) y `VerificationPurpose`. Al conectar
el correo real, reemplaza el módulo por un almacén de códigos por usuario; los
llamadores no cambian. **Rota/elimina el código universal antes de producción.**

## Storage de media (Cloudflare R2)

La media subida (`ImageField`/`FileField`) usa **Cloudflare R2** (compatible con
S3, vía `django-storages`) en producción, porque el filesystem de Vercel es de
solo lectura y efímero. En local cae a `FileSystemStorage` sin credenciales.

R2 se activa con `USE_R2=True` (o implícitamente cuando hay credenciales). Las
variables viven en `core/settings_storages.py`: `R2_ACCOUNT_ID`,
`R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_PUBLIC_URL`
(host público que sirve los objetos). Los estáticos **no** van a R2: los sirve
WhiteNoise. Ver `src/core/.env.example`.

## Despliegue en Vercel

El proyecto se despliega serverless con `@vercel/python`:

- `vercel.json` — enruta todo a `api/index.py`.
- `api/index.py` — entrypoint WSGI (pone `src/` en el path y construye la app).
- `requirements.txt` — dependencias de runtime (en sync con `pyproject.toml`).

Con `VERCEL=1` (que la plataforma inyecta) los settings se endurecen solos:
`DEBUG=False`, logging solo a consola, `STATIC_ROOT` bajo `/tmp` y confianza
automática en `VERCEL_URL`/`VERCEL_PROJECT_PRODUCTION_URL` para
`ALLOWED_HOSTS`/CSRF. En Vercel `DATABASE_URL` es **obligatoria** y debe ser
Postgres (sqlite no persiste). Configura las variables (`SECRET_KEY`,
`DATABASE_URL`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, R2…) en el
dashboard de Vercel.

## Tests / CI

```bash
uv run pytest          # cobertura objetivo 80%
uv run ruff check src
uv run ruff format src
make check             # migraciones al día + ruff + pytest (lo mismo que corre CI)
```

El workflow `.github/workflows/ci.yml` corre `make check` en cada push/PR a
`dev` y `main`: como pytest importa `core.settings`, cualquier error de import o
de configuración se detecta en CI y **nunca llega a Vercel**.
