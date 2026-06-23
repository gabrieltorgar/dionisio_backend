"""Lógica determinística de rondas especiales (HU-20, HU-23, HU-24).

El tipo de ronda especial se deriva de forma determinística del número de
escena para que backend y Flutter coincidan sin sincronizar estado.

Algoritmo portable (replicado idénticamente en Dart):
    - Una escena es especial si `scene_number % interval == 0`.
    - Si es especial: `lightning` cuando `scene_number` es par, `team` si es impar.

Se prefiere esta regla a `hashCode % 2` porque `hashCode` no es portable entre
Python y Dart; esta función sí lo es.
"""

LIGHTNING = "lightning"
TEAM = "team"


def is_special_scene(*, scene_number: int, interval: int) -> bool:
    """Indica si la escena dispara una ronda especial."""
    if interval <= 0:
        return False
    return scene_number % interval == 0


def special_round_type(*, scene_number: int, interval: int) -> str | None:
    """Devuelve `lightning`, `team` o `None` para una escena dada."""
    if not is_special_scene(scene_number=scene_number, interval=interval):
        return None
    return LIGHTNING if scene_number % 2 == 0 else TEAM
