-- 004: busqueda por palabras (el segundo bibliotecario).
-- Columna generada: Postgres la calcula sola desde texto_para_buscar
-- y la recalcula si el texto cambia. No hay que volver a ingerir.

ALTER TABLE fragmentos
    ADD COLUMN palabras tsvector
    GENERATED ALWAYS AS (to_tsvector('spanish', texto_para_buscar)) STORED;

CREATE INDEX idx_fragmentos_palabras ON fragmentos USING GIN (palabras);
