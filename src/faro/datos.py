"""Carga los datos ficticios de data/ y los pasa por los modelos.

Si un dato no cumple el molde, la carga falla y dice en qué archivo,
en qué registro y cuál es el dato malo. Así la utilería sirve también
como prueba de los modelos.
"""

import json
from pathlib import Path

from pydantic import BaseModel, ValidationError

from faro.modelos import Cliente, Producto, Proveedor

# src/faro/datos.py -> subir dos carpetas -> raíz del repo -> data/
CARPETA_DATOS = Path(__file__).resolve().parents[2] / "data"


def _leer_json(nombre_archivo: str) -> list[dict]:
    ruta = CARPETA_DATOS / nombre_archivo
    return json.loads(ruta.read_text(encoding="utf-8"))


def _validar(nombre_archivo: str, modelo: type[BaseModel], campo_id: str) -> list:
    """Pasa cada fila por el modelo. Si una falla, dice cuál y por qué."""
    resultado = []
    for numero, fila in enumerate(_leer_json(nombre_archivo), start=1):
        try:
            resultado.append(modelo(**fila))
        except ValidationError as error:
            identificador = fila.get(campo_id, "sin identificador")
            raise ValueError(
                f"{nombre_archivo}, registro {numero} ({identificador}) no es válido:\n{error}"
            ) from error
    return resultado


def cargar_productos() -> list[Producto]:
    return _validar("productos.json", Producto, "referencia")


def cargar_proveedores() -> list[Proveedor]:
    return _validar("proveedores.json", Proveedor, "nit")


def cargar_clientes() -> list[Cliente]:
    return _validar("clientes.json", Cliente, "documento")
