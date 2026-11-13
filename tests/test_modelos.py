from decimal import Decimal

import pytest
from pydantic import ValidationError

from faro.modelos import Cliente, Cotizacion, Factura, Producto, Proveedor


def producto_valido(**cambios):
    datos = {
        "referencia": "PF-1001",
        "nombre": "Pastilla de freno delantera",
        "marca": "Bosch",
        "categoria": "Frenos",
        "precio_venta": "85000",
        "costo": "52000",
        "stock": 20,
    }
    datos.update(cambios)
    return Producto(**datos)


def factura_valida(**cambios):
    datos = {
        "numero": "FV-2031",
        "proveedor_nit": "900123456-7",
        "fecha": "2026-11-10",
        "items": [
            {"referencia": "PF-1001", "descripcion": "Pastilla de freno", "cantidad": 10,
             "precio_unitario": "52000", "subtotal": "520000"},
            {"referencia": "FA-2002", "descripcion": "Filtro de aceite", "cantidad": 5,
             "precio_unitario": "18000", "subtotal": "90000"},
        ],
        "subtotal": "610000",
        "iva": "115900",
        "total": "725900",
    }
    datos.update(cambios)
    return Factura(**datos)


def test_producto_valido_guarda_el_precio_como_decimal():
    p = producto_valido()
    assert isinstance(p.precio_venta, Decimal)
    assert p.precio_venta == Decimal("85000")


def test_stock_negativo_se_rechaza():
    with pytest.raises(ValidationError):
        producto_valido(stock=-3)


def test_precio_con_texto_se_rechaza():
    with pytest.raises(ValidationError):
        producto_valido(precio_venta="abc")


def test_nit_sin_digito_de_verificacion_se_rechaza():
    with pytest.raises(ValidationError):
        Proveedor(nit="900123456", razon_social="Frenos del Norte SAS")


def test_tipo_de_cliente_fuera_de_la_lista_se_rechaza():
    with pytest.raises(ValidationError):
        Cliente(documento="1020304050", nombre="Taller El Pistón", tipo="mayorista")


def test_factura_correcta_cuadra():
    assert factura_valida().cuadra() is True


def test_factura_con_total_mal_digitado_no_se_rechaza_pero_no_cuadra():
    f = factura_valida(total="752900")
    assert f.cuadra() is False


def test_factura_sin_items_se_rechaza():
    with pytest.raises(ValidationError):
        factura_valida(items=[])


def test_cotizacion_calcula_descuento_iva_y_total():
    c = Cotizacion(
        numero="COT-0001",
        cliente_documento="1020304050",
        vendedor="Andrés",
        fecha="2026-11-13",
        items=[{"referencia": "PF-1001", "cantidad": 2,
                "precio_unitario": "85000", "descuento_pct": "10"}],
    )
    assert c.subtotal == Decimal("153000")
    assert c.iva == Decimal("29070")
    assert c.total == Decimal("182070")
    assert c.estado == "borrador"


def test_estado_de_cotizacion_invalido_se_rechaza():
    with pytest.raises(ValidationError):
        Cotizacion(
            numero="COT-0002", cliente_documento="1020304050", vendedor="Andrés",
            fecha="2026-11-13", estado="regalada",
            items=[{"referencia": "PF-1001", "cantidad": 1, "precio_unitario": "85000"}],
        )


def test_por_que_la_plata_va_en_decimal_y_no_en_float():
    assert 0.1 + 0.2 != 0.3
    assert Decimal("0.1") + Decimal("0.2") == Decimal("0.3")