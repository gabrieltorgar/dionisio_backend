.PHONY: help install migrate migrations run test cov lint format check superuser shell \
        clean clean_migrations data sync flush initial-data-flush lock collectstatic \
        setup dev

help:
	@echo "Comandos disponibles:"
	@echo "  make install      - Instalar dependencias"
	@echo "  make migrate      - Ejecutar migraciones"
	@echo "  make migrations   - Generar migraciones"
	@echo "  make run          - Ejecutar servidor de desarrollo"
	@echo "  make test         - Ejecutar tests"
	@echo "  make cov          - Tests con cobertura"
	@echo "  make lint         - Linter (ruff)"
	@echo "  make format       - Formatear (ruff)"
	@echo "  make superuser    - Crear superusuario"
	@echo "  make data         - Cargar fixtures (colecciones)"
	@echo "  make sync         - Sincronizar catálogo desde OMDb"
	@echo "  make shell        - Abrir shell de Django"
	@echo "  make clean        - Limpiar archivos temporales"
	@echo "  make lock         - Refrescar uv.lock"

install:
	uv sync

migrate:
	uv run python src/manage.py migrate

migrations:
	uv run python src/manage.py makemigrations

run:
	uv run python src/manage.py runserver 8500

test:
	uv run pytest

cov:
	uv run pytest --cov=apps --cov-report=term-missing

lint:
	uv run ruff check src

format:
	uv run ruff format src

# Gate de calidad (lo corre CI): migraciones al día + ruff + pytest.
check:
	uv run python src/manage.py makemigrations --dry-run --check
	uv run ruff check src
	uv run pytest

superuser:
	DJANGO_SUPERUSER_USERNAME=dev \
	DJANGO_SUPERUSER_FIRST_NAME="Developer" \
	DJANGO_SUPERUSER_LAST_NAME="User" \
	DJANGO_SUPERUSER_PASSWORD=Mexico123. \
	DJANGO_SUPERUSER_EMAIL="admin@develop.com" \
	uv run python src/manage.py createsuperuser --noinput

shell:
	cd src && uv run python manage.py shell

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

clean_migrations:
	find src/apps/movies/migrations/ -type f ! -name "__init__.py" -delete
	find src/apps/games/migrations/ -type f ! -name "__init__.py" -delete
	find src/apps/config_settings/migrations/ -type f ! -name "__init__.py" -delete

data:
	uv run python src/manage.py loaddata src/apps/movies/fixtures/collections.json

sync:
	uv run python src/manage.py sync_movies --pages 2

flush:
	uv run python src/manage.py flush

initial-data-flush: flush superuser data
	@echo "Datos iniciales recargados."

lock:
	uv lock

collectstatic:
	cd src && uv run python manage.py collectstatic --noinput

setup: install migrate superuser data
	@echo "Setup completo!"

dev: migrate run
