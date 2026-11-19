-- 006: ranking BM25 para la busqueda por palabras (lakebase_text de Neon).
-- ts_rank no sabe que tan rara es cada palabra; BM25 si (IDF, saturacion y largo).
-- Usa la columna palabras que ya existe (es_sin_tildes), no hay que tocarla.
-- IF NOT EXISTS: en la base donde ya se probo a mano no hace nada.

CREATE EXTENSION IF NOT EXISTS lakebase_text;

-- El codigo busca este indice por su nombre: no cambiarlo.
CREATE INDEX IF NOT EXISTS fragmentos_palabras_bm25
    ON fragmentos USING lakebase_bm25 (palabras);

-- Las estadisticas de BM25 se actualizan con VACUUM. Con 0, el VACUUM automatico
-- no espera a que la tabla crezca un porcentaje. Aun asi, despues de cargar
-- fichas conviene correr VACUUM fragmentos.
ALTER TABLE fragmentos SET (autovacuum_vacuum_insert_scale_factor = 0);