"""Experimento: ¿el embedding entiende la jerga del vendedor? ¿Distingue referencias?"""

from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

RAIZ = Path(__file__).resolve().parents[1]
load_dotenv(RAIZ / ".env")

cliente = OpenAI()
MODELO = "text-embedding-3-small"


def similitud(a, b):
    # Los vectores de OpenAI vienen con largo 1: el producto punto es el coseno.
    return sum(x * y for x, y in zip(a, b))


def comparar(pregunta, textos):
    respuesta = cliente.embeddings.create(model=MODELO, input=[pregunta, *textos])
    vectores = [d.embedding for d in respuesta.data]
    print(f'\nPregunta: "{pregunta}"  (vector de {len(vectores[0])} numeros)')
    for texto, vector in zip(textos, vectores[1:]):
        print(f"  {similitud(vectores[0], vector):.3f}  {texto}")
    return respuesta.usage.total_tokens


tokens = comparar(
    "pastillas pa'l Spark",
    [
        "Pastilla de freno delantera para Chevrolet Spark 2010 a 2018",
        "Filtro de aceite para Renault Logan",
        "Politica de devoluciones: 30 dias con factura",
    ],
)
tokens += comparar("BRK-2210", ["BRK-2201", "BRK-9999", "Pastilla de freno"])

print(f"\nTokens usados en total: {tokens}")