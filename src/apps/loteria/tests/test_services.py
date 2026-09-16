"""Tests de la lógica de lotería: sala, tableros, canto y validación."""

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.loteria.cards import BOARD_SIZE, CARDS, DECK_SIZE
from apps.loteria.models import RoomStatus
from apps.loteria.services import (
    CODE_LENGTH,
    claim_loteria,
    create_room,
    draw_next,
    join_room,
    reset_to_lobby,
    set_mark,
    start_round,
)


@pytest.fixture
def room(db):
    return create_room()


def _mark_all_drawn(player, room):
    """Marca en el tablero del jugador todas las casillas ya cantadas."""
    drawn = set(room.deck[: room.drawn_count])
    for index, number in enumerate(player.board):
        if number in drawn:
            player = set_mark(player, index, True)
    return player


def test_baraja_completa_y_sin_repetidos():
    assert DECK_SIZE == 54
    assert len(CARDS) == 54
    assert CARDS[0]["name"] == "El gallo"
    assert CARDS[53]["name"] == "La rana"
    assert len({c["number"] for c in CARDS}) == 54


@pytest.mark.django_db
def test_create_room_genera_codigo_y_baraja(room):
    assert len(room.code) == CODE_LENGTH
    assert room.status == RoomStatus.LOBBY
    assert sorted(room.deck) == list(range(1, DECK_SIZE + 1))
    assert "O" not in room.code and "0" not in room.code


@pytest.mark.django_db
def test_join_reparte_tablero_de_16_sin_repetir(room):
    player = join_room(room.code, "  Ana  ")
    assert player.name == "Ana"
    assert len(player.board) == BOARD_SIZE
    assert len(set(player.board)) == BOARD_SIZE


@pytest.mark.django_db
def test_join_valida_codigo_nombre_y_duplicados(room):
    with pytest.raises(ValidationError):
        join_room("XXXXXX", "Ana")
    with pytest.raises(ValidationError):
        join_room(room.code, "   ")
    join_room(room.code, "Ana")
    with pytest.raises(ValidationError):
        join_room(room.code, "ana")


@pytest.mark.django_db
def test_no_se_puede_entrar_con_la_partida_en_curso(room):
    join_room(room.code, "Ana")
    start_round(room)
    with pytest.raises(ValidationError):
        join_room(room.code, "Beto")


@pytest.mark.django_db
def test_canta_las_54_cartas_sin_repetir(room):
    join_room(room.code, "Ana")
    start_round(room)
    salidas = []
    while (card := draw_next(room)) is not None:
        salidas.append(card)
    assert len(salidas) == DECK_SIZE
    assert len(set(salidas)) == DECK_SIZE


@pytest.mark.django_db
def test_loteria_valida_gana_y_cierra_la_partida(room):
    player = join_room(room.code, "Ana")
    start_round(room)
    # Se canta la baraja completa: el tablero de Ana queda cubierto.
    while draw_next(room) is not None:
        pass
    room.refresh_from_db()
    player = _mark_all_drawn(player, room)

    winner = claim_loteria(player)
    room.refresh_from_db()
    assert winner.is_winner is True
    assert room.status == RoomStatus.FINISHED
    assert room.winner_id == player.id


@pytest.mark.django_db
def test_loteria_rechaza_tablero_incompleto(room):
    player = join_room(room.code, "Ana")
    start_round(room)
    draw_next(room)
    with pytest.raises(ValidationError, match="faltan"):
        claim_loteria(player)


@pytest.mark.django_db
def test_loteria_rechaza_marcas_de_mas(room):
    player = join_room(room.code, "Ana")
    start_round(room)
    draw_next(room)
    # Marca las 16 casillas aunque solo se ha cantado una carta.
    for index in range(BOARD_SIZE):
        player = set_mark(player, index, True)
    with pytest.raises(ValidationError, match="no han salido"):
        claim_loteria(player)
    room.refresh_from_db()
    assert room.status == RoomStatus.PLAYING


@pytest.mark.django_db
def test_marcar_y_desmarcar(room):
    player = join_room(room.code, "Ana")
    player = set_mark(player, 3, True)
    player = set_mark(player, 3, True)
    assert player.marked == [3]
    player = set_mark(player, 3, False)
    assert player.marked == []
    with pytest.raises(ValidationError):
        set_mark(player, 99, True)


@pytest.mark.django_db
def test_otra_ronda_rebaraja_y_limpia_marcas(room):
    player = join_room(room.code, "Ana")
    start_round(room)
    draw_next(room)
    player = set_mark(player, 0, True)

    reset_to_lobby(room)
    room.refresh_from_db()
    player.refresh_from_db()
    assert room.status == RoomStatus.LOBBY
    assert room.round_number == 2
    assert room.drawn_count == 0
    assert player.marked == []
    assert player.is_winner is False


@pytest.mark.django_db
def test_endpoints_crear_unirse_y_consultar(api_client):
    created = api_client.post(reverse("loteria-room-list"), {}, format="json")
    assert created.status_code == 201
    code = created.data["room"]["code"]
    assert created.data["host_token"]

    joined = api_client.post(
        reverse("loteria-room-join", kwargs={"code": code}),
        {"name": "Ana"},
        format="json",
    )
    assert joined.status_code == 201
    assert joined.data["player_token"]
    assert len(joined.data["you"]["board"]) == BOARD_SIZE
    assert joined.data["you"]["board"][0]["name"]

    detail = api_client.get(reverse("loteria-room-detail", kwargs={"code": code}))
    assert detail.status_code == 200
    assert [p["name"] for p in detail.data["players"]] == ["Ana"]

    cards = api_client.get(reverse("loteria-cards"))
    assert cards.status_code == 200
    assert cards.data["count"] == DECK_SIZE


@pytest.mark.django_db
def test_join_con_codigo_inexistente_devuelve_400(api_client):
    response = api_client.post(
        reverse("loteria-room-join", kwargs={"code": "ZZZZZZ"}),
        {"name": "Ana"},
        format="json",
    )
    assert response.status_code == 400
