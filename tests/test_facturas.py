"""Pruebas de las facturas ficticias: la hoja de respuestas tiene que ser confiable.

Si esperado.json está mal, en la Fase 2 mediríamos a la IA contra una
respuesta equivocada. Por eso la hoja de respuestas también pasa por el molde.
"""

import json
from pathlib import Path

import pytest

from faro.modelos import Factura

CARPETA = Path(__file__).resolve().parents[1] / "data" / "facturas"


@pytest.fixture(scope="module")
def esperado() -> list[dict]:
    return json.loads((CARPETA / "esperado.json").read_text(encoding="utf-8"))


def test_hay_20_facturas_y_cada_una_tiene_su_pdf(esperado):
    assert len(esperado) == 20
    for f in esperado:
        assert (CARPETA / f["archivo"]).exists(), f"falta {f['archivo']}"


def test_todas_pasan_por_el_molde(esperado):
    for f in esperado:
        Factura(**f)  # si una no cumple, Pydantic lanza el error


def test_17_cuadran_y_3_van_a_revision(esperado):
    no_cuadran = {f["archivo"] for f in esperado if not Factura(**f).cuadra()}
    sembradas = {f["archivo"] for f in esperado if f["error_sembrado"]}
    assert len(no_cuadran) == 3
    assert no_cuadran == sembradas
