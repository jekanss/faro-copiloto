"""Pruebas de la API: verifican lo que antes revisamos a mano en el navegador."""

from pathlib import Path

from fastapi.testclient import TestClient

from faro.api import TAMANO_MAXIMO, app

cliente = TestClient(app)

RAIZ = Path(__file__).resolve().parent.parent
FACTURA = RAIZ / "data" / "facturas" / "FAC-01.pdf"


def test_salud_responde_ok():
    respuesta = cliente.get("/salud")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok", "version": "0.1.0"}


def test_ruta_inexistente_da_404():
    respuesta = cliente.get("/no-existe")
    assert respuesta.status_code == 404


def test_factura_pdf_se_recibe():
    with FACTURA.open("rb") as archivo:
        respuesta = cliente.post(
            "/facturas", files={"pdf": ("FAC-01.pdf", archivo, "application/pdf")}
        )
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["archivo"] == "FAC-01.pdf"
    assert datos["tamano_bytes"] == FACTURA.stat().st_size
    assert datos["estado"] == "recibida"


def test_pdf_disfrazado_da_415():
    # Dice ser PDF por nombre y por tipo, pero por dentro es texto.
    respuesta = cliente.post(
        "/facturas", files={"pdf": ("factura.pdf", b"hola, no soy un PDF", "application/pdf")}
    )
    assert respuesta.status_code == 415


def test_archivo_vacio_da_400():
    respuesta = cliente.post(
        "/facturas", files={"pdf": ("vacia.pdf", b"", "application/pdf")}
    )
    assert respuesta.status_code == 400


def test_archivo_gigante_da_413():
    gigante = b"%PDF" + b"0" * TAMANO_MAXIMO
    respuesta = cliente.post(
        "/facturas", files={"pdf": ("gigante.pdf", gigante, "application/pdf")}
    )
    assert respuesta.status_code == 413


def test_sin_archivo_da_422():
    respuesta = cliente.post("/facturas")
    assert respuesta.status_code == 422