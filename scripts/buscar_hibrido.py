"""Busqueda hibrida en las fichas. Uso: python scripts/buscar_hibrido.py "tu pregunta" """

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
load_dotenv(RAIZ / ".env")

from faro.busqueda import K_RRF, buscar  # noqa: E402

pregunta = " ".join(sys.argv[1:])

with psycopg.connect(os.environ["DATABASE_URL"]) as con:
    ids, sentido, palabras = buscar(con, pregunta)
    datos = {
        fila[0]: fila[1:]
        for fila in con.execute(
            "SELECT id, referencia, seccion FROM fragmentos WHERE id = ANY(%s)", (ids,)
        )
    }


def puesto(lista, id_):
    return lista.index(id_) + 1 if id_ in lista else None


print(f'\nPregunta: "{pregunta}"')
print("  sentido  palabras  puntaje  referencia   seccion")
for id_ in ids:
    ps, pp = puesto(sentido, id_), puesto(palabras, id_)
    total = sum(1 / (K_RRF + p) for p in (ps, pp) if p)
    referencia, seccion = datos[id_]
    print(f"  {ps or '-':>7}  {pp or '-':>8}  {total:.4f}  {referencia:<11}  {seccion}")