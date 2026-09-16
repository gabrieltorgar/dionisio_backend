"""Tests del WebSocket de la lotería: canto en vivo y grito de lotería."""

import pytest
from asgiref.sync import sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator

from apps.loteria.cards import BOARD_SIZE
from apps.loteria.models import Room
from apps.loteria.routing import websocket_urlpatterns
from apps.loteria.services import create_room, draw_next, join_room

application = URLRouter(websocket_urlpatterns)


@sync_to_async
def make_room(**kwargs):
    return create_room(**kwargs)


@sync_to_async
def add_player(code: str, name: str):
    return join_room(code, name)


@sync_to_async
def deal_whole_deck(room_id: int) -> None:
    """Canta la baraja completa desde fuera del consumer (atajo de test)."""
    room = Room.objects.get(pk=room_id)
    while draw_next(room) is not None:
        pass


async def connect(code: str, token: str) -> WebsocketCommunicator:
    communicator = WebsocketCommunicator(
        application, f"/ws/loteria/{code}/?token={token}"
    )
    connected, _ = await communicator.connect()
    assert connected
    return communicator


async def drain_until(communicator: WebsocketCommunicator, kind: str, limit: int = 200):
    """Lee mensajes hasta encontrar el tipo buscado."""
    for _ in range(limit):
        message = await communicator.receive_json_from(timeout=5)
        if message["type"] == kind:
            return message
    raise AssertionError(f"No llegó ningún mensaje de tipo {kind}")


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_sala_desconocida_rechaza_la_conexion():
    communicator = WebsocketCommunicator(application, "/ws/loteria/ZZZZZZ/?token=x")
    connected, code = await communicator.connect()
    assert connected is False
    assert code == 4404


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_token_invalido_rechaza_la_conexion():
    room = await make_room()
    communicator = WebsocketCommunicator(
        application, f"/ws/loteria/{room.code}/?token=nope"
    )
    connected, close_code = await communicator.connect()
    assert connected is False
    assert close_code == 4403


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_partida_completa_en_vivo():
    room = await make_room(draw_interval_ms=15000)
    ana = await add_player(room.code, "Ana")
    beto = await add_player(room.code, "Beto")

    host = await connect(room.code, room.host_token)
    ana_ws = await connect(room.code, ana.token)
    beto_ws = await connect(room.code, beto.token)

    # Al conectarse, cada quien recibe su estado: el anfitrión sin tablero.
    host_state = await drain_until(host, "state")
    assert host_state["you"]["role"] == "host"
    ana_state = await drain_until(ana_ws, "state")
    assert len(ana_state["you"]["board"]) == BOARD_SIZE

    # Solo el anfitrión puede iniciar.
    await ana_ws.send_json_to({"action": "start"})
    error = await drain_until(ana_ws, "error")
    assert "anfitrión" in error["detail"]

    await host.send_json_to({"action": "start"})
    await drain_until(ana_ws, "round_started")
    ana_state = await drain_until(ana_ws, "state")
    board = [card["number"] for card in ana_state["you"]["board"]]

    # El anfitrión canta una carta a mano y llega a todos.
    await host.send_json_to({"action": "draw"})
    drawn = await drain_until(beto_ws, "card_drawn")
    assert drawn["card"]["name"]
    assert drawn["drawn_count"] == 1

    # Gritar lotería con el tablero a medias se rechaza y el juego sigue.
    await ana_ws.send_json_to({"action": "claim"})
    rejected = await drain_until(ana_ws, "claim_rejected")
    assert "faltan" in rejected["detail"]

    # Se canta toda la baraja y Ana marca su tablero completo.
    await deal_whole_deck(room.id)
    for index in range(BOARD_SIZE):
        await ana_ws.send_json_to({"action": "mark", "index": index})
    marks = await drain_until(ana_ws, "marks")
    assert marks["marked"]

    await ana_ws.send_json_to({"action": "claim"})
    win = await drain_until(beto_ws, "loteria")
    assert win["winner"]["name"] == "Ana"
    assert len(board) == BOARD_SIZE

    # Otra ronda: el anfitrión devuelve la sala a la espera.
    await host.send_json_to({"action": "reset"})
    await drain_until(ana_ws, "lobby")
    fresh = await drain_until(ana_ws, "state")
    assert fresh["room"]["status"] == "lobby"
    assert fresh["room"]["round"] == 2
    assert fresh["you"]["marked"] == []

    for communicator in (host, ana_ws, beto_ws):
        await communicator.disconnect()
