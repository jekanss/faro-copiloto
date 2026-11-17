"""Pruebas de la API: verifican lo que antes revisamos a mano en el navegador.

Ninguna prueba toca OpenAI ni Neon: los guardianes lo prohíben.
Cada prueba pone un extractor falso, y el guardado falso anota lo que le pidieron guardar.
"""

from pathlib import Path

import httpx
import psycopg
import pytest
from fastapi.testclient import TestClient
from openai import APIConnectionError

from faro import db, extraccion
from faro.api import TAMANO_MAXIMO, app
from faro.modelos import Factura

cliente = TestClient(app)

RAIZ = Path(__file__).resolve().parent.parent
FACTURA = RAIZ / "data" / "facturas" / "FAC-01.pdf"

# Los números reales de la FAC-01 con esfuerzo low: cuestan USD 0.00093125.
USO_FALSO = {
    "modelo": "falso",
    "esfuerzo": "low",
    "tokens_entrada": 589,
    "tokens_salida": 392,
    "tokens_razonamiento": 192,
}


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
def guardados(monkeypatch):
    """Guardianes: prohíben OpenAI y cambian Neon por una libreta en memoria."""

    def prohibido(*args, **kwargs):
        raise AssertionError("Una prueba intentó llamar a OpenAI.")

    libreta = []

    def guardar_falso(archivo, estado, motivo, factura, uso, costo):
        libreta.append({"archivo": archivo, "estado": estado, "motivo": motivo, "factura": factura, "costo": costo})
        return 7

    monkeypatch.setattr(extraccion, "extraer_bytes", prohibido)
    monkeypatch.setattr(db, "guardar_factura", guardar_falso)
    return libreta


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


def test_factura_que_cuadra_queda_procesada_y_guardada(monkeypatch, guardados):
    monkeypatch.setattr(extraccion, "extraer_bytes", lambda contenido, nombre: (factura_ejemplo(), USO_FALSO))
    respuesta = subir_factura()
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["id"] == 7
    assert datos["archivo"] == "FAC-01.pdf"
    assert datos["tamano_bytes"] == FACTURA.stat().st_size
    assert datos["estado"] == "procesada"
    assert datos["motivo"] is None
    assert datos["factura"]["total"] == "94248"
    assert datos["costo_usd"] == "0.00093125"
    assert len(guardados) == 1
    assert guardados[0]["estado"] == "procesada"


def test_factura_que_no_cuadra_va_a_revision_y_se_guarda(monkeypatch, guardados):
    monkeypatch.setattr(
        extraccion, "extraer_bytes", lambda contenido, nombre: (factura_ejemplo(total="99999"), USO_FALSO)
    )
    respuesta = subir_factura()
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["estado"] == "para_revision"
    assert "cuadran" in datos["motivo"]
    assert datos["factura"]["total"] == "99999"
    assert guardados[0]["estado"] == "para_revision"


def test_lectura_invalida_va_a_revision_y_se_guarda_sin_datos(monkeypatch, guardados):
    def lectura_rota(contenido, nombre):
        Factura.model_validate({"numero": "X"})  # le faltan campos: lanza ValidationError

    monkeypatch.setattr(extraccion, "extraer_bytes", lectura_rota)
    respuesta = subir_factura()
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["estado"] == "para_revision"
    assert datos["factura"] is None
    assert datos["costo_usd"] is None
    assert guardados[0]["factura"] is None


def test_openai_caido_da_502_y_no_guarda_nada(monkeypatch, guardados):
    def openai_caido(contenido, nombre):
        raise APIConnectionError(request=httpx.Request("POST", "https://api.openai.com/v1/responses"))

    monkeypatch.setattr(extraccion, "extraer_bytes", openai_caido)
    respuesta = subir_factura()
    assert respuesta.status_code == 502
    assert guardados == []


def test_base_caida_da_503(monkeypatch):
    def base_caida(*args, **kwargs):
        raise psycopg.OperationalError("sin conexión")

    monkeypatch.setattr(extraccion, "extraer_bytes", lambda contenido, nombre: (factura_ejemplo(), USO_FALSO))
    monkeypatch.setattr(db, "guardar_factura", base_caida)
    respuesta = subir_factura()
    assert respuesta.status_code == 503


def test_pdf_disfrazado_da_415_y_no_guarda_nada(guardados):
    # Dice ser PDF por nombre y por tipo, pero por dentro es texto.
    respuesta = cliente.post(
        "/facturas", files={"pdf": ("factura.pdf", b"hola, no soy un PDF", "application/pdf")}
    )
    assert respuesta.status_code == 415
    assert guardados == []


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