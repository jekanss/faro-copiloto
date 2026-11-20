"""Reranking: el jefe de bodega que abre las cajas.

La busqueda hibrida trae candidatos baratos; aqui gpt-5-mini lee la
pregunta y todos los pedazos juntos (listwise), les pone nota de 0 a 10
y deja pasar solo los que llegan al MINIMO.
Los pedazos van ordenados por id, no por puesto: asi no se deja llevar
por el que va primero (sesgo de posicion).
"""

import os

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from faro.busqueda import embedding, fusionar_rrf
from faro.busqueda import por_palabras, por_sentido, referencias_en
from faro.extraccion import costo_usd

load_dotenv()

MODELO = os.getenv("OPENAI_MODEL", "gpt-5-mini")
ESFUERZO = "low"
CANDIDATOS = 20  # cuantos entran al reranker
MINIMO = 3  # nota minima para pasar al modelo que responde

INSTRUCCIONES = """Eres el jefe de bodega de una distribuidora de repuestos.
Te llega una pregunta y una lista de pedazos de fichas tecnicas, cada uno con su id.

Antes de calificar:
1. Saca TODAS las condiciones de la pregunta: tipo de producto, vehiculo, tema
   (garantia, instalacion, especificaciones...).
2. Si la pregunta nombra un vehiculo, usa los pedazos de "Vehiculos compatibles"
   para saber cuales referencias le sirven a ESE vehiculo.

Califica cada pedazo de 0 a 10:
- 10: es de una referencia que cumple todas las condiciones y trata el tema preguntado.
- 6: es el pedazo de "Vehiculos compatibles" que demuestra que esa referencia
  le sirve al vehiculo (el puente).
- 3: es de la referencia correcta pero de otro tema.
- 0: cualquier otro caso, incluida una referencia del mismo tipo de producto
  que no se demostro compatible con el vehiculo.

Si ningun pedazo de "Vehiculos compatibles" habla del vehiculo de la pregunta,
no castigues por vehiculo: califica solo por tipo de producto y tema.
Califica todos los ids, uno por uno. En el campo id va solo el numero.
No inventes ids.
"""


class Puntaje(BaseModel):
    id: str
    puntaje: int


class Calificacion(BaseModel):
    puntajes: list[Puntaje]


def reordenar(con, pregunta, candidatos, n=5):
    """Devuelve (hasta n ids con nota >= MINIMO, nota por id, uso)."""
    if not candidatos:
        return [], {}, None
    filas = con.execute(
        "SELECT id, texto_para_buscar FROM fragmentos "
        "WHERE id = ANY(%s) ORDER BY id",
        (list(candidatos),),
    ).fetchall()
    bloque = "\n\n".join(f"[id {i}]\n{texto}" for i, texto in filas)
    respuesta = OpenAI().responses.parse(
        model=MODELO,
        reasoning={"effort": ESFUERZO},
        instructions=INSTRUCCIONES,
        input=f"Pregunta: {pregunta}\n\nPedazos:\n\n{bloque}",
        text_format=Calificacion,
    )
    por_texto = {str(i): i for i, _ in filas}
    puntaje = {}
    for p in respuesta.output_parsed.puntajes:
        id_ = por_texto.get(p.id.strip())
        if id_ is not None:  # un id inventado se ignora
            puntaje[id_] = max(0, min(10, p.puntaje))
    puesto_rrf = {id_: k for k, id_ in enumerate(candidatos)}
    orden = sorted(
        candidatos,
        key=lambda i: (-puntaje.get(i, 0), puesto_rrf[i]),
    )
    aprobados = [i for i in orden if puntaje.get(i, 0) >= MINIMO]
    detalle = respuesta.usage.output_tokens_details
    uso = {
        "modelo": MODELO,
        "esfuerzo": ESFUERZO,
        "tokens_entrada": respuesta.usage.input_tokens,
        "tokens_salida": respuesta.usage.output_tokens,
        "tokens_razonamiento": detalle.reasoning_tokens if detalle else 0,
    }
    uso["costo_usd"] = costo_usd(uso)
    return aprobados[:n], puntaje, uso


def buscar_con_reranking(con, pregunta, n=5):
    """Como buscar(), pero la votacion deja pasar CANDIDATOS
    y el reranker elige hasta n que lleguen al MINIMO."""
    referencias = referencias_en(pregunta) or None
    sentido = por_sentido(con, embedding(pregunta), referencias)
    palabras = por_palabras(con, pregunta, referencias)
    listas = [[i for i, _ in sentido], [i for i, _ in palabras]]
    candidatos = fusionar_rrf(listas)[:CANDIDATOS]
    final, puntaje, uso = reordenar(con, pregunta, candidatos, n)
    return final, candidatos, puntaje, uso