"""Mide el extractor contra la hoja de respuestas (data/facturas/esperado.json).

Corre las 20 facturas, compara campo por campo y suma el costo.
Muestra el progreso en vivo. Gasta plata en cada corrida: no es una prueba de pytest.
"""

import json
import sys
import time
from decimal import Decimal
from pathlib import Path

from pydantic import ValidationError

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from faro.extraccion import extraer_factura  # noqa: E402

CARPETA = RAIZ / "data" / "facturas"

# Dólares por millón de tokens. Verificar en la página de precios de OpenAI.
PRECIO_ENTRADA = Decimal("0.25")
PRECIO_SALIDA = Decimal("2.00")

CAMPOS = ["numero", "proveedor_nit", "fecha", "items", "subtotal", "iva", "total"]


def normalizar_items(items):
    """Convierte los ítems a una forma comparable: números como números."""
    return [
        (
            i["referencia"],
            int(i["cantidad"]),
            Decimal(str(i["precio_unitario"])),
            Decimal(str(i["subtotal"])),
        )
        for i in items
    ]


def comparar(extraida: dict, esperada: dict) -> list[str]:
    """Devuelve los campos que no coinciden con la hoja de respuestas."""
    malos = []
    for campo in CAMPOS:
        a, b = extraida[campo], esperada[campo]
        if campo == "items":
            iguales = normalizar_items(a) == normalizar_items(b)
        elif campo in ("subtotal", "iva", "total"):
            iguales = Decimal(str(a)) == Decimal(str(b))
        else:
            iguales = str(a) == str(b)
        if not iguales:
            malos.append(campo)
    return malos


esperadas = json.loads((CARPETA / "esperado.json").read_text(encoding="utf-8"))
n = len(esperadas)
aciertos_campo = {c: 0 for c in CAMPOS}
perfectas = 0
cuadre_bien = 0
fallos_forma = []
costo_total = Decimal("0")
inicio = time.time()

print(f"Midiendo {n} facturas con el extractor...\n", flush=True)

for idx, esp in enumerate(esperadas, start=1):
    archivo = esp["archivo"]
    debe_cuadrar = esp["error_sembrado"] is None
    print(f"[{idx}/{n}] {archivo} leyendo...", end=" ", flush=True)
    t0 = time.time()

    try:
        factura, uso = extraer_factura(CARPETA / archivo)
    except ValidationError as e:
        fallos_forma.append(archivo)
        print(f"FALLO DE FORMA ({e.error_count()} errores): va a revisión  ({time.time() - t0:.0f} s)", flush=True)
        continue

    costo = (
        uso["tokens_entrada"] * PRECIO_ENTRADA + uso["tokens_salida"] * PRECIO_SALIDA
    ) / 1_000_000
    costo_total += costo

    malos = comparar(factura.model_dump(mode="json"), esp)
    for c in CAMPOS:
        if c not in malos:
            aciertos_campo[c] += 1
    if not malos:
        perfectas += 1

    cuadra = factura.cuadra()
    if cuadra == debe_cuadrar:
        cuadre_bien += 1
        nota = ""
    else:
        nota = "  <-- cuadre equivocado"

    estado = "OK" if not malos else "MAL en " + ", ".join(malos)
    print(f"{estado}  cuadra={cuadra}  ${costo:.4f}  ({time.time() - t0:.0f} s){nota}", flush=True)

procesadas = n - len(fallos_forma)
print()
print(f"Facturas: {n}  |  perfectas: {perfectas}/{n}  |  fallos de forma: {len(fallos_forma)}")
print(f"Cuadre correcto: {cuadre_bien}/{procesadas}")
print("Aciertos por campo:")
for c in CAMPOS:
    print(f"  {c:<14} {aciertos_campo[c]}/{n}")
if procesadas:
    print(f"Costo total: ${costo_total:.4f}  |  promedio por factura: ${costo_total / procesadas:.4f}")
print(f"Tiempo total: {time.time() - inicio:.0f} s")