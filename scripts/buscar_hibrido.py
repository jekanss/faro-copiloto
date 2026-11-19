"""Busqueda hibrida en las fichas. Uso: python scripts/buscar_hibrido.py "tu pregunta"

Muestra lo que devolvio cada bibliotecario, como se calculo la votacion
y el texto de los pedazos ganadores (lo que se le entregaria al modelo).
"""

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
load_dotenv(RAIZ / ".env")

from faro.busqueda import K_RRF, buscar, referencias_en  # noqa: E402

pregunta = " ".join(sys.argv[1:])

with psycopg.connect(os.environ["DATABASE_URL"]) as con:
    ids, sentido, palabras = buscar(con, pregunta)
    todos = list({i for i, _ in sentido} | {i for i, _ in palabras})
    datos = {
        fila[0]: fila[1:]
        for fila in con.execute(
            "SELECT id, referencia, seccion, texto FROM fragmentos WHERE id = ANY(%s)",
            (todos,),
        )
    }


def nombre(id_):
    referencia, seccion, _ = datos[id_]
    return f"{referencia:<11} {seccion}"


def mostrar(titulo, lista, decimales):
    print(f"\n{titulo}")
    if not lista:
        print("   (no encontro nada)")
    for puesto, (id_, valor) in enumerate(lista, start=1):
        print(f"  {puesto:>2}  {valor:.{decimales}f}  {nombre(id_)}")


print(f'\nPregunta: "{pregunta}"')
print("Filtro por referencia:", ", ".join(referencias_en(pregunta)) or "ninguno")
mostrar("Bibliotecario 1, sentido (similitud coseno, de 0 a 1):", sentido, 3)
mostrar("Bibliotecario 2, palabras (BM25, otra escala):", palabras, 4)

puestos_sentido = {id_: p for p, (id_, _) in enumerate(sentido, start=1)}
puestos_palabras = {id_: p for p, (id_, _) in enumerate(palabras, start=1)}

print(f"\nVotacion RRF: cada lista le da 1/({K_RRF} + puesto). Top {len(ids)}:")
for id_ in ids:
    partes, total = [], 0.0
    for puestos in (puestos_sentido, puestos_palabras):
        p = puestos.get(id_)
        if p:
            partes.append(f"1/({K_RRF}+{p})")
            total += 1 / (K_RRF + p)
        else:
            partes.append("no aparece")
    print(f"  {total:.4f} = {' + '.join(partes):<26} {nombre(id_)}")

print("\nTexto de los pedazos ganadores (lo que recibiria el modelo):")
for puesto, id_ in enumerate(ids, start=1):
    _, _, texto = datos[id_]
    print(f"\n[{puesto}] {nombre(id_)}  (id {id_})")
    for linea in texto.strip().splitlines():
        print(f"    {linea}")