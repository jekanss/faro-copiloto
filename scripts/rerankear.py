"""Muestra el proceso completo: bibliotecarios, votacion y reranker.
Uso: python scripts/rerankear.py "tu pregunta"
"""

import os
import sys
import time
from pathlib import Path

import psycopg
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
load_dotenv(RAIZ / ".env")

from faro.busqueda import embedding, fusionar_rrf  # noqa: E402
from faro.busqueda import por_palabras, por_sentido  # noqa: E402
from faro.busqueda import referencias_en  # noqa: E402
from faro.reranking import CANDIDATOS, reordenar  # noqa: E402

SQL_TEXTO = (
    "SELECT id, texto_para_buscar "
    "FROM fragmentos WHERE id = ANY(%s)"
)


def describir(texto):
    """'Nombre (REF, Cat). Seccion: ...' -> 'REF  Seccion  Nombre'."""
    nombre, _, resto = texto.partition(" (")
    ref = resto.split(",")[0]
    _, _, cuerpo = resto.partition("). ")
    seccion = cuerpo.split(":")[0]
    return f"{ref:<11} {seccion:<23} {nombre}"


def etiquetas(con, ids):
    """id -> 'REF  Seccion  Nombre'."""
    if not ids:
        return {}
    filas = con.execute(SQL_TEXTO, (list(ids),)).fetchall()
    return {i: describir(t) for i, t in filas}


def paso(titulo):
    print(f"\n=== {titulo} ===", flush=True)


def linea(texto):
    print(texto, flush=True)


pregunta = " ".join(sys.argv[1:])
tiempos = {}
linea(f"Pregunta: {pregunta}")

with psycopg.connect(os.environ["DATABASE_URL"]) as con:
    paso("1. Referencias exactas")
    referencias = referencias_en(pregunta) or None
    linea(f"  {referencias or 'ninguna: busca en todas'}")

    paso("2. Bibliotecario 1: por sentido")
    t = time.perf_counter()
    vector = embedding(pregunta)
    sentido = por_sentido(con, vector, referencias)
    tiempos["sentido"] = time.perf_counter() - t
    nombres = etiquetas(con, [i for i, _ in sentido])
    for k, (i, s) in enumerate(sentido, 1):
        linea(f"  {k:>2}. [{i:>3}] {s:.3f}  {nombres[i]}")

    paso("3. Bibliotecario 2: por palabras (BM25)")
    t = time.perf_counter()
    palabras = por_palabras(con, pregunta, referencias)
    tiempos["palabras"] = time.perf_counter() - t
    nombres = etiquetas(con, [i for i, _ in palabras])
    for k, (i, s) in enumerate(palabras, 1):
        linea(f"  {k:>2}. [{i:>3}] {s:5.2f}  {nombres[i]}")

    paso("4. Votacion RRF")
    ids_sentido = [i for i, _ in sentido]
    ids_palabras = [i for i, _ in palabras]
    votacion = fusionar_rrf([ids_sentido, ids_palabras])
    candidatos = votacion[:CANDIDATOS]
    nombres = etiquetas(con, candidatos)
    linea(f"  Pasan al reranker: {len(candidatos)}")
    linea("  Top 5 ANTES:")
    for k, i in enumerate(candidatos[:5], 1):
        linea(f"  {k:>2}. [{i:>3}] {nombres[i]}")

    paso("5. Reranker: lee pregunta y pedazos juntos")
    linea("  Llamando al modelo...")
    t = time.perf_counter()
    final, puntaje, uso = reordenar(con, pregunta, candidatos)
    tiempos["reranker"] = time.perf_counter() - t
    linea("  Nota de cada candidato (orden de la votacion):")
    for k, i in enumerate(candidatos, 1):
        nota = puntaje.get(i, 0)
        linea(f"  {k:>2}. [{i:>3}] {nota:>2}/10  {nombres[i]}")

    paso("6. Top 5 DESPUES del reranker")
    for k, i in enumerate(final, 1):
        nota = puntaje.get(i, 0)
        linea(f"  {k:>2}. [{i:>3}] {nota:>2}/10  {nombres[i]}")

paso("Costo y tiempos")
if uso:
    entrada = uso["tokens_entrada"]
    salida = uso["tokens_salida"]
    razon = uso["tokens_razonamiento"]
    linea(f"  Tokens entrada: {entrada}")
    linea(f"  Tokens salida: {salida} ({razon} razonando)")
    linea(f"  Costo: USD {uso['costo_usd']:.5f}")
for etapa, segundos in tiempos.items():
    linea(f"  {etapa}: {segundos:.2f} s")