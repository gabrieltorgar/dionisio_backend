"""Catálogo de la baraja tradicional de lotería mexicana (54 cartas).

El orden es el clásico (Don Clemente) y es la fuente de verdad del número de
cada carta: el frontend usa el mismo número para resolver su imagen
(`/images/loteria/NN.jpg`).
"""

from typing import TypedDict


class Card(TypedDict):
    number: int
    name: str


CARD_NAMES: tuple[str, ...] = (
    "El gallo",
    "El diablito",
    "La dama",
    "El catrín",
    "El paraguas",
    "La sirena",
    "La escalera",
    "La botella",
    "El barril",
    "El árbol",
    "El melón",
    "El valiente",
    "El gorrito",
    "La muerte",
    "La pera",
    "La bandera",
    "El bandolón",
    "El violoncello",
    "La garza",
    "El pájaro",
    "La mano",
    "La bota",
    "La luna",
    "El cotorro",
    "El borracho",
    "El negrito",
    "El corazón",
    "La sandía",
    "El tambor",
    "El camarón",
    "Las jaras",
    "El músico",
    "La araña",
    "El soldado",
    "La estrella",
    "El cazo",
    "El mundo",
    "El apache",
    "El nopal",
    "El alacrán",
    "La rosa",
    "La calavera",
    "La campana",
    "El cantarito",
    "El venado",
    "El sol",
    "La corona",
    "La chalupa",
    "El pino",
    "El pescado",
    "La palma",
    "La maceta",
    "El arpa",
    "La rana",
)

DECK_SIZE = len(CARD_NAMES)
BOARD_SIZE = 16  # cuadrícula 4×4

CARDS: tuple[Card, ...] = tuple(
    Card(number=i, name=name) for i, name in enumerate(CARD_NAMES, start=1)
)


def card_name(number: int) -> str:
    """Nombre de la carta por su número (1–54)."""
    if 1 <= number <= DECK_SIZE:
        return CARD_NAMES[number - 1]
    raise ValueError(f"Carta fuera de rango: {number}")
