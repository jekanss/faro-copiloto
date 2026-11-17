"""API de Faro Copiloto: la ventanilla por donde otros sistemas le hablan al programa."""

from decimal import Decimal
from typing import Literal

import psycopg
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from openai import APIError
from pydantic import BaseModel, ValidationError
from starlette.concurrency import run_in_threadpool

from faro import db, extraccion
from faro.modelos import Factura

app = FastAPI(
    title="Faro Copiloto",
    version="0.1.0",
    description="Servicios de IA para Faro: lectura de facturas, consulta de fichas y cotizaciones.",
)

TAMANO_MAXIMO = 10 * 1024 * 1024  # 10 MB


class EstadoSalud(BaseModel):
    """Forma de la respuesta de /salud."""

    estado: str
    version: str


class FacturaProcesada(BaseModel):
    """Lo que responde la API después de leer y guardar un PDF.

    procesada: se extrajo y las cuentas cierran.
    para_revision: Diana tiene que mirarla; motivo dice por qué.
    """

    id: int
    archivo: str
    tamano_bytes: int
    estado: Literal["procesada", "para_revision"]
    motivo: str | None = None
    factura: Factura | None = None
    costo_usd: Decimal | None = None


@app.get("/salud", response_model=EstadoSalud, tags=["operación"])
def salud() -> EstadoSalud:
    """Responde si la API está viva. La usa el monitoreo para saber si hay que reiniciarla."""
    return EstadoSalud(estado="ok", version=app.version)


@app.post(
    "/facturas",
    response_model=FacturaProcesada,
    status_code=status.HTTP_201_CREATED,
    tags=["facturas"],
)
async def recibir_factura(pdf: UploadFile = File(...)) -> FacturaProcesada:
    """Recibe el PDF, lo lee con IA, lo verifica con reglas y lo guarda con su costo.

    La IA propone, las reglas verifican: lo que no cuadra va a revisión, no a contabilidad.
    """
    contenido = await pdf.read()

    if not contenido:
        raise HTTPException(status_code=400, detail="El archivo llegó vacío.")
    if len(contenido) > TAMANO_MAXIMO:
        raise HTTPException(status_code=413, detail="El archivo pasa de 10 MB.")
    if not contenido.startswith(b"%PDF"):
        raise HTTPException(status_code=415, detail="El archivo no es un PDF.")

    nombre = pdf.filename or "sin_nombre.pdf"
    factura: Factura | None = None
    uso: dict | None = None

    # 1. Leer. El ayudante espera a OpenAI; la API sigue atendiendo a los demás.
    try:
        factura, uso = await run_in_threadpool(extraccion.extraer_bytes, contenido, nombre)
    except ValidationError:
        estado, motivo = "para_revision", "La lectura no pasó la validación de forma (NIT, fecha o valores)."
    except APIError:
        raise HTTPException(
            status_code=502,
            detail="El servicio de lectura no respondió. Intenta de nuevo en un momento.",
        )
    else:
        # 2. Decidir. Las reglas juzgan lo que la IA propuso.
        if factura.cuadra():
            estado, motivo = "procesada", None
        else:
            estado, motivo = "para_revision", "Las cuentas de la factura no cuadran."

    costo = extraccion.costo_usd(uso) if uso else None

    # 3. Guardar, una sola vez, con el estado ya decidido.
    try:
        factura_id = await run_in_threadpool(
            db.guardar_factura, nombre, estado, motivo, factura, uso, costo
        )
    except psycopg.Error:
        raise HTTPException(
            status_code=503,
            detail="La factura se leyó pero no se pudo guardar. Súbela de nuevo en un momento.",
        )

    return FacturaProcesada(
        id=factura_id,
        archivo=nombre,
        tamano_bytes=len(contenido),
        estado=estado,
        motivo=motivo,
        factura=factura,
        costo_usd=costo,
    )