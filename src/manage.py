#!/usr/bin/env python
"""Utilidad de línea de comandos de Django.

Vive dentro de `src/`, que es la raíz de PYTHONPATH. Se añade su propio
directorio a `sys.path` para que los imports `apps.`/`common.`/`core.`/`api.`
funcionen tanto ejecutándolo desde la raíz (`python src/manage.py`) como desde
dentro de `src/` (`python manage.py`).
"""

import os
import sys
from pathlib import Path


def main() -> None:
    """Ejecuta tareas administrativas."""
    src_path = Path(__file__).resolve().parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "No se pudo importar Django. ¿Está instalado y activo el entorno virtual?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
