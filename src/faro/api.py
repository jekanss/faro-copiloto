"""API de Faro Copiloto: la ventanilla por donde otros sistemas le hablan al programa."""

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from pydantic import BaseModel

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


class FacturaRecibida(BaseModel):
    """Lo que responde la API cuando acepta un PDF."""

    archivo: str
    tamano_bytes: int
    estado: str


@app.get("/salud", response_model=EstadoSalud, tags=["operación"])
def salud() -> EstadoSalud:
    """Responde si la API está viva. La usa el monitoreo para saber si hay que reiniciarla."""
    return EstadoSalud(estado="ok", version=app.version)


@app.post(
    "/facturas",
    response_model=FacturaRecibida,
    status_code=status.HTTP_201_CREATED,
    tags=["facturas"],
)
async def recibir_factura(pdf: UploadFile = File(...)) -> FacturaRecibida:
    """Recibe el PDF de una factura y verifica que sea un PDF real antes de aceptarlo."""
    contenido = await pdf.read()

    if not contenido:
        raise HTTPException(status_code=400, detail="El archivo llegó vacío.")
    if len(contenido) > TAMANO_MAXIMO:
        raise HTTPException(status_code=413, detail="El archivo pasa de 10 MB.")
    if not contenido.startswith(b"%PDF"):
        raise HTTPException(status_code=415, detail="El archivo no es un PDF.")

    return FacturaRecibida(
        archivo=pdf.filename or "sin_nombre.pdf",
        tamano_bytes=len(contenido),
        estado="recibida",
    )