"""Pruebas de las fichas técnicas: cada producto del catálogo tiene la suya."""

from pathlib import Path

from faro.datos import cargar_productos

CARPETA = Path(__file__).resolve().parents[1] / "data" / "fichas"


def test_cada_producto_tiene_su_ficha():
    faltan = [p.referencia for p in cargar_productos()
              if not (CARPETA / f"{p.referencia}.pdf").exists()]
    assert faltan == [], f"productos sin ficha: {faltan}"


def test_no_hay_fichas_huerfanas():
    """Una ficha sin producto es un documento que el RAG citaría sin respaldo."""
    referencias = {p.referencia for p in cargar_productos()}
    huerfanas = [f.stem for f in CARPETA.glob("*.pdf") if f.stem not in referencias]
    assert huerfanas == [], f"fichas sin producto: {huerfanas}"
