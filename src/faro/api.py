"""API de Faro Copiloto: la ventanilla por donde otros sistemas le hablan al programa."""

from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from openai import APIError
from pydantic import BaseModel, ValidationError
from starlette.concurrency import run_in_threadpool

from faro import extraccion
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
    """Lo que responde la API después de leer un PDF.

    procesada: se extrajo y las cuentas cierran.
    para_revision: Diana tiene que mirarla; motivo dice por qué.
    """

    archivo: str
    tamano_bytes: int
    estado: Literal["procesada", "para_revision"]
    motivo: str | None = None
    factura: Factura | None = None


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
    """Recibe el PDF de una factura, la lee con IA y la verifica con reglas.

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

    try:
        # El ayudante espera a OpenAI; la API sigue atendiendo a los demás.
        factura, _uso = await run_in_threadpool(extraccion.extraer_bytes, contenido, nombre)
    except ValidationError:
        return FacturaProcesada(
            archivo=nombre,
            tamano_bytes=len(contenido),
            estado="para_revision",
            motivo="La lectura no pasó la validación de forma (NIT, fecha o valores).",
        )
    except APIError:
        raise HTTPException(
            status_code=502,
            detail="El servicio de lectura no respondió. Intenta de nuevo en un momento.",
        )

    if not factura.cuadra():
        return FacturaProcesada(
            archivo=nombre,
            tamano_bytes=len(contenido),
            estado="para_revision",
            motivo="Las cuentas de la factura no cuadran.",
            factura=factura,
        )

    return FacturaProcesada(
        archivo=nombre,
        tamano_bytes=len(contenido),
        estado="procesada",
        factura=factura,
    )