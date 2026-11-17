"""Aplica en orden las migraciones de migraciones/ que todavía no estén en la base.

Se puede correr las veces que quieras: lo ya aplicado se salta.
"""

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[1]
load_dotenv(RAIZ / ".env")

with psycopg.connect(os.environ["DATABASE_URL"]) as con:
    con.execute(
        "CREATE TABLE IF NOT EXISTS migraciones ("
        " nombre TEXT PRIMARY KEY, aplicada_en TIMESTAMPTZ NOT NULL DEFAULT now())"
    )
    hechas = {fila[0] for fila in con.execute("SELECT nombre FROM migraciones")}

    for archivo in sorted((RAIZ / "migraciones").glob("*.sql")):
        if archivo.name in hechas:
            print(f"ya aplicada: {archivo.name}")
            continue
        con.execute(archivo.read_text(encoding="utf-8"))
        con.execute("INSERT INTO migraciones (nombre) VALUES (%s)", (archivo.name,))
        print(f"aplicada:    {archivo.name}")

print("Base al día.")