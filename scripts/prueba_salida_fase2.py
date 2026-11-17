"""Prueba de salida de la Fase 2: las 20 facturas por el servicio, de punta a punta.

Sube cada PDF a POST /facturas (OpenAI y Neon de verdad), luego lee de la base
lo que quedó guardado y lo compara con la hoja de respuestas.
Gasta plata y escribe en la base: no es una prueba de pytest.
"""

import json
import os
import sys
from decimal import Decimal
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from fastapi.testclient import TestClient

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
load_dotenv(RAIZ / ".env")

from faro.api import app  # noqa: E402

CARPETA = RAIZ / "data" / "facturas"
esperadas = json.loads((CARPETA / "esperado.json").read_text(encoding="utf-8"))
cliente = TestClient(app)


def leer_de_la_base(con, factura_id):
    """Lo que de verdad quedó guardado, no lo que respondió la API."""
    f = con.execute(
        "SELECT numero, proveedor_nit, fecha, subtotal, iva, total, estado, costo_usd"
        " FROM facturas WHERE id = %s",
        (factura_id,),
    ).fetchone()
    items = con.execute(
        "SELECT referencia, cantidad, precio_unitario, subtotal"
        " FROM items_factura WHERE factura_id = %s ORDER BY renglon",
        (factura_id,),
    ).fetchall()
    return f, items


def coincide(f, items, esp) -> bool:
    """Compara lo guardado con la hoja de respuestas, la plata como Decimal."""
    cabecera = (f[0], f[1], str(f[2]), f[3], f[4], f[5]) == (
        esp["numero"],
        esp["proveedor_nit"],
        esp["fecha"],
        Decimal(str(esp["subtotal"])),
        Decimal(str(esp["iva"])),
        Decimal(str(esp["total"])),
    )
    renglones = [tuple(r) for r in items] == [
        (i["referencia"], int(i["cantidad"]), Decimal(str(i["precio_unitario"])), Decimal(str(i["subtotal"])))
        for i in esp["items"]
    ]
    return cabecera and renglones


n = len(esperadas)
bien = 0
costo_total = Decimal("0")
print(f"Prueba de salida: {n} facturas por POST /facturas y de vuelta desde Neon\n", flush=True)

with psycopg.connect(os.environ["DATABASE_URL"]) as con:
    for idx, esp in enumerate(esperadas, start=1):
        archivo = esp["archivo"]
        debe = "procesada" if esp["error_sembrado"] is None else "para_revision"
        print(f"[{idx}/{n}] {archivo}...", end=" ", flush=True)

        with (CARPETA / archivo).open("rb") as pdf:
            r = cliente.post("/facturas", files={"pdf": (archivo, pdf, "application/pdf")})
        if r.status_code != 201:
            print(f"HTTP {r.status_code}: {r.text}", flush=True)
            continue

        datos = r.json()
        f, items = leer_de_la_base(con, datos["id"])
        estado_ok = datos["estado"] == debe == f[6]
        datos_ok = f[0] is not None and coincide(f, items, esp)
        costo_total += f[7] or Decimal("0")
        if estado_ok and datos_ok:
            bien += 1

        print(
            f"id={datos['id']:<3} {datos['estado']:<13} "
            f"estado {'OK' if estado_ok else 'MAL (esperaba ' + debe + ')'}  "
            f"base {'OK' if datos_ok else 'MAL'}",
            flush=True,
        )

print()
print(f"Correctas de punta a punta: {bien}/{n}")
print(f"Costo guardado en la base: ${costo_total:.4f}  |  promedio: ${costo_total / n:.6f} por factura")
print("CRITERIO DE SALIDA CUMPLIDO" if bien == n else "CRITERIO DE SALIDA NO CUMPLIDO")