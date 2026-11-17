"""Pruebas del extractor que no llaman a OpenAI."""

from decimal import Decimal

from faro.extraccion import costo_usd


def test_costo_un_millon_de_cada_uno():
    uso = {"tokens_entrada": 1_000_000, "tokens_salida": 1_000_000}
    assert costo_usd(uso) == Decimal("2.25")


def test_costo_de_una_factura_real():
    # Los números de la FAC-01 con esfuerzo low.
    uso = {"tokens_entrada": 589, "tokens_salida": 392}
    assert costo_usd(uso) == Decimal("0.00093125")