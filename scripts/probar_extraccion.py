"""Prueba manual: extrae una factura y la muestra en pantalla."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from faro.extraccion import extraer_factura  # noqa: E402

archivo = sys.argv[1] if len(sys.argv) > 1 else "data/facturas/FAC-01.pdf"
factura, uso = extraer_factura(archivo)
print(factura.model_dump_json(indent=2))
print("Cuadra:", factura.cuadra())
print("Uso:", uso)