"""Pruebas de la API: verifican lo que antes revisamos a mano en el navegador.

Ninguna prueba llama a OpenAI: el guardián lo prohíbe y cada prueba
pone un extractor falso que responde lo que necesitamos.
"""

from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from openai import APIConnectionError

from faro import extraccion
from faro.api import TAMANO_MAXIMO, app
from faro.modelos import Factura

cliente = TestClient(app)

RAIZ = Path(__file__).resolve().parent.parent
FACTURA = RAIZ / "data" / "facturas" / "FAC-01.pdf"

USO_FALSO = {"modelo": "falso", "esfuerzo": "low", "tokens_entrada": 0, "tokens_salida": 0, "tokens_razonamiento": 0}


def factura_ejemplo(total: str = "94248") -> Factura:
    """Factura que cuadra con el total por defecto; con otro total, no cuadra."""
    return Factura(
        numero="IMP-7891",
        proveedor_nit="900452318-4",
        fecha="2026-10-15",
        items=[
            {
                "referencia": "FAR-FA-003",
                "descripcion": "Filtro de aceite Fram",
                "cantidad": 4,
                "precio_unitario": "19800",
                "subtotal": "79200",
            }
        ],
        subtotal="79200",
        iva="15048",
        total=total,
    )


@pytest.fixture(autouse=True)
def guardian_sin_openai(monkeypatch):
    """Si una prueba intenta llamar a OpenAI de verdad, falla."""

    def prohibido(*args, **kwargs):
        raise AssertionError("Una prueba intentó llamar a OpenAI.")

    monkeypatch.setattr(extraccion, "extraer_bytes", prohibido)


def subir_factura():
    with FACTURA.open("rb") as archivo:
        return cliente.post("/facturas", files={"pdf": ("FAC-01.pdf", archivo, "application/pdf")})


def test_salud_responde_ok():
    respuesta = cliente.get("/salud")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok", "version": "0.1.0"}


def test_ruta_inexistente_da_404():
    respuesta = cliente.get("/no-existe")
    assert respuesta.status_code == 404


def test_factura_que_cuadra_queda_procesada(monkeypatch):
    monkeypatch.setattr(extraccion, "extraer_bytes", lambda contenido, nombre: (factura_ejemplo(), USO_FALSO))
    respuesta = subir_factura()
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["archivo"] == "FAC-01.pdf"
    assert datos["tamano_bytes"] == FACTURA.stat().st_size
    assert datos["estado"] == "procesada"
    assert datos["motivo"] is None
    assert datos["factura"]["total"] == "94248"


def test_factura_que_no_cuadra_va_a_revision(monkeypatch):
    monkeypatch.setattr(
        extraccion, "extraer_bytes", lambda contenido, nombre: (factura_ejemplo(total="99999"), USO_FALSO)
    )
    respuesta = subir_factura()
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["estado"] == "para_revision"
    assert "cuadran" in datos["motivo"]
    assert datos["factura"]["total"] == "99999"


def test_lectura_invalida_va_a_revision_y_no_tumba_la_api(monkeypatch):
    def lectura_rota(contenido, nombre):
        Factura.model_validate({"numero": "X"})  # le faltan campos: lanza ValidationError

    monkeypatch.setattr(extraccion, "extraer_bytes", lectura_rota)
    respuesta = subir_factura()
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["estado"] == "para_revision"
    assert datos["factura"] is None


def test_openai_caido_da_502(monkeypatch):
    def openai_caido(contenido, nombre):
        raise APIConnectionError(request=httpx.Request("POST", "https://api.openai.com/v1/responses"))

    monkeypatch.setattr(extraccion, "extraer_bytes", openai_caido)
    respuesta = subir_factura()
    assert respuesta.status_code == 502


def test_pdf_disfrazado_da_415():
    # Dice ser PDF por nombre y por tipo, pero por dentro es texto.
    respuesta = cliente.post(
        "/facturas", files={"pdf": ("factura.pdf", b"hola, no soy un PDF", "application/pdf")}
    )
    assert respuesta.status_code == 415


def test_archivo_vacio_da_400():
    respuesta = cliente.post("/facturas", files={"pdf": ("vacia.pdf", b"", "application/pdf")})
    assert respuesta.status_code == 400


def test_archivo_gigante_da_413():
    gigante = b"%PDF" + b"0" * TAMANO_MAXIMO
    respuesta = cliente.post("/facturas", files={"pdf": ("gigante.pdf", gigante, "application/pdf")})
    assert respuesta.status_code == 413


def test_sin_archivo_da_422():
    respuesta = cliente.post("/facturas")
    assert respuesta.status_code == 422