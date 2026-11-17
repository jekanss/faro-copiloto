"""Guardado de facturas en Postgres (Neon).

Cada factura entra con sus ítems en una sola transacción: o todo o nada.
Los valores viajan aparte del SQL (%s): el texto de una factura nunca se vuelve una orden.
"""

import os
from decimal import Decimal

import psycopg
from dotenv import load_dotenv

from faro.modelos import Factura

load_dotenv()


def guardar_factura(
    archivo: str,
    estado: str,
    motivo: str | None,
    factura: Factura | None,
    uso: dict | None,
    costo: Decimal | None,
) -> int:
    """Guarda la factura y sus ítems. Devuelve el id que le dio la base."""
    uso = uso or {}
    f = factura
    datos = (f.numero, f.proveedor_nit, f.fecha, f.subtotal, f.iva, f.total) if f else (None,) * 6

    with psycopg.connect(os.environ["DATABASE_URL"]) as con:
        factura_id = con.execute(
            """
            INSERT INTO facturas (
                archivo, estado, motivo,
                numero, proveedor_nit, fecha, subtotal, iva, total,
                modelo, esfuerzo, tokens_entrada, tokens_salida, tokens_razonamiento, costo_usd
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                archivo, estado, motivo,
                *datos,
                uso.get("modelo"), uso.get("esfuerzo"),
                uso.get("tokens_entrada"), uso.get("tokens_salida"), uso.get("tokens_razonamiento"),
                costo,
            ),
        ).fetchone()[0]

        if f:
            with con.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO items_factura (
                        factura_id, renglon, referencia, descripcion, cantidad, precio_unitario, subtotal
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    [
                        (factura_id, n, i.referencia, i.descripcion, i.cantidad, i.precio_unitario, i.subtotal)
                        for n, i in enumerate(f.items, start=1)
                    ],
                )

    return factura_id