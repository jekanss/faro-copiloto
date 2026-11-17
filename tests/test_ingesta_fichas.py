from pathlib import Path

import pytest

from faro.fichas import leer_texto, partir_ficha

FICHA = Path(__file__).resolve().parents[1] / "data" / "fichas" / "FAR-PF-001.pdf"


def test_parte_la_ficha_por_secciones():
    secciones = [f.seccion for f in partir_ficha(leer_texto(FICHA))]
    assert secciones == ["Especificaciones", "Vehículos compatibles", "Garantía", "Notas de instalación"]


def test_cada_fragmento_lleva_su_cabecera():
    garantia = next(f for f in partir_ficha(leer_texto(FICHA)) if f.seccion == "Garantía")
    assert garantia.texto.startswith("6 meses")
    assert garantia.texto_para_buscar.startswith("Pastillas de freno delanteras Bosch (FAR-PF-001, Frenos)")


def test_el_pie_no_entra_a_ningun_fragmento():
    assert all("Documento ficticio" not in f.texto for f in partir_ficha(leer_texto(FICHA)))


def test_texto_sin_cabecera_falla():
    with pytest.raises(ValueError):
        partir_ficha("Una linea\nOtra linea\nSin referencia")