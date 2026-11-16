"""Pruebas de la API: verifican lo que antes revisamos a mano en el navegador."""

from fastapi.testclient import TestClient

from faro.api import app

cliente = TestClient(app)


def test_salud_responde_ok():
    respuesta = cliente.get("/salud")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok", "version": "0.1.0"}


def test_ruta_inexistente_da_404():
    respuesta = cliente.get("/no-existe")
    assert respuesta.status_code == 404