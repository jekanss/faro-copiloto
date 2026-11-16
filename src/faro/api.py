from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Faro Copiloto", version="0.1.0")


class Salud(BaseModel):
    estado: str
    servicio: str
    version: str


@app.get("/salud", response_model=Salud)
def salud() -> Salud:
    return Salud(estado="ok", servicio="faro-copiloto", version=app.version)