-- 003: fragmentos de documentos (fichas) con su vector, para el RAG.
-- Una fila por pedazo. Lo que se filtra o se cita va en su propia columna.

CREATE TABLE fragmentos (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    documento          TEXT NOT NULL,
    referencia         TEXT NOT NULL,
    seccion            TEXT NOT NULL,
    texto              TEXT NOT NULL,
    texto_para_buscar  TEXT NOT NULL,
    visible_para       TEXT[] NOT NULL CHECK (cardinality(visible_para) > 0),
    huella             TEXT NOT NULL,
    modelo_embedding   TEXT NOT NULL,
    embedding          vector(1536) NOT NULL,
    actualizado_en     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (documento, seccion)
);

CREATE INDEX idx_fragmentos_referencia ON fragmentos (referencia);