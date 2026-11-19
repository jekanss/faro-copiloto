"""Busca en las fichas por significado. Uso: python scripts/buscar.py "tu pregunta" """

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from openai import OpenAI

RAIZ = Path(__file__).resolve().parents[1]
load_dotenv(RAIZ / ".env")

MODELO = "text-embedding-3-small"  # el mismo con que se cargaron las fichas

pregunta = " ".join(sys.argv[1:])
vector = OpenAI().embeddings.create(model=MODELO, input=pregunta).data[0].embedding
literal = "[" + ",".join(str(n) for n in vector) + "]"

with psycopg.connect(os.environ["DATABASE_URL"]) as con:
    filas = con.execute(
        """
        SELECT referencia, seccion, 1 - (embedding <=> %s::vector) AS similitud, texto
        FROM fragmentos
        WHERE modelo_embedding = %s
        ORDER BY embedding <=> %s::vector
        LIMIT 5
        """,
        (literal, MODELO, literal),
    ).fetchall()

print(f'\nPregunta: "{pregunta}"')
for referencia, seccion, similitud, texto in filas:
    print(f"  {similitud:.3f}  {referencia}  {seccion:<22} {texto.splitlines()[0][:60]}")