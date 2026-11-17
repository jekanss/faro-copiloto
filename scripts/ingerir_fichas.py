"""Carga las fichas en Neon: las parte, calcula sus vectores y guarda solo lo que cambió.

Se puede correr las veces que quieras: lo que no cambió no se vuelve a pagar.
"""

import hashlib
import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from openai import OpenAI

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
load_dotenv(RAIZ / ".env")

from faro.fichas import leer_texto, partir_ficha  # noqa: E402

MODELO = "text-embedding-3-small"
PRECIO_USD_POR_MILLON = 0.02  # precio de lista del modelo: verificarlo en la página de OpenAI
VISIBLE_PARA = ["ventas", "gerencia"]  # las fichas no traen costos: las ven todos


def huella(texto):
    # Si cambia el texto o el modelo, cambia la huella y toca recalcular el vector.
    return hashlib.sha256(f"{MODELO}\n{texto}".encode("utf-8")).hexdigest()


def como_vector(numeros):
    return "[" + ",".join(str(n) for n in numeros) + "]"


fragmentos = []
for ruta in sorted((RAIZ / "data" / "fichas").glob("*.pdf")):
    for f in partir_ficha(leer_texto(ruta)):
        fragmentos.append((f"fichas/{ruta.name}", f))

with psycopg.connect(os.environ["DATABASE_URL"]) as con:
    guardadas = {
        (doc, sec): h
        for doc, sec, h in con.execute("SELECT documento, seccion, huella FROM fragmentos")
    }
    pendientes = [
        (doc, f) for doc, f in fragmentos
        if guardadas.get((doc, f.seccion)) != huella(f.texto_para_buscar)
    ]

    tokens = 0
    if pendientes:
        respuesta = OpenAI().embeddings.create(
            model=MODELO, input=[f.texto_para_buscar for _, f in pendientes]
        )
        tokens = respuesta.usage.total_tokens
        datos = sorted(respuesta.data, key=lambda d: d.index)
        for (doc, f), dato in zip(pendientes, datos):
            con.execute(
                """
                INSERT INTO fragmentos (documento, referencia, seccion, texto, texto_para_buscar,
                                        visible_para, huella, modelo_embedding, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
                ON CONFLICT (documento, seccion) DO UPDATE SET
                    referencia = EXCLUDED.referencia,
                    texto = EXCLUDED.texto,
                    texto_para_buscar = EXCLUDED.texto_para_buscar,
                    visible_para = EXCLUDED.visible_para,
                    huella = EXCLUDED.huella,
                    modelo_embedding = EXCLUDED.modelo_embedding,
                    embedding = EXCLUDED.embedding,
                    actualizado_en = now()
                """,
                (doc, f.referencia, f.seccion, f.texto, f.texto_para_buscar,
                 VISIBLE_PARA, huella(f.texto_para_buscar), MODELO, como_vector(dato.embedding)),
            )

    # Pedazos de fichas que ya no existen: si se quedan, el RAG citaría documentos borrados.
    vigentes = {(doc, f.seccion) for doc, f in fragmentos}
    sobrantes = [c for c in guardadas if c[0].startswith("fichas/") and c not in vigentes]
    for doc, sec in sobrantes:
        con.execute("DELETE FROM fragmentos WHERE documento = %s AND seccion = %s", (doc, sec))

print(f"Pedazos leídos:        {len(fragmentos)}")
print(f"Nuevos o cambiados:    {len(pendientes)}")
print(f"Sin cambios:           {len(fragmentos) - len(pendientes)}")
print(f"Borrados (sobrantes):  {len(sobrantes)}")
print(f"Tokens:                {tokens}")
print(f"Costo:                 USD {tokens * PRECIO_USD_POR_MILLON / 1_000_000:.6f}")