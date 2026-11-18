-- 005: busqueda sin tildes. "garantia" y "garantia con tilde" deben dar la misma raiz.
-- Configuracion es_sin_tildes: copia de spanish que primero quita tildes
-- (unaccent) y despues recorta la palabra (spanish_stem).

CREATE EXTENSION IF NOT EXISTS unaccent;

CREATE TEXT SEARCH CONFIGURATION es_sin_tildes (COPY = spanish);

ALTER TEXT SEARCH CONFIGURATION es_sin_tildes
    ALTER MAPPING FOR hword, hword_part, word
    WITH unaccent, spanish_stem;

-- Una columna generada no se edita: se borra (con su indice) y se crea de nuevo.
ALTER TABLE fragmentos DROP COLUMN palabras;

ALTER TABLE fragmentos
    ADD COLUMN palabras tsvector
    GENERATED ALWAYS AS (to_tsvector('es_sin_tildes', texto_para_buscar)) STORED;

CREATE INDEX idx_fragmentos_palabras ON fragmentos USING GIN (palabras);