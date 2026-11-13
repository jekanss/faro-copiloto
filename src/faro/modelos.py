"""Modelos de datos de Faro Copiloto.

Cada clase es un molde: describe la forma de un dato del negocio
y Pydantic rechaza en la puerta lo que no cumpla.
"""

from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, Field

# Plata: siempre Decimal, nunca float. No negativa y con máximo 2 decimales.
Dinero = Annotated[Decimal, Field(ge=0, decimal_places=2)]

# NIT colombiano: de 6 a 10 dígitos, guion y dígito de verificación. Ej: 900123456-7
Nit = Annotated[str, Field(pattern=r"^\d{6,10}-\d$")]

IVA = Decimal("0.19")


class Producto(BaseModel):
    referencia: str = Field(min_length=1)
    nombre: str = Field(min_length=1)
    marca: str
    categoria: str
    precio_venta: Dinero
    costo: Dinero
    stock: int = Field(ge=0)
    vehiculos_compatibles: list[str] = []


class Proveedor(BaseModel):
    nit: Nit
    razon_social: str = Field(min_length=1)
    telefono: str | None = None
    correo: str | None = None


class Cliente(BaseModel):
    documento: str = Field(min_length=5)
    nombre: str = Field(min_length=1)
    tipo: Literal["taller", "empresa", "persona"]
    telefono: str | None = None
    ciudad: str = "Bogotá"


class ItemFactura(BaseModel):
    referencia: str
    descripcion: str
    cantidad: int = Field(gt=0)
    precio_unitario: Dinero
    subtotal: Dinero


class Factura(BaseModel):
    numero: str = Field(min_length=1)
    proveedor_nit: Nit
    fecha: date
    items: list[ItemFactura] = Field(min_length=1)
    subtotal: Dinero
    iva: Dinero
    total: Dinero

    def cuadra(self) -> bool:
        """True si las cuentas de la factura cierran.

        No rechaza la factura: si no cuadra, va a revisión de Diana.
        """
        items_ok = all(i.cantidad * i.precio_unitario == i.subtotal for i in self.items)
        suma_ok = sum((i.subtotal for i in self.items), Decimal("0")) == self.subtotal
        total_ok = self.subtotal + self.iva == self.total
        return items_ok and suma_ok and total_ok


class ItemCotizacion(BaseModel):
    referencia: str
    cantidad: int = Field(gt=0)
    precio_unitario: Dinero
    descuento_pct: Decimal = Field(default=Decimal("0"), ge=0, le=100)

    @property
    def subtotal(self) -> Decimal:
        bruto = self.cantidad * self.precio_unitario
        return (bruto * (1 - self.descuento_pct / 100)).quantize(Decimal("0.01"))


class Cotizacion(BaseModel):
    numero: str
    cliente_documento: str
    vendedor: str
    fecha: date
    items: list[ItemCotizacion] = Field(min_length=1)
    estado: Literal["borrador", "aprobada", "enviada"] = "borrador"

    @property
    def subtotal(self) -> Decimal:
        return sum((i.subtotal for i in self.items), Decimal("0"))

    @property
    def iva(self) -> Decimal:
        return (self.subtotal * IVA).quantize(Decimal("0.01"))

    @property
    def total(self) -> Decimal:
        return self.subtotal + self.iva