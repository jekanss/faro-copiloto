"""API de Faro Copiloto: la ventanilla por donde otros sistemas le hablan al programa."""

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="Faro Copiloto",
    version="0.1.0",
    description="Servicios de IA para Faro: lectura de facturas, consulta de fichas y cotizaciones.",
)


class EstadoSalud(BaseModel):
    """Forma de la respuesta de /salud."""

    estado: str
    version: str


@app.get("/salud", response_model=EstadoSalud, tags=["operación"])
def salud() -> EstadoSalud:
    """Responde si la API está viva. La usa el monitoreo para saber si hay que reiniciarla."""
    return EstadoSalud(estado="ok", version=app.version)