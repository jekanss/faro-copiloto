"""Busqueda hibrida: sentido (vectores) + palabras (texto), juntadas con RRF.

Si la pregunta trae una referencia exacta (FAR-PF-002), las dos busquedas
se hacen solo sobre los pedazos de ese producto: lo que se resuelve con SQL
no se le pide a la IA.
"""

import re

from openai import OpenAI

MODELO = "text-embedding-3-small"  # el mismo con que se cargaron las fichas
K_RRF = 60  # constante estandar del paper de RRF
POR_LISTA = 10  # cuantos pedazos trae cada bibliotecario
PATRON_REFERENCIA = re.compile(r"\bFAR-[A-Z]{2}-\d{3}\b", re.IGNORECASE)  # formato de Faro
INDICE_BM25 = "fragmentos_palabras_bm25"  # creado en la migracion 006


def referencias_en(pregunta):
    """Las referencias exactas que trae la pregunta, en mayuscula y sin repetir."""
    return sorted({r.upper() for r in PATRON_REFERENCIA.findall(pregunta)})


def fusionar_rrf(listas, k=K_RRF):
    """Junta listas ordenadas de ids. Cada id suma 1/(k + puesto) por lista."""
    puntaje = {}
    for lista in listas:
        for puesto, id_ in enumerate(lista, start=1):
            puntaje[id_] = puntaje.get(id_, 0.0) + 1.0 / (k + puesto)
    return sorted(puntaje, key=lambda i: puntaje[i], reverse=True)


def embedding(pregunta):
    """Bibliotecario 1, paso 1: la pregunta convertida en 1.536 numeros."""
    datos = OpenAI().embeddings.create(model=MODELO, input=pregunta)
    return "[" + ",".join(str(n) for n in datos.data[0].embedding) + "]"


def por_sentido(con, literal, referencias=None, n=POR_LISTA):
    """Bibliotecario 1: (id, similitud coseno) de los n pedazos mas cercanos."""
    filas = con.execute(
        """
        SELECT id, 1 - (embedding <=> %s::vector) AS similitud FROM fragmentos
        WHERE modelo_embedding = %s
          AND (%s::text[] IS NULL OR referencia = ANY(%s::text[]))
        ORDER BY embedding <=> %s::vector, id
        LIMIT %s
        """,
        (literal, MODELO, referencias, referencias, literal, n),
    ).fetchall()
    return [(f[0], float(f[1])) for f in filas]


def por_palabras(con, pregunta, referencias=None, n=POR_LISTA):
    """Bibliotecario 2: (id, puntaje BM25) de pedazos con alguna palabra (O, no Y).

    Mismos candidatos que antes (el O con @@); solo cambia el orden:
    BM25 sabe que tan rara es cada palabra y ts_rank no.
    <@> da el puntaje en negativo; se le cambia el signo para que mas alto sea mejor.
    Nota de escala: ordenar por el valor con signo cambiado puede saltarse el
    atajo top-K del indice. Con cientos de pedazos no importa; con miles, revisar.
    """
    filas = con.execute(
        """
        WITH q AS (
            SELECT string_agg(quote_literal(l), ' | ')::tsquery AS q
            FROM unnest(tsvector_to_array(to_tsvector('es_sin_tildes', %s))) AS l
        )
        SELECT f.id,
               -(f.palabras <@> to_bm25query(to_tsvector('es_sin_tildes', %s), %s)) AS rango
        FROM fragmentos f, q
        WHERE f.palabras @@ q.q
          AND (%s::text[] IS NULL OR f.referencia = ANY(%s::text[]))
        ORDER BY rango DESC, f.id
        LIMIT %s
        """,
        (pregunta, pregunta, INDICE_BM25, referencias, referencias, n),
    ).fetchall()
    return [(f[0], float(f[1])) for f in filas]


def buscar(con, pregunta, n=5):
    """Filtra por referencia si la hay, pregunta a los dos y junta por votacion."""
    referencias = referencias_en(pregunta) or None
    sentido = por_sentido(con, embedding(pregunta), referencias)
    palabras = por_palabras(con, pregunta, referencias)
    ids = fusionar_rrf([[i for i, _ in sentido], [i for i, _ in palabras]])[:n]
    return ids, sentido, palabras