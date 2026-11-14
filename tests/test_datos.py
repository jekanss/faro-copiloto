"""Pruebas de los datos ficticios: que pasen por los modelos y que tengan sentido de negocio."""

import pytest
from faro import datos
from faro.datos import cargar_clientes, cargar_productos, cargar_proveedores

# Pruebas de forma: el archivo carga y cada fila pasa por su modelo.

def test_productos_cargan():
    assert len(cargar_productos()) >= 20


def test_proveedores_cargan():
    assert len(cargar_proveedores()) >= 5


def test_clientes_cargan():
    assert len(cargar_clientes()) >= 10


# Pruebas de negocio: cosas que Pydantic no ve pero Faro sí.

def test_referencias_no_se_repiten():
    referencias = [p.referencia for p in cargar_productos()]
    assert len(referencias) == len(set(referencias))


def test_ningun_producto_se_vende_a_perdida():
    for p in cargar_productos():
        assert p.precio_venta > p.costo, f"{p.referencia} se vende por debajo del costo"


def test_nits_de_proveedores_no_se_repiten():
    nits = [p.nit for p in cargar_proveedores()]
    assert len(nits) == len(set(nits))


def test_documentos_de_clientes_no_se_repiten():
    documentos = [c.documento for c in cargar_clientes()]
    assert len(documentos) == len(set(documentos))


# Casos borde: los datos deben traer las situaciones difíciles, no solo las felices.

def test_hay_productos_agotados():
    """El copiloto tendrá que responder 'no hay'. Necesitamos con qué probarlo."""
    assert any(p.stock == 0 for p in cargar_productos())


def test_hay_los_tres_tipos_de_cliente():
    tipos = {c.tipo for c in cargar_clientes()}
    assert tipos == {"taller", "empresa", "persona"}
    

def test_dato_malo_se_rechaza_y_dice_cual_es(monkeypatch):
    """Lo que hicimos a mano con el stock en -5, ahora automático y para siempre."""
    datos_falsos = [
        {"referencia": "FAR-OK-001", "nombre": "Bueno", "marca": "X", "categoria": "X",
         "precio_venta": 100, "costo": 50, "stock": 3},
        {"referencia": "FAR-MAL-002", "nombre": "Malo", "marca": "X", "categoria": "X",
         "precio_venta": 100, "costo": 50, "stock": -5},
    ]
    monkeypatch.setattr(datos, "_leer_json", lambda nombre: datos_falsos)

    with pytest.raises(ValueError, match="registro 2 \\(FAR-MAL-002\\)"):
        cargar_productos()