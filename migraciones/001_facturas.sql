-- 001: facturas y sus ítems. Una factura tiene muchos ítems (uno a muchos).

CREATE TABLE facturas (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    archivo             TEXT NOT NULL,
    estado              TEXT NOT NULL CHECK (estado IN ('procesada', 'para_revision')),
    motivo              TEXT,
    numero              TEXT,
    proveedor_nit       TEXT,
    fecha               DATE,
    subtotal            NUMERIC(14, 2),
    iva                 NUMERIC(14, 2),
    total               NUMERIC(14, 2),
    modelo              TEXT,
    esfuerzo            TEXT,
    tokens_entrada      INTEGER,
    tokens_salida       INTEGER,
    tokens_razonamiento INTEGER,
    costo_usd           NUMERIC(12, 8),
    creada_en           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE items_factura (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    factura_id       BIGINT NOT NULL REFERENCES facturas (id) ON DELETE CASCADE,
    renglon          INTEGER NOT NULL,
    referencia       TEXT NOT NULL,
    descripcion      TEXT NOT NULL,
    cantidad         INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario  NUMERIC(14, 2) NOT NULL,
    subtotal         NUMERIC(14, 2) NOT NULL
);

CREATE INDEX idx_items_factura_id ON items_factura (factura_id);
CREATE INDEX idx_facturas_estado ON facturas (estado);