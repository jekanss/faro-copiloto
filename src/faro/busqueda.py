"""Busqueda hibrida: sentido (vectores) + palabras (texto), juntadas con RRF."""

from openai import OpenAI

MODELO = "text-embedding-3-small"  # el mismo con que se cargaron las fichas
K_RRF = 60  # constante estandar del paper de RRF
POR_LISTA = 10  # cuantos pedazos trae cada bibliotecario


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


def por_sentido(con, literal, n=POR_LISTA):
    """Bibliotecario 1: los n pedazos mas cercanos en significado."""
    filas = con.execute(
        """
        SELECT id FROM fragmentos
        WHERE modelo_embedding = %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """,
        (MODELO, literal, n),
    ).fetchall()
    return [f[0] for f in filas]


def por_palabras(con, pregunta, n=POR_LISTA):
    """Bibliotecario 2: pedazos con alguna palabra de la pregunta (O, no Y)."""
    filas = con.execute(
        """
        WITH q AS (
            SELECT string_agg(quote_literal(l), ' | ')::tsquery AS q
            FROM unnest(tsvector_to_array(to_tsvector('spanish', %s))) AS l
        )
        SELECT f.id FROM fragmentos f, q
        WHERE f.palabras @@ q.q
        ORDER BY ts_rank(f.palabras, q.q) DESC
        LIMIT %s
        """,
        (pregunta, n),
    ).fetchall()
    return [f[0] for f in filas]


def buscar(con, pregunta, n=5):
    """Pregunta a los dos bibliotecarios y junta sus listas por votacion."""
    sentido = por_sentido(con, embedding(pregunta))
    palabras = por_palabras(con, pregunta)
    return fusionar_rrf([sentido, palabras])[:n], sentido, palabras